import pytest

from src.hyperpod_usage_report.utils.query_builder import QueryBuilder


def test_build_query_summary():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    report_type = "summary"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date
    )

    # Assert
    assert "FROM summary_report" in query
    assert f"DATE('{start_date}')" in query
    assert f"DATE('{end_date}')" in query


def test_build_query_detailed():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    report_type = "detailed"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date
    )

    # Assert
    assert "FROM detailed_report" in query
    assert f"DATE('{start_date}')" in query
    assert f"DATE('{end_date}')" in query


def test_build_query_invalid_type():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    report_type = "invalid"

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        QueryBuilder.build_fetch_report_data_query(report_type, start_date, end_date)
    assert "Invalid report type" in str(exc_info.value)


def test_build_fetch_heartdub_query():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"

    # Act
    query = QueryBuilder.build_fetch_heartdub_query(start_date, end_date)

    # Assert
    assert "FROM heartdub" in query
    assert f"DATE('{start_date}')" in query
    assert f"DATE('{end_date}')" in query
    assert "SELECT DISTINCT cluster" in query
    assert "year, month, day, hour" in query


def test_build_fetch_heartdub_query_different_dates():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-26"

    # Act
    query = QueryBuilder.build_fetch_heartdub_query(start_date, end_date)

    # Assert
    assert "FROM heartdub" in query
    assert f"DATE('{start_date}')" in query
    assert f"DATE('{end_date}')" in query
    assert "BETWEEN" in query


def test_build_query_summary_with_team():
    # Arrange
    report_type = "summary"
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    namespace = "test-namespace"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert f"AND namespace = '{namespace}'" in query


def test_build_query_detailed_with_team():
    # Arrange
    report_type = "detailed"
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    namespace = "data-science"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert f"AND namespace = '{namespace}'" in query


def test_build_query_summary_without_team():
    # Arrange
    report_type = "summary"
    start_date = "2025-03-25"
    end_date = "2025-03-25"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace=None
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert "AND namespace =" not in query


def test_build_query_detailed_without_team():
    # Arrange
    report_type = "detailed"
    start_date = "2025-03-25"
    end_date = "2025-03-25"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace=None
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert "AND namespace =" not in query


def test_build_query_with_empty_team():
    # Arrange
    report_type = "summary"
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    namespace = ""

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert "AND namespace =" not in query


def test_build_query_with_team_containing_quotes():
    # Arrange
    report_type = "summary"
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    namespace = "ml-team"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert f"AND namespace = '{namespace}'" in query


def test_build_query_with_task_containing_quotes():
    # Arrange
    report_type = "summary"
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    namespace = "ml-team"
    task = "training-job-1"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace, task
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert "AND namespace = 'ml-team'" in query
    assert "AND task_name = 'training-job-1'" in query


def test_build_query_with_task_only():
    # Arrange
    report_type = "detailed"
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    namespace = None
    task = "inference-job-2"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace, task
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert "AND namespace =" not in query
    assert "AND task_name = 'inference-job-2'" in query


def test_build_query_with_team_and_task():
    # Arrange
    report_type = "summary"
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    namespace = "data-science"
    task = "model-training"

    # Act
    query = QueryBuilder.build_fetch_report_data_query(
        report_type, start_date, end_date, namespace, task
    )

    # Assert
    assert "WHERE DATE(report_date) BETWEEN DATE('2025-03-25') AND DATE('2025-03-25')" in query
    assert "AND namespace = 'data-science'" in query
    assert "AND task_name = 'model-training'" in query
