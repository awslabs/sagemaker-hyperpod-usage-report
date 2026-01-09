from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import pandas as pd
from fpdf import FPDF

from .base import BaseReportGenerator
from ..utils.util import has_mig_usage, filter_zero_usage_rows


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
    

    

    
    def _remove_duplicate_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows from the dataframe"""
        if df.empty:
            return df
        return df.drop_duplicates().reset_index(drop=True)
    


    def _setup_column_configs(self):
        """Initialize column configurations and table headers for both report types"""
        # Detailed report columns without MIG
        self.detailed_columns = [
            ColumnConfig("report_date", 20, lambda x: x.strftime("%Y-%m-%d")),
            ColumnConfig("period_start", 20, lambda x: x.strftime("%H:%M:%S")),
            ColumnConfig("period_end", 20, lambda x: x.strftime("%H:%M:%S")),
            ColumnConfig("namespace", 32),
            ColumnConfig("team", 14),
            ColumnConfig("task_name", 65),
            ColumnConfig("instance", 25),
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
            ColumnConfig("priority_class", 26),
        ]
        
        # Detailed report columns with MIG
        self.detailed_columns_with_mig = [
            ColumnConfig("report_date", 18, lambda x: x.strftime("%Y-%m-%d")),
            ColumnConfig("period_start", 18, lambda x: x.strftime("%H:%M:%S")),
            ColumnConfig("period_end", 18, lambda x: x.strftime("%H:%M:%S")),
            ColumnConfig("namespace", 30),
            ColumnConfig("team", 12),
            ColumnConfig("task_name", 55),
            ColumnConfig("instance", 23),
            ColumnConfig("status", 18),
            *[
                ColumnConfig(f, 19, lambda x: f"{x:.2f}")
                for f in [
                    "utilized_neuron_core_hours",
                    "utilized_neuron_core_count",
                    "utilized_gpu_hours",
                    "utilized_gpu_count",
                    "utilized_vcpu_hours",
                    "utilized_vcpu_count",
                ]
            ],
            ColumnConfig("mig_profile", 18, lambda x: str(x) if pd.notna(x) and x != "" else ""),
            ColumnConfig("utilized_mig_hours", 19, lambda x: f"{x:.2f}" if pd.notna(x) else "0.00"),
            ColumnConfig("utilized_mig_count", 19, lambda x: f"{x:.2f}" if pd.notna(x) else "0.00"),
            ColumnConfig("priority_class", 24),
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
            "Priority\nClass",
        ]
        
        self.detailed_table_headers_with_mig = [
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
            "MIG\nProfile",
            "Total\nutilization\n(hours)",
            "Total\nutilization\n(count)",
            "Priority\nClass",
        ]

        self.summary_columns = [
            ColumnConfig("report_date", 18, lambda x: x.strftime("%Y-%m-%d")),
            ColumnConfig("namespace", 32),
            ColumnConfig("team", 20),
            ColumnConfig("instance_type", 26),
            *[
                ColumnConfig(f, 22, lambda x: f"{x:.2f}")
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
        
        # Summary report columns with MIG
        self.summary_columns_with_mig = [
            ColumnConfig("report_date", 16, lambda x: x.strftime("%Y-%m-%d")),
            ColumnConfig("namespace", 28),
            ColumnConfig("team", 18),
            ColumnConfig("instance_type", 22),
            *[
                ColumnConfig(f, 20, lambda x: f"{x:.2f}")
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
            ColumnConfig("mig_profile", 16, lambda x: str(x) if pd.notna(x) else ""),
            ColumnConfig("total_mig_utilization_hours", 20, lambda x: f"{x:.2f}" if pd.notna(x) else "0.00"),
            ColumnConfig("allocated_mig_utilization_hours", 20, lambda x: f"{x:.2f}" if pd.notna(x) else "0.00"),
            ColumnConfig("borrowed_mig_utilization_hours", 20, lambda x: f"{x:.2f}" if pd.notna(x) else "0.00"),
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
        
        self.summary_table_headers_with_mig = [
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
            "MIG\nProfile",
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

        pdf.rect(x_start, y_start, width, height, 'F')
        if "\n" not in text:
            pdf.cell(width, height, text, 0, 0, "C")
        else:
            pdf.multi_cell(
                width,
                height / 3,
                text,
                0,
                "C",
                False,
            )

        # Return to the right of the cell
        pdf.set_xy(x_start + width, y_start)

        # Draw the border
        pdf.rect(x_start, y_start, width, height, 'D')

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
        has_mig: bool,
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
            if has_mig:
                mig_profile_width = columns[14].width
                mig_metric_width = columns[15].width * 2
                pdf.cell(mig_profile_width, 10, "", 1, 0, "C", True)
                pdf.cell(mig_metric_width, 10, "MIG", 1, 0, "C", True)
            pdf.cell(columns[-1].width, 10, "", 1, 1, "C", True)
        else:
            base_width = sum(col.width for col in columns[:3])
            type_width = columns[3].width
            metric_width = columns[4].width * 3
            pdf.cell(base_width, 10, "", 1, 0, "C", True)
            pdf.cell(type_width, 10, "Instance", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "NeuronCore", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "GPU", 1, 0, "C", True)
            pdf.cell(metric_width, 10, "vCPU", 1, 0, "C", True)
            if has_mig:
                mig_profile_width = columns[13].width
                mig_metric_width = columns[14].width * 3
                pdf.cell(mig_profile_width, 10, "", 1, 0, "C", True)
                pdf.cell(mig_metric_width, 10, "MIG", 1, 1, "C", True)
            else:
                pdf.ln()

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
            x_start = pdf.get_x()
            y_start = pdf.get_y()
            
            for i, col in enumerate(columns):
                value = row[col.name]
                formatted_value = col.formatter(value)
                
                # Set position for this cell
                x_pos = x_start + sum(c.width for c in columns[:i])
                pdf.set_xy(x_pos, y_start)
                
                # Use cell for consistent height and alignment
                pdf.cell(col.width, 10, formatted_value, 1, 0, "L")
            
            # Move to next row
            pdf.ln()

    def _generate_report(
        self,
        df: pd.DataFrame,
        header_info: Dict[str, Any],
        columns: List[ColumnConfig],
        headers: List[str],
        is_detailed: bool,
        missing_periods: list,
        has_mig: bool,
    ) -> str:
        """Generate a PDF report with the specified format"""
        output_file = self._build_filename(header_info, self.PDF_EXTENSION)
        pdf = self._create_pdf()
        
        # Check if there's data to display
        if df.empty:
            self._add_report_header(pdf, header_info, missing_periods)
            self._add_table_headers(pdf, columns, headers, is_detailed, has_mig)
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
                    
                    self._add_table_headers(pdf, columns, headers, is_detailed, has_mig)
                    self._add_table_content(pdf, namespace_data, columns)
            else:
                self._add_report_header(pdf, header_info, missing_periods)
                self._add_table_headers(pdf, columns, headers, is_detailed, has_mig)
                self._add_table_content(pdf, df, columns)
        
        pdf.output(output_file)
        return output_file

    def generate_detailed_report(
        self, df: pd.DataFrame, header_info: Dict[str, Any], missing_periods: list
    ) -> str:
        """Generate a detailed PDF report"""
        df = filter_zero_usage_rows(df, True)
        df = self._remove_duplicate_rows(df)
        has_mig = has_mig_usage(df, True)
        columns = self.detailed_columns_with_mig if has_mig else self.detailed_columns
        headers = self.detailed_table_headers_with_mig if has_mig else self.detailed_table_headers
        
        return self._generate_report(
            df,
            header_info,
            columns,
            headers,
            True,
            missing_periods,
            has_mig,
        )

    def generate_summary_report(
        self, df: pd.DataFrame, header_info: Dict[str, Any], missing_periods: list
    ) -> str:
        """Generate a summary PDF report"""
        df = filter_zero_usage_rows(df, False)
        df = self._remove_duplicate_rows(df)
        has_mig = has_mig_usage(df, False)
        columns = self.summary_columns_with_mig if has_mig else self.summary_columns
        headers = self.summary_table_headers_with_mig if has_mig else self.summary_table_headers
        
        return self._generate_report(
            df,
            header_info,
            columns,
            headers,
            False,
            missing_periods,
            has_mig,
        )
