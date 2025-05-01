from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.hyperpod_usage_report.report_generator import ReportGenerator


@pytest.fixture
def report_generator():
    return ReportGenerator(
        start_date="2025-03-25",
        end_date="2025-03-25",
        cluster_name="dummy-cluster",
        database_name="dummy-db",
        database_workgroup_name='dummy-workgroup',
        report_type="summary",
        output_location="s3://dummy-bucket/reports",
        format="csv",
    )


def test_report_generator_init(report_generator):
    assert report_generator.database_name == "dummy-db"
    assert report_generator.report_type == "summary"
    assert report_generator.format == "csv"
    assert isinstance(report_generator.start_date, datetime)
    assert isinstance(report_generator.end_date, datetime)


@patch("src.hyperpod_usage_report.report_generator.wr")
def test_fetch_data(mock_wr, report_generator):
    # Arrange
    mock_df = Mock()
    mock_wr.athena.read_sql_query.return_value = mock_df

    # Act
    result = report_generator._fetch_data()

    # Assert
    assert result == mock_df
    mock_wr.athena.read_sql_query.assert_called_once()


@patch("src.hyperpod_usage_report.report_generator.wr")
def test_fetch_data_error(mock_wr, report_generator):
    # Arrange
    mock_wr.athena.read_sql_query.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        report_generator._fetch_data()
    assert "Database error" in str(exc_info.value)
