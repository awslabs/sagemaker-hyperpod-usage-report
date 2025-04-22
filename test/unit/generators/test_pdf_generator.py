import os
from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from hyperpod_usage_report.generators.pdf_generator import (ColumnConfig,
                                                            PDFReportGenerator,
                                                            PDFStyle)


@pytest.fixture
def summary_df():
    return pd.DataFrame(
        {
            "report_date": [datetime.strptime("2025-03-25", "%Y-%m-%d")],
            "namespace": ["test-namespace"],
            "team": ["test-team"],
            "instance_type": ["t2.micro"],
            "total_neuron_core_utilization_hours": [1.0],
            "allocated_neuron_core_utilization_hours": [0.5],
            "borrowed_neuron_core_utilization_hours": [0.5],
            "total_gpu_utilization_hours": [2.0],
            "allocated_gpu_utilization_hours": [1.0],
            "borrowed_gpu_utilization_hours": [1.0],
            "total_vcpu_utilization_hours": [3.0],
            "allocated_vcpu_utilization_hours": [1.5],
            "borrowed_vcpu_utilization_hours": [1.5],
        }
    )


@pytest.fixture
def detailed_df():
    return pd.DataFrame(
        {
            "report_date": [datetime.strptime("2025-03-25", "%Y-%m-%d")],
            "namespace": ["test-namespace"],
            "period_start": [datetime.strptime("20:00:00", "%H:%M:%S")],
            "period_end": [datetime.strptime("21:00:00", "%H:%M:%S")],
            "team": ["test-team"],
            "task_name": ["test-task"],
            "instance": ["instance-1"],
            "status": ["Running"],
            "utilized_neuron_core_hours": [1.0],
            "utilized_neuron_core_count": [2],
            "utilized_gpu_hours": [2.0],
            "utilized_gpu_count": [1],
            "utilized_vcpu_hours": [3.0],
            "utilized_vcpu_count": [4],
            "priority_class": ["high"],
            "labels": [""],
        }
    )


@pytest.fixture
def header_info():
    return {
        "cluster_name": "test-cluster",
        "report_date": "20250325",
        "report_type": "summary",
        "start_date": "2025-03-25",
        "end_date": "2025-03-25",
        "days": 1,
    }


@pytest.fixture
def empty_missing_periods():
    return []


@pytest.fixture
def missing_periods():
    return [{"start_time": "start_time", "end_time": "end_time"}]


@pytest.fixture
def mock_pdf():
    with patch("fpdf.FPDF") as mock:
        yield mock.return_value


def test_column_config_initialization():
    generator = PDFReportGenerator()

    # Test summary columns
    assert len(generator.summary_columns) == 13
    assert isinstance(generator.summary_columns[0], ColumnConfig)
    assert generator.summary_columns[0].name == "report_date"

    # Test detailed columns
    assert len(generator.detailed_columns) == 16
    assert isinstance(generator.detailed_columns[0], ColumnConfig)
    assert generator.detailed_columns[0].name == "report_date"


def test_get_output_filename(header_info):
    generator = PDFReportGenerator()

    # Test single day
    filename = generator._get_output_filename(header_info)
    assert filename == "summary-report-2025-03-25.pdf"

    # Test multiple days
    header_info["days"] = 7
    header_info["end_date"] = "2025-03-31"
    filename = generator._get_output_filename(header_info)
    assert filename == "summary-report-2025-03-25-2025-03-31.pdf"


def test_add_report_header(mock_pdf, header_info, empty_missing_periods):
    generator = PDFReportGenerator()
    generator._add_report_header(mock_pdf, header_info, empty_missing_periods)

    assert mock_pdf.set_font.called
    assert mock_pdf.cell.called
    calls = mock_pdf.cell.call_args_list
    assert any("test-cluster" in str(call) for call in calls)
    assert any("Summary" in str(call) for call in calls)


def test_add_report_header_with_missing_periods(mock_pdf, header_info, missing_periods):
    generator = PDFReportGenerator()
    generator._add_report_header(mock_pdf, header_info, missing_periods)

    assert mock_pdf.set_font.called
    assert mock_pdf.cell.called
    calls = mock_pdf.cell.call_args_list
    assert any("test-cluster" in str(call) for call in calls)
    assert any("Summary" in str(call) for call in calls)
    assert any("start_time" in str(call) for call in calls)


@patch("hyperpod_usage_report.generators.pdf_generator.FPDF")
def test_generate_summary_report(
    mock_fpdf, summary_df, header_info, empty_missing_periods
):
    generator = PDFReportGenerator()
    output_file = generator.generate_summary_report(
        summary_df, header_info, empty_missing_periods
    )

    assert output_file == "summary-report-2025-03-25.pdf"
    mock_fpdf.return_value.output.assert_called_once_with(output_file)


@patch("hyperpod_usage_report.generators.pdf_generator.FPDF")
def test_generate_detailed_report(
    mock_fpdf, detailed_df, header_info, empty_missing_periods
):
    generator = PDFReportGenerator()
    header_info["report_type"] = "detailed"
    output_file = generator.generate_detailed_report(
        detailed_df, header_info, empty_missing_periods
    )

    assert output_file == "detailed-report-2025-03-25.pdf"
    mock_fpdf.return_value.output.assert_called_once_with(output_file)


def test_add_table_headers(mock_pdf):
    generator = PDFReportGenerator()

    # Test summary headers
    generator._add_table_headers(
        mock_pdf, generator.summary_columns, generator.summary_table_headers, False
    )
    assert mock_pdf.set_fill_color.called
    assert mock_pdf.cell.called

    # Reset mock
    mock_pdf.reset_mock()

    # Test detailed headers
    generator._add_table_headers(
        mock_pdf, generator.detailed_columns, generator.detailed_table_headers, True
    )
    assert mock_pdf.set_fill_color.called
    assert mock_pdf.cell.called


def test_add_table_content(mock_pdf, summary_df):
    generator = PDFReportGenerator()
    generator._add_table_content(mock_pdf, summary_df, generator.summary_columns)

    assert mock_pdf.set_font.called
    assert mock_pdf.cell.called


def test_formatter_functions():
    generator = PDFReportGenerator()

    # Test date formatter
    date_col = next(
        col for col in generator.summary_columns if col.name == "report_date"
    )
    formatted_date = date_col.formatter(datetime.strptime("2025-03-25", "%Y-%m-%d"))
    assert formatted_date == "2025-03-25"

    # Test numeric formatter
    numeric_col = next(
        col
        for col in generator.summary_columns
        if col.name == "total_neuron_core_utilization_hours"
    )
    formatted_num = numeric_col.formatter(1.234)
    assert formatted_num == "1.23"


@patch("fpdf.FPDF")
def test_multiple_day_report(mock_fpdf, summary_df, header_info, empty_missing_periods):
    generator = PDFReportGenerator()
    header_info["days"] = 7
    header_info["end_date"] = "2025-03-31"

    output_file = generator.generate_summary_report(
        summary_df, header_info, empty_missing_periods
    )
    assert output_file == "summary-report-2025-03-25-2025-03-31.pdf"
    os.remove(output_file)


def test_pdf_style_constants():
    assert PDFStyle.TITLE_FONT == ("Arial", "B", 16)
    assert PDFStyle.HEADER_FONT == ("Arial", "B", 10)
    assert PDFStyle.CONTENT_FONT == ("Arial", "", 8)
    assert PDFStyle.HEADER_BG_COLOR == (0, 0, 0)
    assert PDFStyle.HEADER_TEXT_COLOR == (255, 255, 255)
    assert PDFStyle.SUBHEADER_BG_COLOR == (200, 200, 200)
