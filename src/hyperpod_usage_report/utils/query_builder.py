class QueryBuilder:
    @staticmethod
    def build_query(report_type: str, start_date: str, end_date: str) -> str:
        if report_type == "summary":
            return f"""
            SELECT *
            FROM summary_report
            WHERE DATE(report_date) BETWEEN DATE('{start_date}')
                AND DATE('{end_date}')
            ORDER BY report_date, namespace, team
            """
        elif report_type == "detailed":
            return f"""
            SELECT *
            FROM detailed_report
            WHERE DATE(report_date) BETWEEN DATE('{start_date}')
                AND DATE('{end_date}')
            ORDER BY report_date, namespace, team, task_name
            """
        else:
            raise ValueError(
                f"Invalid report type '{report_type}'. Must be either 'summary' or 'detailed'."
            )
