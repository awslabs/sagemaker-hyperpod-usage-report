import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict

import awswrangler as wr
import pandas as pd

from .generators.csv_generator import CSVReportGenerator
from .generators.pdf_generator import PDFReportGenerator
from .utils.query_builder import QueryBuilder
from .utils.s3_uploader import S3Uploader


class ReportType(Enum):
    SUMMARY = "summary"
    DETAILED = "detailed"


class DataFetchError(Exception):
    pass


class ReportGenerationError(Exception):
    pass


class S3UploadError(Exception):
    pass


class ReportGenerator:
    def __init__(
        self,
        start_date: str,
        end_date: str,
        cluster_name: str,
        database_name: str,
        report_type: str,
        output_location: str,
        database_workgroup_name: str,
        format: str,
    ):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.database_name = database_name
        self.report_type = report_type
        self.output_location = output_location
        self.format = format
        self.cluster_name = cluster_name
        self.database_workgroup_name = database_workgroup_name
        
        self.generator = (
            CSVReportGenerator() if format.lower() == "csv" else PDFReportGenerator()
        )

    def _fetch_data(self):
        """Fetches required data for report generation"""
        try:
            query = QueryBuilder.build_fetch_report_data_query(
                self.report_type,
                self.start_date.strftime("%Y-%m-%d"),
                self.end_date.strftime("%Y-%m-%d"),
            )
            return wr.athena.read_sql_query(sql=query, database=self.database_name, workgroup=self.database_workgroup_name)
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            raise

    def _prepare_header_info(self) -> Dict[str, str]:
        """Prepares header information for the report"""
        return {
            "cluster_name": self.cluster_name,
            "report_date": self.end_date.strftime("%Y-%m-%d"),
            "report_type": self.report_type,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "days": str((self.end_date - self.start_date).days + 1),
        }

    def _generate_report_by_type(
        self,
        df: Any,
        header_info: Dict[str, str],
        report_type: ReportType,
        missing_periods: list,
    ) -> str:
        """Generates the appropriate type of report"""
        try:
            if report_type == ReportType.SUMMARY:
                return self.generator.generate_summary_report(
                    df, header_info, missing_periods
                )
            elif report_type == ReportType.DETAILED:
                return self.generator.generate_detailed_report(
                    df, header_info, missing_periods
                )
        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate {report_type.value} report: {str(e)}"
            )

    def _upload_and_cleanup(self, output_file: str) -> None:
        """Uploads the generated report to S3"""
        try:
            S3Uploader.upload_file(output_file, self.output_location)
            print(f"Successfully uploaded report to {self.output_location}")
        except Exception as e:
            raise S3UploadError(f"Failed to upload report: {str(e)}")

    def _find_missing_period(self) -> list:
        """Find missing periods from cluster usage collector"""
        all_hours = list(range(24))
        results = []
        try:
            query = QueryBuilder.build_fetch_heartdub_query(
                self.start_date.strftime("%Y-%m-%d"),
                self.end_date.strftime("%Y-%m-%d"),
            )
            df = wr.athena.read_sql_query(sql=query, database=self.database_name)
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            raise
        if df.empty:
            start_time = datetime.combine(self.start_date.date(), datetime.min.time())
            end_time = datetime.combine(
                (self.end_date + timedelta(days=1)).date(), datetime.min.time()
            )
            return [
                {
                    "start_time": start_time,
                    "end_time": end_time,
                }
            ]
        df["hour"] = df["hour"].astype(int)
        df["date"] = pd.to_datetime(
            df[["year", "month", "day"]].astype(str).agg("-".join, axis=1)
        )

        for (_, day), group in df.groupby(["cluster", "date"]):
            existing_hours = sorted(group["hour"].unique())
            missing_hours = sorted(set(all_hours) - set(existing_hours))

            if missing_hours:
                current_start = missing_hours[0]
                prev = current_start

                for h in missing_hours[1:] + [None]:
                    if h is None or h != prev + 1:
                        start_time = datetime.combine(
                            day.date(), datetime.min.time()
                        ) + timedelta(hours=current_start)
                        end_time = datetime.combine(
                            day.date(), datetime.min.time()
                        ) + timedelta(hours=prev + 1)
                        results.append(
                            {
                                "start_time": start_time,
                                "end_time": end_time,
                            }
                        )
                        if h is not None:
                            current_start = h
                    prev = h
        return results

    def generate_report(self):
        output_file = None
        try:
            # Validate report type
            report_type = ReportType(self.report_type)

            # Fetch and prepare data
            df = self._fetch_data()
            header_info = self._prepare_header_info()

            # Fetch missing date period
            missing_periods = self._find_missing_period()

            # Generate appropriate report
            output_file = self._generate_report_by_type(
                df, header_info, report_type, missing_periods
            )

            # Upload and cleanup
            self._upload_and_cleanup(output_file)

            print(f"Successfully generated and uploaded {report_type.value} report")

        except ValueError:
            print(f"Invalid report type: {self.report_type}")
            raise
        except Exception as e:
            print(f"Report generation failed: {str(e)}")
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")
        finally:
            if output_file and os.path.exists(output_file):
                os.remove(output_file)
                print(f"Cleaned up temporary file: {output_file}")
