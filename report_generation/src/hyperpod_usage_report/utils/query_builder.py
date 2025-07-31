class QueryBuilder:
    @staticmethod
    def build_fetch_report_data_query(
        report_type: str, start_date: str, end_date: str, namespace: str = None, task: str = None
    ) -> str:
        where_clause = f"DATE(report_date) BETWEEN DATE('{start_date}') AND DATE('{end_date}')"
        
        if namespace:
            where_clause += f" AND namespace = '{namespace}'"
        
        if task:
            where_clause += f" AND task_name = '{task}'"
        
        if report_type == "summary":
            return f"""
            SELECT *
            FROM summary_report
            WHERE {where_clause}
            ORDER BY report_date, namespace, team
            """
        elif report_type == "detailed":
            return f"""
            SELECT *
            FROM detailed_report
            WHERE {where_clause}
            ORDER BY report_date, period_start, namespace, team, task_name
            """
        else:
            raise ValueError(
                f"Invalid report type '{report_type}'. Must be either 'summary' or 'detailed'."
            )

    @staticmethod
    def build_fetch_heartdub_query(start_date: str, end_date: str) -> str:
        return f"""
            SELECT DISTINCT cluster, year, month, day, hour
            FROM heartdub
            WHERE DATE(timestamp) BETWEEN DATE('{start_date}')
                AND DATE('{end_date}')
        """
