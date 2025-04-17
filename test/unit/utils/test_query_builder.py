import pytest

from hyperpod_usage_report.utils.query_builder import QueryBuilder


def test_build_query_summary():
    # Arrange
    start_date = "2025-03-25"
    end_date = "2025-03-25"
    report_type = "summary"

    # Act
    query = QueryBuilder.build_query(report_type, start_date, end_date)

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
    query = QueryBuilder.build_query(report_type, start_date, end_date)

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
        QueryBuilder.build_query(report_type, start_date, end_date)
    assert "Invalid report type" in str(exc_info.value)
