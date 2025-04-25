from datetime import datetime
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.hyperpod_usage_report.generators.csv_generator import CSVReportGenerator


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
            "period_start": [datetime.strptime("20:00:00", "%H:%M:%S")],
            "period_end": [datetime.strptime("21:00:00", "%H:%M:%S")],
            "namespace": ["test-namespace"],
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
        "report_date": "2025-03-25",
        "report_type": "summary",
        "start_date": "2025-03-25",
        "end_date": "2025-03-25",
        "days": 1,
    }


@pytest.fixture
def empty_missing_periods():
    return []


def test_generate_report_header(header_info):
    # Arrange
    generator = CSVReportGenerator()
    expected_header = [
        "Amazon SageMaker HyperPod",
        "ClusterName: test-cluster",
        "Type: Summary Utilization Report",
        "Date Generated: 2025-03-25",
        "Date Range (UTC): 2025-03-25 to 2025-03-25",
    ]

    # Act
    header = generator.generate_report_header(header_info)

    # Assert
    assert header == expected_header


def test_generate_summary_report_single_day(
    summary_df, header_info, empty_missing_periods
):
    # Arrange
    generator = CSVReportGenerator()
    expected_filename = "summary-report-2025-03-25.csv"
    m = mock_open()

    # Act
    with patch("builtins.open", m):
        output_file = generator.generate_summary_report(
            summary_df, header_info, empty_missing_periods
        )

    # Assert
    assert output_file == expected_filename
    m.assert_called_once_with(expected_filename, "w")


def test_generate_summary_report_multiple_days(
    summary_df, header_info, empty_missing_periods
):
    # Arrange
    generator = CSVReportGenerator()
    header_info["days"] = 7
    header_info["end_date"] = "2025-03-31"
    expected_filename = "summary-report-2025-03-25-2025-03-31.csv"
    m = mock_open()

    # Act
    with patch("builtins.open", m):
        output_file = generator.generate_summary_report(
            summary_df, header_info, empty_missing_periods
        )

    # Assert
    assert output_file == expected_filename
    m.assert_called_once_with(expected_filename, "w")


def test_generate_detailed_report_single_day(
    detailed_df, header_info, empty_missing_periods
):
    # Arrange
    generator = CSVReportGenerator()
    header_info["report_type"] = "detailed"
    expected_filename = "detailed-report-2025-03-25.csv"
    m = mock_open()

    # Act
    with patch("builtins.open", m):
        output_file = generator.generate_detailed_report(
            detailed_df, header_info, empty_missing_periods
        )

    # Assert
    assert output_file == expected_filename
    m.assert_called_once_with(expected_filename, "w")


def test_generate_detailed_report_multiple_days(
    detailed_df, header_info, empty_missing_periods
):
    # Arrange
    generator = CSVReportGenerator()
    header_info["report_type"] = "detailed"
    header_info["days"] = 7
    header_info["end_date"] = "2025-03-31"
    expected_filename = "detailed-report-2025-03-25-2025-03-31.csv"
    m = mock_open()

    # Act
    with patch("builtins.open", m):
        output_file = generator.generate_detailed_report(
            detailed_df, header_info, empty_missing_periods
        )

    # Assert
    assert output_file == expected_filename
    m.assert_called_once_with(expected_filename, "w")


def test_summary_report_content(summary_df, header_info, empty_missing_periods):
    # Arrange
    generator = CSVReportGenerator()
    m = mock_open()

    # Act
    with patch("builtins.open", m) as mock_file:
        generator.generate_summary_report(
            summary_df, header_info, empty_missing_periods
        )

    # Assert
    write_calls = [call.args[0] for call in mock_file().write.call_args_list]
    assert any("ClusterName: test-cluster\n" in call for call in write_calls)
    assert any(
        "2025-03-25,test-namespace,test-team,t2.micro" in call for call in write_calls
    )


def test_detailed_report_content(detailed_df, header_info, empty_missing_periods):
    # Arrange
    generator = CSVReportGenerator()
    header_info["report_type"] = "detailed"
    m = mock_open()

    # Act
    with patch("builtins.open", m) as mock_file:
        generator.generate_detailed_report(
            detailed_df, header_info, empty_missing_periods
        )

    # Assert
    write_calls = [call.args[0] for call in mock_file().write.call_args_list]
    assert any("ClusterName: test-cluster\n" in call for call in write_calls)
    assert any(
        "2025-03-25,20:00:00,21:00:00,test-namespace,test-team,test-task" in call
        for call in write_calls
    )
