# HyperPod Cluster Usage Report

This repository enables the HyperPod cluster usage report feature for AWS HyperPod clusters.

## Prerequisites

- AWS HyperPod cluster
- Python 3.8 or higher
- pip
- AWS CLI

Install the package:

```bash
pip install -e .
```

## Setup

### Step 1: Deploy CloudFormation

Deploy the CloudFormation stack using the following command:

```bash
aws cloudformation update-stack --stack-name STACK_NAME \
--template-body file://configuration/cloudformation/usage-report.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters \
ParameterKey=EKSClusterName,ParameterValue=CLUSTER_NAME
```
Configuration parameters:

- `EKSClusterName`: Name of your HyperPod cluster (required)
- `AthenaDBName`: Name of the Athena database (default: `usage_report`)
- `DataRetentionDays`: Number of days to retain data (default: `180`)

### Step 2: Install Helm Chart
[Add instructions for installing the Helm chart]

### Step 3: Report Generation
Generate usage reports using the following command:

```bash
python3 run.py --start-date YYYY-MM-DD \
               --end-date YYYY-MM-DD \
               --format [csv|pdf] \
               --database-name <AthenaDBName> \
               --type [summary|detailed] \
               --output-report-location s3://bucket-name/path/ \
               --cluster-name <EKSClusterName>
```
#### Parameters:
- `--start-date`: Start date of the report (YYYY-MM-DD format)
- `--end-date`: End date of the report (YYYY-MM-DD format)
- `--format`: Output format (`csv` or `pdf`)
- `--database-name`: Must match the `AthenaDBName` specified in Step 1
- `--type`: Report type
  - `summary`: Generates namespace-level aggregated reports
  - `detailed`: Generates task-level detailed reports
- `--output-report-location`: S3 bucket path where reports will be stored
- `--cluster-name`: Must match the `EKSClusterName` specified in Step 1

## Report Types

### Summary Report
- Provides aggregated resource usage by namespace
- Ideal for high-level resource consumption analysis
- Includes namespace-level metrics and statistics

### Detailed Report
- Provides granular resource usage by individual tasks
- Suitable for detailed analysis and troubleshooting
- Includes task-level metrics and resource allocation details

## Local Development

### Running Unit Tests

To run the unit tests locally:
```bash
pytest
```
This will execute all test cases in the test directory. The test suite includes unit tests for all major components of the usage report functionality.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

