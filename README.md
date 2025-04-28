# HyperPod Cluster Usage Report

This repository enables the HyperPod cluster usage report feature for AWS HyperPod clusters.

## Prerequisites

- AWS HyperPod cluster
- Python 3.8 or higher
- pip
- AWS CLI

## Setup

### Set local environment in your terminal
```
export AWS_ACCOUNT=<customer account>
export AWS_REGION=<aws region>
export HYPERPOD_CLUSTER_NAME=<hyperpod cluster name>
export EKS_CLUSTER_NAME=<eks cluster name>
export USAGE_REPORT_CFN_STACK_NAME=sagemaker-hyperpod-usage-report
export HYPERPOD_CLUSTER_ID=$(aws sagemaker describe-cluster --cluster-name $HYPERPOD_CLUSTER_NAME --region $AWS_REGION | jq -r '.ClusterArn | split("/")[-1]')
```

### Step 1: Deploy CloudFormation

Deploy the CloudFormation stack using the following command:

```bash
aws cloudformation create-stack --stack-name $USAGE_REPORT_CFN_STACK_NAME \
--template-body file://cloudformation/usage-report.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters \
ParameterKey=EKSClusterName,ParameterValue=$EKS_CLUSTER_NAME ParameterKey=HyperPodClusterId,ParameterValue=$HYPERPOD_CLUSTER_ID
```
Configuration parameters:

- `EKSClusterName`: Name of your EKS cluster (required)
- `HyperPodClusterId`: Id of your HyperPod cluster (required)
- `AthenaDBName`: Name of the Athena database (default: `usage_report`)
- `DataRetentionDays`: Number of days to retain data (default: `180`)
- `InstallPodIdentityAddon`: Whether to install the Pod Identity Addon, (default: true)

Notes:
- Make sure the `eks-auth:AssumeRoleForPodIdentity` permission exists in the IAM execution role for the SageMaker HyperPod cluster
- If the stack creation failed with error `eks-pod-identity-agent already exists` please recreate the stack with additional parameters `ParameterKey=InstallPodIdentityAddon,ParameterValue=false` as below 
```bash
aws cloudformation create-stack --stack-name $USAGE_REPORT_CFN_STACK_NAME \
--template-body file://cloudformation/usage-report.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters \
ParameterKey=EKSClusterName,ParameterValue=$EKS_CLUSTER_NAME ParameterKey=HyperPodClusterId,ParameterValue=$HYPERPOD_CLUSTER_ID ParameterKey=InstallPodIdentityAddon,ParameterValue=false
```
- If the EKS AccessEntry for the role already exists, the stack deployment may fail with the error: `The specified access entry resource is already in use on this cluster`.
  We recommend removing the AccessEntry to allow the CloudFormation stack to create it.

### Step 2: Install Helm Chart
To configure the connection to your cluster, run
```
aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION
```
Then install the Helm chart
```
cd helm_chart
helm install sagemaker-hyperpod-usage-report ./SageMakerHyperPodUsageReportChart --set region=$AWS_REGION --set clusterName=$HYPERPOD_CLUSTER_NAME --set s3BucketName=$AWS_ACCOUNT-$AWS_REGION-$HYPERPOD_CLUSTER_ID-usage-report
```
### Step 3: Report Generation
Generate usage reports using the following command:

Install the package:

```bash
cd report_generation
pip install -e .
```

```bash
python3 run.py --start-date YYYY-MM-DD \
               --end-date YYYY-MM-DD \
               --format [csv|pdf] \
               --database-name <AthenaDBName> \
               --type [summary|detailed] \
               --output-report-location s3://bucket-name/path/ \
               --cluster-name $EKS_CLUSTER_NAME
```
#### Parameters:
- `--start-date`: Start date of the report (YYYY-MM-DD format)
- `--end-date`: End date of the report (YYYY-MM-DD format)
- `--format`: Output format (`csv` or `pdf`)
- `--database-name`: Must match the `AthenaDBName` specified in Step 1, default: `usage_report` 
- `--type`: Report type
  - `summary`: Generates namespace-level aggregated reports
  - `detailed`: Generates task-level detailed reports
- `--output-report-location`: S3 bucket path where reports will be stored
- `--cluster-name`: EKS cluster name

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

