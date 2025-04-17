from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import pandas as pd
from fpdf import FPDF

from .base import BaseReportGenerator


@dataclass
class ColumnConfig:
    name: str
    width: int
    formatter: Callable = str


class PDFStyle:
    TITLE_FONT = ("Arial", "B", 16)
    HEADER_FONT = ("Arial", "B", 10)
    CONTENT_FONT = ("Arial", "", 8)
    HEADER_BG_COLOR = (0, 0, 0)
    HEADER_TEXT_COLOR = (255, 255, 255)
    SUBHEADER_BG_COLOR = (200, 200, 200)


class PDFReportGenerator(BaseReportGenerator):
    def __init__(self):
        self._setup_column_configs()

    def _setup_column_configs(self):
        """Initialize column configurations and table headers for both report types"""
        self.detailed_columns = [
            ColumnConfig("report_date", 20, lambda x: x.strftime("%Y-%m-%d")),
            ColumnConfig("namespace", 50),
            ColumnConfig("team", 30),
            ColumnConfig("task_name", 70),
            ColumnConfig("instance", 20),
            ColumnConfig("status", 20),
            *[
                ColumnConfig(f, 22, lambda x: f"{x:.2f}")
                for f in [
                    "utilized_neuron_core_hours",
                    "utilized_neuron_core_count",
                    "utilized_gpu_hours",
                    "utilized_gpu_count",
                    "utilized_vcpu_hours",
                    "utilized_vcpu_count",
                ]
            ],
            ColumnConfig("priority_class", 30),
        ]

        self.detailed_table_headers = [
            "Date",
            "Namespace",
            "Team",
            "Task",
            "Instance",
            "Status",
            "Total\nutilization\n(hour)",
            "Total\nutilization\n(count)",
            "Total\nutilization\n(hour)",
            "Total\nutilization\n(count)",
            "Total\nutilization\n(hour)",
            "Total\nutilization\n(count)",
            "Priority class",
        ]

        self.summary_columns = [
            ColumnConfig("report_date", 20, lambda x: x.strftime("%Y-%m-%d")),
            ColumnConfig("namespace", 50),
            ColumnConfig("team", 50),
            ColumnConfig("instance_type", 30),
            *[
                ColumnConfig(f, 25, lambda x: f"{x:.2f}")
                for f in [
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
            ],
        ]

        self.summary_table_headers = [
            "Date",
            "Namespace",
            "Team",
            "Type",
            "Total\nutilization\n(hour)",
            "Allocated\nutilization\n(hour)",
            "Borrowed\nutilization\n(hour)",
            "Total\nutilization\n(hour)",
            "Allocated\nutilization\n(hour)",
            "Borrowed\nutilization\n(hour)",
            "Total\nutilization\n(hour)",
            "Allocated\nutilization\n(hour)",
            "Borrowed\nutilization\n(hour)",
        ]

    def _create_pdf(self) -> FPDF:
        """Initialize PDF object with standard settings"""
        pdf = FPDF(orientation="L", format="A3")
        pdf.add_page()
        return pdf

    def header_cell(self, pdf, width, height, text, border=1):
        # Save current position
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        # Print the cell content
        pdf.multi_cell(width, height / 3 if "\n" in text else height, text, 0, "C", True)

        # Return to the right of the cell
        pdf.set_xy(x_start + width, y_start)

        # Draw the border
        pdf.rect(x_start, y_start, width, height)

    def _add_report_header(self, pdf: FPDF, header_info: Dict[str, Any]) -> None:
        """Add report header with title and metadata"""
        # Title
        pdf.set_font(*PDFStyle.TITLE_FONT)
        pdf.cell(0, 10, f"ClusterName: {header_info['cluster_name']}", ln=True, align="C")
        pdf.ln(5)

        # First separator
        pdf.cell(0, 1, "", "B", ln=True)
        pdf.ln(5)

        # Report metadata
        pdf.set_font(*PDFStyle.HEADER_FONT)
        metadata_lines = [
            f"Type: {header_info['report_type'].title()} Utilization Report",
            f"Date Generated: {header_info['report_date']}",
            f"Date Range: {header_info['start_date']} to {header_info['end_date']}",
        ]
        for line in metadata_lines:
            pdf.cell(0, 10, line, ln=True, align="C")
        pdf.ln(5)

        # Second separator
        pdf.cell(0, 1, "", "B", ln=True)
        pdf.ln(5)

    def _add_table_headers(
        self, pdf: FPDF, columns: List[ColumnConfig], headers: List[str], is_detailed: bool
    ) -> None:
        """Add table headers with correct group formatting"""
        pdf.set_fill_color(*PDFStyle.HEADER_BG_COLOR)
        pdf.set_text_color(*PDFStyle.HEADER_TEXT_COLOR)
        pdf.set_draw_color(255, 255, 255)

        # First row: Resource type headers with group labels
        if is_detailed:
            base_width = sum(col.width for col in columns[:6])
            metric_width = columns[6].width * 2
            pdf.cell(base_width, 10, "", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "NeuronCore", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "GPU", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "vCPU", 1, 0, "C", True)
            pdf.cell(columns[-1].width, 10, "", 1, 1, "C", True)
        else:
            base_width = sum(col.width for col in columns[:3])
            type_width = columns[3].width
            metric_width = columns[4].width * 3
            pdf.cell(base_width, 10, "", 1, 0, "C", True)
            pdf.cell(type_width, 10, "Instance", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "NeuronCore", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "GPU", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "vCPU", 1, 1, "C", True)

        # Second row: Column headers
        pdf.set_draw_color(0, 0, 0)
        pdf.set_fill_color(*PDFStyle.SUBHEADER_BG_COLOR)
        pdf.set_text_color(0, 0, 0)

        for header, col in zip(headers, columns):
            self.header_cell(pdf, col.width, 15, header)
        pdf.ln(15)

    def _add_table_content(self, pdf: FPDF, df: pd.DataFrame, columns: List[ColumnConfig]) -> None:
        """Add table content rows"""
        pdf.set_font(*PDFStyle.CONTENT_FONT)
        for _, row in df.iterrows():
            for col in columns:
                value = row[col.name]
                formatted_value = col.formatter(value)
                pdf.cell(col.width, 10, formatted_value, 1)
            pdf.ln()

    def _get_output_filename(self, header_info: Dict[str, Any]) -> str:
        """Generate output filename based on report parameters"""
        base_name = f"{header_info['report_type']}-report-{header_info['start_date']}"
        return (
            f"{base_name}-{header_info['end_date']}.pdf"
            if int(header_info["days"]) > 1
            else f"{base_name}.pdf"
        )

    def _generate_report(
        self,
        df: pd.DataFrame,
        header_info: Dict[str, Any],
        columns: List[ColumnConfig],
        headers: List[str],
        is_detailed: bool,
    ) -> str:
        """Generate a PDF report with the specified format"""
        output_file = self._get_output_filename(header_info)
        pdf = self._create_pdf()
        self._add_report_header(pdf, header_info)
        self._add_table_headers(pdf, columns, headers, is_detailed)
        self._add_table_content(pdf, df, columns)
        pdf.output(output_file)
        return output_file

    def generate_detailed_report(self, df: pd.DataFrame, header_info: Dict[str, Any]) -> str:
        """Generate a detailed PDF report"""
        return self._generate_report(
            df, header_info, self.detailed_columns, self.detailed_table_headers, True
        )

    def generate_summary_report(self, df: pd.DataFrame, header_info: Dict[str, Any]) -> str:
        """Generate a summary PDF report"""
        return self._generate_report(
            df, header_info, self.summary_columns, self.summary_table_headers, False
        )
