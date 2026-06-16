import pandas as pd

from .base import BaseReportGenerator
from ..utils.util import has_mig_usage


class CSVReportGenerator(BaseReportGenerator):

    def generate_report_header(self, header_info: dict) -> list:
        """Generate standard report header"""
        time_period = f"{header_info['start_date']} to {header_info['end_date']}"

        return [
            "Amazon SageMaker HyperPod",
            f"Cluster Name: {header_info['cluster_name']}",
            f"Report Type: {header_info['report_type'].title()} Utilization Report",
            f"Report Date Generated: {header_info['report_date']}",
            f"Report Date Range (UTC): {time_period}",
        ]
        
    def generate_filter_lines(self, header_info: dict) -> list:
        """Generate filter information lines"""
        filter_fields = {
            "namespace": "Namespace",
            "task": "Task"
        }
        
        filter_lines = [
            f"{display_name}: {header_info[field]}"
            for field, display_name in filter_fields.items()
            if header_info.get(field)
        ]
        
        return filter_lines

    def generate_summary_report(
        self, df: pd.DataFrame, header_info: dict, missing_periods: list
    ) -> str:
        """Generate CSV Summary report"""
        output_file = self._build_filename(header_info, self.CSV_EXTENSION)
        
        has_mig = has_mig_usage(df, False)

        # Column headers (multi-level)
        if has_mig:
            resource_headers = [
                ",,,Instance,NeuronCore,,,GPU,,,vCPU,,,MIG Profile,MIG,,",
                "Date,Namespace,Team,Type,Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours),"
                + "Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours),"
                + "Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours),"
                + "Profile,Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours)",
            ]
        else:
            resource_headers = [
                ",,,Instance,NeuronCore,,,GPU,,,vCPU,,",
                "Date,Namespace,Team,Type,Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours),"
                + "Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours),"
                + "Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours)",
            ]

        # Reorder DataFrame columns to match desired output
        if has_mig:
            df = df[
                [
                    "report_date",
                    "namespace",
                    "team",
                    "instance_type",
                    "total_neuron_core_utilization_hours",
                    "allocated_neuron_core_utilization_hours",
                    "borrowed_neuron_core_utilization_hours",
                    "total_gpu_utilization_hours",
                    "allocated_gpu_utilization_hours",
                    "borrowed_gpu_utilization_hours",
                    "total_vcpu_utilization_hours",
                    "allocated_vcpu_utilization_hours",
                    "borrowed_vcpu_utilization_hours",
                    "mig_profile",
                    "total_mig_utilization_hours",
                    "allocated_mig_utilization_hours",
                    "borrowed_mig_utilization_hours",
                ]
            ]
        else:
            df = df[
                [
                    "report_date",
                    "namespace",
                    "team",
                    "instance_type",
                    "total_neuron_core_utilization_hours",
                    "allocated_neuron_core_utilization_hours",
                    "borrowed_neuron_core_utilization_hours",
                    "total_gpu_utilization_hours",
                    "allocated_gpu_utilization_hours",
                    "borrowed_gpu_utilization_hours",
                    "total_vcpu_utilization_hours",
                    "allocated_vcpu_utilization_hours",
                    "borrowed_vcpu_utilization_hours",
                ]
            ]

        # Write to file
        with open(output_file, "w") as f:
            # Write base header
            for row in self.generate_report_header(header_info):
                f.write(f"{row}\n")

            # Write filter lines
            for row in self.generate_filter_lines(header_info):
                f.write(f"{row}\n")

            # Write missing periods (moved to after filters)
            if missing_periods != []:
                f.write(f"Missing data periods\n")
                for period in missing_periods:
                    f.write(f"{period['start_time']} to {period['end_time']}\n")

            # Write column headers
            for header_row in resource_headers:
                f.write(f"{header_row}\n")

            if df.empty:
                f.write("No Results\n")
            else:
                # Write data
                for _, row in df.iterrows():
                    formatted_row = [
                        row["report_date"].strftime("%Y-%m-%d"),
                        row["namespace"],
                        row["team"],
                        row["instance_type"],
                        f"{row['total_neuron_core_utilization_hours']:.2f}",
                        f"{row['allocated_neuron_core_utilization_hours']:.2f}",
                        f"{row['borrowed_neuron_core_utilization_hours']:.2f}",
                        f"{row['total_gpu_utilization_hours']:.2f}",
                        f"{row['allocated_gpu_utilization_hours']:.2f}",
                        f"{row['borrowed_gpu_utilization_hours']:.2f}",
                        f"{row['total_vcpu_utilization_hours']:.2f}",
                        f"{row['allocated_vcpu_utilization_hours']:.2f}",
                        f"{row['borrowed_vcpu_utilization_hours']:.2f}",
                    ]
                    if has_mig:
                        formatted_row.extend([
                            str(row["mig_profile"]) if pd.notna(row["mig_profile"]) else "",
                            f"{row['total_mig_utilization_hours']:.2f}" if pd.notna(row['total_mig_utilization_hours']) else "0.00",
                            f"{row['allocated_mig_utilization_hours']:.2f}" if pd.notna(row['allocated_mig_utilization_hours']) else "0.00",
                            f"{row['borrowed_mig_utilization_hours']:.2f}" if pd.notna(row['borrowed_mig_utilization_hours']) else "0.00",
                        ])
                    f.write(",".join(formatted_row) + "\n")

        return output_file

    def generate_detailed_report(
        self, df: pd.DataFrame, header_info: dict, missing_periods: list
    ) -> str:
        """Generate CSV Detailed report"""
        output_file = self._build_filename(header_info, self.CSV_EXTENSION)
        
        has_mig = has_mig_usage(df, True)

        # Column headers (multi-level)
        if has_mig:
            resource_headers = [
                ",,,,,,NeuronCore,,GPU,,vCPU,,,MIG Profile,MIG,,",
                "Date,Period Start,Period End,Namespace,Team,Task,Instance,Status,Total utilization (hours),"
                + "Total utilization (count),Total utilization (hours),Total utilization (count),"
                + "Total utilization (hours),Total utilization (count),Profile,Total utilization (hours),Total utilization (count),Priority class",
            ]
        else:
            resource_headers = [
                ",,,,,,NeuronCore,,GPU,,vCPU,,",
                "Date,Period Start,Period End,Namespace,Team,Task,Instance,Status,Total utilization (hours),"
                + "Total utilization (count),Total utilization (hours),Total utilization (count),"
                + "Total utilization (hours),Total utilization (count),Priority class",
            ]

        # Reorder DataFrame columns to match desired output
        if has_mig:
            df = df[
                [
                    "report_date",
                    "period_start",
                    "period_end",
                    "namespace",
                    "team",
                    "task_name",
                    "instance",
                    "status",
                    "utilized_neuron_core_hours",
                    "utilized_neuron_core_count",
                    "utilized_gpu_hours",
                    "utilized_gpu_count",
                    "utilized_vcpu_hours",
                    "utilized_vcpu_count",
                    "mig_profile",
                    "utilized_mig_hours",
                    "utilized_mig_count",
                    "priority_class",
                ]
            ]
        else:
            df = df[
                [
                    "report_date",
                    "period_start",
                    "period_end",
                    "namespace",
                    "team",
                    "task_name",
                    "instance",
                    "status",
                    "utilized_neuron_core_hours",
                    "utilized_neuron_core_count",
                    "utilized_gpu_hours",
                    "utilized_gpu_count",
                    "utilized_vcpu_hours",
                    "utilized_vcpu_count",
                    "priority_class",
                ]
            ]

        # Write to file
        with open(output_file, "w") as f:
            # Write base header
            for row in self.generate_report_header(header_info):
                f.write(f"{row}\n")

            # Write filter lines
            for row in self.generate_filter_lines(header_info):
                f.write(f"{row}\n")

            # Write missing periods
            if missing_periods != []:
                f.write(f"Missing Data Periods\n")
                for period in missing_periods:
                    f.write(f"{period['start_time']} to {period['end_time']}\n")

            # Write column headers
            for header_row in resource_headers:
                f.write(f"{header_row}\n")

            if df.empty:
                f.write("No Results\n")
            else:
                # Write data
                for _, row in df.iterrows():
                    formatted_row = [
                        row["report_date"].strftime("%Y-%m-%d"),
                        row["period_start"].strftime("%H:%M:%S"),
                        row["period_end"].strftime("%H:%M:%S"),
                        row["namespace"],
                        row["team"],
                        row["task_name"],
                        row["instance"],
                        row["status"],
                        f"{row['utilized_neuron_core_hours']:.2f}",
                        f"{row['utilized_neuron_core_count']:.2f}",
                        f"{row['utilized_gpu_hours']:.2f}",
                        f"{row['utilized_gpu_count']:.2f}",
                        f"{row['utilized_vcpu_hours']:.2f}",
                        f"{row['utilized_vcpu_count']:.2f}",
                    ]
                    if has_mig:
                        formatted_row.extend([
                            str(row["mig_profile"]) if pd.notna(row["mig_profile"]) else "",
                            f"{row['utilized_mig_hours']:.2f}" if pd.notna(row['utilized_mig_hours']) else "0.00",
                            f"{row['utilized_mig_count']:.2f}" if pd.notna(row['utilized_mig_count']) else "0.00",
                        ])
                    formatted_row.append(row["priority_class"])
                    f.write(",".join(formatted_row) + "\n")

        return output_file
