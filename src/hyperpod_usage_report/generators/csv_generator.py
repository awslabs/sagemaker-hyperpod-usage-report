import pandas as pd

from .base import BaseReportGenerator


class CSVReportGenerator(BaseReportGenerator):
    def generate_report_header(self, header_info: dict) -> list:
        """Generate standard report header"""
        time_period = f"{header_info['start_date']} to {header_info['end_date']}"

        return [
            f"ClusterName: {header_info['cluster_name']}",
            f"Type: {header_info['report_type'].title()} Utilization Report",
            f"Date Generated: {header_info['report_date']}",
            f"Date Range: {time_period}",
        ]

    def generate_summary_report(self, df: pd.DataFrame, header_info: dict) -> str:
        """Generate CSV Summary report"""
        base_name = f"{header_info['report_type']}-report-{header_info['start_date']}"
        output_file = (
            f"{base_name}-{header_info['end_date']}.pdf"
            if int(header_info["days"]) > 1
            else f"{base_name}.csv"
        )

        # Column headers (multi-level)
        resource_headers = [
            ",,,Instance,NeuronCore,,,GPU,,,vCPU,,",
            "Date,Namespace,Team,Type,Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours),"
            + "Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours),"
            + "Total utilization (hours),Allocated utilization (hours),Borrowed utilization (hours)",
        ]

        # Reorder DataFrame columns to match desired output
        df = df[
            [
                "report_date",
                "namespace",
                "team",
                "instance_type",
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
        ]

        # Write to file
        with open(output_file, "w") as f:
            for row in self.generate_report_header(header_info):
                f.write(f"{row}\n")

            for header_row in resource_headers:
                f.write(f"{header_row}\n")

            # Write data
            for _, row in df.iterrows():
                formatted_row = [
                    row["report_date"].strftime("%Y-%m-%d"),
                    row["namespace"],
                    row["team"],
                    row["instance_type"],
                    f"{row['total_neuron_core_utilization_hours']:.2f}",
                    f"{row['allocated_neuron_core_utilization_hours']:.2f}",
                    f"{row['borrowed_neuron_core_utilization_hours']:.2f}",
                    f"{row['total_gpu_utilization_hours']:.2f}",
                    f"{row['allocated_gpu_utilization_hours']:.2f}",
                    f"{row['borrowed_gpu_utilization_hours']:.2f}",
                    f"{row['total_vcpu_utilization_hours']:.2f}",
                    f"{row['allocated_vcpu_utilization_hours']:.2f}",
                    f"{row['borrowed_vcpu_utilization_hours']:.2f}",
                ]
                f.write(",".join(formatted_row) + "\n")

        return output_file

    def generate_detailed_report(self, df: pd.DataFrame, header_info: dict) -> str:
        """Generate CSV Detailed report"""
        base_name = f"{header_info['report_type']}-report-{header_info['start_date']}"
        output_file = (
            f"{base_name}-{header_info['end_date']}.pdf"
            if int(header_info["days"]) > 1
            else f"{base_name}.csv"
        )

        # Column headers (multi-level)
        resource_headers = [
            ",,,,,,NeuronCore,,GPU,,vCPU,,",
            "Date,Namespace,Team,Task,Instance,Status,Total utilization (hour),"
            + "Total utilization (count),Total utilization (hour),Total utilization (count),"
            + "Total utilization (hour),Total utilization (count),Priority class",
        ]

        # Reorder DataFrame columns to match desired output
        df = df[
            [
                "report_date",
                "namespace",
                "team",
                "task_name",
                "instance",
                "status",
                "utilized_neuron_core_hours",
                "utilized_neuron_core_count",
                "utilized_gpu_hours",
                "utilized_gpu_count",
                "utilized_vcpu_hours",
                "utilized_vcpu_count",
                "priority_class",
            ]
        ]

        # Write to file
        with open(output_file, "w") as f:
            for row in self.generate_report_header(header_info):
                f.write(f"{row}\n")

            for header_row in resource_headers:
                f.write(f"{header_row}\n")

            # Write data
            for _, row in df.iterrows():
                formatted_row = [
                    row["report_date"].strftime("%Y-%m-%d"),
                    row["namespace"],
                    row["team"],
                    row["task_name"],
                    row["instance"],
                    row["status"],
                    f"{row['utilized_neuron_core_hours']:.2f}",
                    f"{row['utilized_neuron_core_count']:.2f}",
                    f"{row['utilized_gpu_hours']:.2f}",
                    f"{row['utilized_gpu_count']:.2f}",
                    f"{row['utilized_vcpu_hours']:.2f}",
                    f"{row['utilized_vcpu_count']:.2f}",
                    row["priority_class"],
                ]
                f.write(",".join(formatted_row) + "\n")

        return output_file
