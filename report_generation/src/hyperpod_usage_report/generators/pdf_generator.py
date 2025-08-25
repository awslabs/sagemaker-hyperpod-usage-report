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
            ColumnConfig("period_start", 20, lambda x: x.strftime("%H:%M:%S")),
            ColumnConfig("period_end", 20, lambda x: x.strftime("%H:%M:%S")),
            ColumnConfig("namespace", 40),
            ColumnConfig("team", 20),
            ColumnConfig("task_name", 70),
            ColumnConfig("instance", 20),
            ColumnConfig("status", 20),
            *[
                ColumnConfig(f, 21, lambda x: f"{x:.2f}")
                for f in [
                    "utilized_neuron_core_hours",
                    "utilized_neuron_core_count",
                    "utilized_gpu_hours",
                    "utilized_gpu_count",
                    "utilized_vcpu_hours",
                    "utilized_vcpu_count",
                ]
            ],
            ColumnConfig("priority_class", 25),
        ]

        self.detailed_table_headers = [
            "Date",
            "Period Start",
            "Period End",
            "Namespace",
            "Team",
            "Task",
            "Instance",
            "Status",
            "Total\nutilization\n(hours)",
            "Total\nutilization\n(count)",
            "Total\nutilization\n(hours)",
            "Total\nutilization\n(count)",
            "Total\nutilization\n(hours)",
            "Total\nutilization\n(count)",
            "Priority Class",
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
            "Total\nutilization\n(hours)",
            "Allocated\nutilization\n(hours)",
            "Borrowed\nutilization\n(hours)",
            "Total\nutilization\n(hours)",
            "Allocated\nutilization\n(hours)",
            "Borrowed\nutilization\n(hours)",
            "Total\nutilization\n(hours)",
            "Allocated\nutilization\n(hours)",
            "Borrowed\nutilization\n(hours)",
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
        pdf.multi_cell(
            width,
            height / 3 if "\n" in text else height / 2 if "Period" in text else height,
            text,
            0,
            "C",
            True,
        )

        # Return to the right of the cell
        pdf.set_xy(x_start + width, y_start)

        # Draw the border
        pdf.rect(x_start, y_start, width, height)

    def _add_base_header(
        self, pdf: FPDF, header_info: Dict[str, Any]
    ) -> None:
        """Add base report header with title and metadata"""
        # Title
        pdf.set_font(*PDFStyle.TITLE_FONT)
        pdf.cell(0, 10, f"Amazon SageMaker HyperPod", ln=True, align="C")
        pdf.cell(
            0, 10, f"Cluster Name: {header_info['cluster_name']}", ln=True, align="C"
        )
        pdf.ln(5)

        # First separator
        pdf.cell(0, 1, "", "B", ln=True)
        pdf.ln(5)

        # Report metadata
        pdf.set_font(*PDFStyle.HEADER_FONT)
        metadata_lines = [
            f"Report Type: {header_info['report_type'].title()} Utilization Report",
            f"Report Date Generated: {header_info['report_date']}",
            f"Report Date Range (UTC): {header_info['start_date']} to {header_info['end_date']}",
        ]
        
        for line in metadata_lines:
            pdf.cell(0, 10, line, ln=True, align="L")

    def _add_missing_periods(
        self, pdf: FPDF, missing_periods: list
    ) -> None:
        """Add missing periods information as comma-separated with smart wrapping"""
        if missing_periods != []:
            pdf.set_font(*PDFStyle.HEADER_FONT)
            
            # Build periods list
            periods_list = []
            for period in missing_periods:
                periods_list.append(f"{period['start_time']} to {period['end_time']}")
            
            # Smart wrapping logic
            header_text = "Missing Data Periods: "
            max_line_length = 200  # Character limit per line for PDF
            
            # Start with header
            current_line = header_text
            lines = []
            
            for i, period in enumerate(periods_list):
                # Add comma and space if not the first period
                prefix = ", " if i > 0 else ""
                period_text = prefix + period
                
                # Check if adding this period would exceed line limit
                if len(current_line + period_text) > max_line_length:
                    # Current line is full, start a new line
                    lines.append(current_line)
                    current_line = "    " + period  # Indent continuation lines
                else:
                    # Add to current line
                    current_line += period_text
            
            # Add the last line
            if current_line:
                lines.append(current_line)
            
            # Write all lines to PDF
            for line in lines:
                pdf.cell(0, 10, line, ln=True, align="L")

    def _add_filter_info(
        self, pdf: FPDF, header_info: Dict[str, Any], namespace: str = None
    ) -> None:
        """Add filter information (namespace and task)"""
        filter_lines = []
        
        if namespace:
            filter_lines.append(f"Namespace: {namespace}")
        elif header_info.get('namespace'):
            filter_lines.append(f"Namespace: {header_info['namespace']}")
        
        if header_info.get('task'):
            filter_lines.append(f"Task: {header_info['task']}")
        
        if filter_lines:
            pdf.set_font(*PDFStyle.HEADER_FONT)
            for line in filter_lines:
                pdf.cell(0, 10, line, ln=True, align="L")

    def _add_report_header(
        self, pdf: FPDF, header_info: Dict[str, Any], missing_periods: list, namespace: str = None
    ) -> None:
        """Add complete report header with proper ordering"""
        # Add base header
        self._add_base_header(pdf, header_info)
        
        # Add filter information
        self._add_filter_info(pdf, header_info, namespace)
        
        # Add missing periods (moved to after filters)
        self._add_missing_periods(pdf, missing_periods)
        
        # Second separator
        pdf.cell(0, 1, "", "B", ln=True)
        pdf.ln(5)

    def _add_table_headers(
        self,
        pdf: FPDF,
        columns: List[ColumnConfig],
        headers: List[str],
        is_detailed: bool,
    ) -> None:
        """Add table headers with correct group formatting"""
        pdf.set_fill_color(*PDFStyle.HEADER_BG_COLOR)
        pdf.set_text_color(*PDFStyle.HEADER_TEXT_COLOR)
        pdf.set_draw_color(255, 255, 255)

        # First row: Resource type headers with group labels
        if is_detailed:
            base_width = sum(col.width for col in columns[:8])
            metric_width = columns[8].width * 2
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

    def _add_table_content(
        self, pdf: FPDF, df: pd.DataFrame, columns: List[ColumnConfig]
    ) -> None:
        """Add table content rows"""
        pdf.set_font(*PDFStyle.CONTENT_FONT)
        for _, row in df.iterrows():
            for col in columns:
                value = row[col.name]
                formatted_value = col.formatter(value)
                pdf.cell(col.width, 10, formatted_value, 1)
            pdf.ln()

    def _generate_report(
        self,
        df: pd.DataFrame,
        header_info: Dict[str, Any],
        columns: List[ColumnConfig],
        headers: List[str],
        is_detailed: bool,
        missing_periods: list,
    ) -> str:
        """Generate a PDF report with the specified format"""
        output_file = self._build_filename(header_info, self.PDF_EXTENSION)
        pdf = self._create_pdf()
        
        # Check if there's data to display
        if df.empty:
            self._add_report_header(pdf, header_info, missing_periods)
            self._add_table_headers(pdf, columns, headers, is_detailed)
            pdf.set_font(*PDFStyle.HEADER_FONT)
            pdf.cell(0, 20, "No Results", ln=True, align="C")
        else:
            if 'namespace' in df.columns:
                # Group by namespace and create separate pages
                namespaces = df['namespace'].unique()
                for i, namespace in enumerate(namespaces):
                    if i > 0:
                        pdf.add_page()
                    
                    namespace_data = df[df['namespace'] == namespace]
                    
                    if header_info.get('namespace'):
                        if i == 0:
                            self._add_report_header(pdf, header_info, missing_periods)
                    else:
                        self._add_report_header(pdf, header_info, missing_periods, namespace)
                    
                    self._add_table_headers(pdf, columns, headers, is_detailed)
                    self._add_table_content(pdf, namespace_data, columns)
            else:
                self._add_report_header(pdf, header_info, missing_periods)
                self._add_table_headers(pdf, columns, headers, is_detailed)
                self._add_table_content(pdf, df, columns)
        
        pdf.output(output_file)
        return output_file

    def generate_detailed_report(
        self, df: pd.DataFrame, header_info: Dict[str, Any], missing_periods: list
    ) -> str:
        """Generate a detailed PDF report"""
        return self._generate_report(
            df,
            header_info,
            self.detailed_columns,
            self.detailed_table_headers,
            True,
            missing_periods,
        )

    def generate_summary_report(
        self, df: pd.DataFrame, header_info: Dict[str, Any], missing_periods: list
    ) -> str:
        """Generate a summary PDF report"""
        return self._generate_report(
            df,
            header_info,
            self.summary_columns,
            self.summary_table_headers,
            False,
            missing_periods,
        )
