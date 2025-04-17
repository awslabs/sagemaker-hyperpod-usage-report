from abc import ABC, abstractmethod

import pandas as pd


class BaseReportGenerator(ABC):
    """Base class for report generators"""

    @abstractmethod
    def generate_summary_report(self, df: pd.DataFrame, header_info: dict) -> str:
        """Generate summary report in specific format"""
        pass

    @abstractmethod
    def generate_detailed_report(self, df: pd.DataFrame, header_info: dict) -> str:
        """Generate detailed report in specific format"""
        pass
