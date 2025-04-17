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

### Step 3: Setup Pod Identity
The Helm chart creates a Kubernetes service account `sagemaker-hyperpod-usage-report-service-account`. 
We need to create a pod identity association to allow the service account to put resource usage data in the S3 bucket.


1. Make sure the `eks-auth:AssumeRoleForPodIdentity` permission exists in the IAM execution role for the SageMaker HyperPod cluster.
2. If the `eks-pod-identity-agent` add-on is not already installed on your EKS cluster, install the add-on on the EKS cluster.
```
aws eks create-addon \
    --cluster-name <eks-cluster-name> \
    --addon-name eks-pod-identity-agent
```
3. Create a `trust-relationship.json` file for a new role for pods to call S3 APIs.
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowEksAuthToAssumeRoleForPodIdentity",
            "Effect": "Allow",
            "Principal": {
                "Service": "pods.eks.amazonaws.com"
            },
            "Action": [
                "sts:AssumeRole",
                "sts:TagSession"
            ]
        }
    ]
}
```
4. Create a new IAM role to be assumed by the Kubernetes service account and attach the trust relationship.
```
aws iam create-role --role-name hyperpod-usage-report-service-account-role \
    --assume-role-policy-document file://trust-relationship.json \
    --description "allow pods to put data in s3"
```
5. Create the following policy that grants pods access to put resource usage data in S3.
   Please use the name of the bucket created by the CloudFormation template in Step 1 in "Resource".
```
cat >hyperpod-usage-report-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::<usage-report-s3-bucket_name>"
        }
    ]
}
EOF
```
6. Attach the `hyperpod-usage-report-policy` policy to the `hyperpod-usage-report-service-account-role` using the policy document saved in the previous step.
```
aws iam put-role-policy \
  --role-name hyperpod-usage-report-service-account-role \
  --policy-name hyperpod-usage-report-policy \
  --policy-document file://hyperpod-usage-report-policy.json
```
7. Create a pod identity association.
```
aws eks create-pod-identity-association \
    --cluster-name EKS_CLUSTER_NAME \
    --role-arn arn:aws:iam::<account-id>:hyperpod-usage-report-service-account-role \
    --namespace default \
    --service-account sagemaker-hyperpod-usage-report-service-account
```

### Step 4: Report Generation
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

