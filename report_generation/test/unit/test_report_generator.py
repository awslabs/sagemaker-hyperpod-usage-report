from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import pandas as pd

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


def test_report_generator_init_with_team():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    output_location = "s3://test-bucket/reports/"
    database_workgroup_name = "test-workgroup"
    format = "csv"
    database_name = "test-database"
    report_type = "summary"
    cluster_name = "test-cluster"
    namespace = "test-namespace"

    # Act
    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        output_location=output_location,
        database_workgroup_name=database_workgroup_name,
        format=format,
        database_name=database_name,
        report_type=report_type,
        cluster_name=cluster_name,
        namespace=namespace,
    )

    # Assert
    assert generator.namespace == namespace


def test_report_generator_init_without_team():
    # Arrange & Act
    generator = ReportGenerator(
        start_date="2025-03-25",
        end_date="2025-03-25",
        cluster_name="dummy-cluster",
        database_name="dummy-db",
        database_workgroup_name='dummy-workgroup',
        report_type="summary",
        output_location="s3://dummy-bucket/reports",
        format="csv",
    )
    
    # Assert
    assert generator.namespace is None


def test_prepare_header_info_with_team():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    output_location = "s3://test-bucket/reports/"
    database_workgroup_name = "test-workgroup"
    format = "csv"
    database_name = "test-database"
    report_type = "summary"
    cluster_name = "test-cluster"
    namespace = "ml-team"

    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        output_location=output_location,
        database_workgroup_name=database_workgroup_name,
        format=format,
        database_name=database_name,
        report_type=report_type,
        cluster_name=cluster_name,
        namespace=namespace,
    )

    # Act
    header_info = generator._prepare_header_info()

    # Assert
    assert header_info["namespace"] == "ml-team"


def test_prepare_header_info_without_team():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    output_location = "s3://test-bucket/reports/"
    database_workgroup_name = "test-workgroup"
    format = "csv"
    database_name = "test-database"
    report_type = "summary"
    cluster_name = "test-cluster"
    namespace = None

    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        output_location=output_location,
        database_workgroup_name=database_workgroup_name,
        format=format,
        database_name=database_name,
        report_type=report_type,
        cluster_name=cluster_name,
        namespace=namespace,
    )

    # Act
    header_info = generator._prepare_header_info()

    # Assert
    assert "namespace" not in header_info


def test_prepare_header_info_with_task():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    output_location = "s3://test-bucket/reports/"
    database_workgroup_name = "test-workgroup"
    format = "csv"
    database_name = "test-database"
    report_type = "summary"
    cluster_name = "test-cluster"
    namespace = "ml-team"
    task = "training-job-1"

    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        output_location=output_location,
        database_workgroup_name=database_workgroup_name,
        format=format,
        database_name=database_name,
        report_type=report_type,
        cluster_name=cluster_name,
        namespace=namespace,
        task=task,
    )

    # Act
    header_info = generator._prepare_header_info()

    # Assert
    assert header_info["namespace"] == "ml-team"
    assert header_info["task"] == "training-job-1"


@patch("src.hyperpod_usage_report.report_generator.wr")
@patch("src.hyperpod_usage_report.report_generator.QueryBuilder")
def test_fetch_data_with_team(mock_query_builder, mock_wr):
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    output_location = "s3://test-bucket/reports/"
    database_workgroup_name = "test-workgroup"
    format = "csv"
    database_name = "test-database"
    report_type = "summary"
    cluster_name = "test-cluster"
    namespace = "data-science"

    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        output_location=output_location,
        database_workgroup_name=database_workgroup_name,
        format=format,
        database_name=database_name,
        report_type=report_type,
        cluster_name=cluster_name,
        namespace=namespace,
    )

    mock_df = pd.DataFrame({"test": [1, 2, 3]})
    mock_wr.athena.read_sql_query.return_value = mock_df

    # Act
    result = generator._fetch_data()

    # Assert
    mock_query_builder.build_fetch_report_data_query.assert_called_once_with(
        "summary", "2025-03-25", "2025-03-25", "data-science", None
    )
    pd.testing.assert_frame_equal(result, mock_df)


@patch("src.hyperpod_usage_report.report_generator.wr")
@patch("src.hyperpod_usage_report.report_generator.QueryBuilder")
def test_fetch_data_without_team(mock_query_builder, mock_wr):
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    output_location = "s3://test-bucket/reports/"
    database_workgroup_name = "test-workgroup"
    format = "csv"
    database_name = "test-database"
    report_type = "summary"
    cluster_name = "test-cluster"
    namespace = None

    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        output_location=output_location,
        database_workgroup_name=database_workgroup_name,
        format=format,
        database_name=database_name,
        report_type=report_type,
        cluster_name=cluster_name,
        namespace=namespace,
    )

    mock_df = pd.DataFrame({"test": [1, 2, 3]})
    mock_wr.athena.read_sql_query.return_value = mock_df

    # Act
    result = generator._fetch_data()

    # Assert
    mock_query_builder.build_fetch_report_data_query.assert_called_once_with(
        "summary", "2025-03-25", "2025-03-25", None, None
    )
    pd.testing.assert_frame_equal(result, mock_df)


def test_report_generator_init_without_team():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    output_location = "s3://test-bucket/reports/"
    database_workgroup_name = "test-workgroup"
    format = "csv"
    database_name = "test-database"
    report_type = "summary"
    cluster_name = "test-cluster"
    namespace = None
    task = None

    # Act
    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        output_location=output_location,
        database_workgroup_name=database_workgroup_name,
        format=format,
        database_name=database_name,
        report_type=report_type,
        cluster_name=cluster_name,
        namespace=namespace,
        task=task,
    )

    # Assert
    assert generator.namespace is None
    assert generator.task is None


def test_report_generator_init_with_task():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    output_location = "s3://test-bucket/reports/"
    database_workgroup_name = "test-workgroup"
    format = "csv"
    database_name = "test-database"
    report_type = "summary"
    cluster_name = "test-cluster"
    namespace = "ml-team"
    task = "training-job-1"

    # Act
    generator = ReportGenerator(
        start_date=start_date,
        end_date=end_date,
        output_location=output_location,
        database_workgroup_name=database_workgroup_name,
        format=format,
        database_name=database_name,
        report_type=report_type,
        cluster_name=cluster_name,
        namespace=namespace,
        task=task,
    )

    # Assert
    assert generator.namespace == "ml-team"
    assert generator.task == "training-job-1"
