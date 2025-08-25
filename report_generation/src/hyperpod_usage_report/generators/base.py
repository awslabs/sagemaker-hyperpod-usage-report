from abc import ABC, abstractmethod

import pandas as pd


class BaseReportGenerator(ABC):
    """Base class for report generators"""
    
    # File extensions
    CSV_EXTENSION = "csv"
    PDF_EXTENSION = "pdf"

    @abstractmethod
    def generate_summary_report(
        self, df: pd.DataFrame, header_info: dict, missing_periods: list
    ) -> str:
        """Generate summary report in specific format"""
        pass

    @abstractmethod
    def generate_detailed_report(
        self, df: pd.DataFrame, header_info: dict, missing_periods: list
    ) -> str:
        """Generate detailed report in specific format"""
        pass

    def _build_filename(self, header_info: dict, extension: str) -> str:
        """Build filename with optional namespace and task suffixes"""
        namespace_suffix = f"-{header_info['namespace']}" if header_info.get('namespace') else ""
        task_suffix = f"-{header_info['task']}" if header_info.get('task') else ""
        base_name = f"{header_info['report_type']}-report-{header_info['start_date']}"
        return (
            f"{base_name}-{header_info['end_date']}{namespace_suffix}{task_suffix}.{extension}"
            if int(header_info["days"]) > 1
            else f"{base_name}{namespace_suffix}{task_suffix}.{extension}"
        )
