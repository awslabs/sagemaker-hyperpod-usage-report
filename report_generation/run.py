import argparse

from src.hyperpod_usage_report.report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description="HyperPod Usage Report Generator",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--start-date", required=True, help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end-date", required=True, help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "csv"],
        required=True,
        help="Output format (pdf or csv)",
    )
    parser.add_argument("--database-name", required=True, help="Athena database name")
    parser.add_argument(
        "--database-workgroup-name",
        required=True,
        help="workgroup for the athena database",
    )
    parser.add_argument(
        "--type",
        choices=["summary", "detailed"],
        required=True,
        help="Report type (summary or detailed)",
    )
    parser.add_argument(
        "--output-report-location",
        required=True,
        help="S3 location for output (s3://bucket/path)",
    )
    parser.add_argument("--cluster-name", required=True, help="Hyperpod Cluster Name")
    parser.add_argument("--namespace", required=False, help="Filter report by namespace (optional)")
    parser.add_argument("--task", required=False, help="Filter report by task name (optional)")
    
    args = parser.parse_args()

    generator = ReportGenerator(
        start_date=args.start_date,
        end_date=args.end_date,
        cluster_name=args.cluster_name,
        database_name=args.database_name,
        database_workgroup_name=args.database_workgroup_name,
        report_type=args.type,
        output_location=args.output_report_location,
        format=args.format,
        namespace=args.namespace,
        task=args.task,
    )

    generator.generate_report()


if __name__ == "__main__":
    main()
