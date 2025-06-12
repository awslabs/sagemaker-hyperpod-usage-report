# HyperPod Cluster Usage Report

## Overview

Usage reporting in SageMaker HyperPod EKS-orchestrated clusters provides visibility into compute resource consumption. The capability allows organizations to implement transparent cost attribution, allocating cluster costs to teams, projects, or departments **based on their actual usage**. By tracking metrics such as GPU/CPU hours, and Neuron Core utilization over time, usage reporting complements SageMaker HyperPod's [Task Governance](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance.html) functionality, ensuring fair cost attribution in shared multi-tenant clusters by: 
- Eliminating guesswork in cost allocation
- Directly linking expenses to measurable resource consumption
- Enforcing usage-based accountability in shared infrastructure environments



## Table of Contents

1. [Set up Usage Reporting](#set-up-usage-reporting)
    - [Prerequisites](#prerequisites)
    - [Install Usage Report Infrastructure using CloudFormation](#install-usage-report-infrastructure-using-cloudformation)
    - [Install Usage Report Kubernetes Operator using Helm](#install-usage-report-kubernetes-operator-using-helm)
1. [Generate Reports](#generate-reports) 
1. [Clean Up Resources](#clean-up-resources) 
1. [Local Development](#local-development) 
1. [Attributions and Open Source Acknowledgments](#attributions-and-open-source-acknowledgments)
1. [Contributing](#contributing)
1. [License](#license)



## Set up Usage Reporting

Usage reporting in SageMaker HyperPod requires deploying the SageMaker HyperPod usage report infrastructure using a CloudFormation stack and installing the SageMaker HyperPod usage report Kubernetes operator using a Helm chart.

To successfully deploy and use the SageMaker HyperPod usage report, you should meet the following prerequisites.

### Prerequisites

* Have a running EKS-orchestrated SageMaker HyperPod cluster (Kubernetes version >= 1.30) with the [Task Governance](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance-setup.html) add-on.

* Have AWS CLI, kubectl, and Helm (package manager for Kubernetes - version >= 3.17.1) installed.

* A Python environment (version >= 3.9).

* Clone the GitHub repository sagemaker-hyperpod-usage-report.

    ```sh
    git clone https://github.com/awslabs/sagemaker-hyperpod-usage-report
    ```

* Set the following local environment variables in your terminal:

  **Note**
     -  To install the usage report, you need an *Installer* IAM role and with appropriate permissions. You can either create a new IAM role and leave the role policies blank for now, or reuse an existing role such as your current administrator role. Use the selected role name in the `USAGE_REPORT_INSTALLER_ROLE_NAME` variable. You will populate the role policies in the upcoming configuration steps.

    ```sh
    # Set up the environment variable
    export AWS_ACCOUNT=<account number>
    export AWS_REGION=<region>
    export HYPERPOD_CLUSTER_NAME=<hyperpod cluster name>
    export EKS_CLUSTER_NAME=<eks cluster name>
    export USAGE_REPORT_INSTALLER_ROLE_NAME=<Installer IAM role name>
    export USAGE_REPORT_OPERATOR_NAME=hyperpod-usage-report <keep under 22 characters if custom>
    export HYPERPOD_CLUSTER_ID=$(aws sagemaker describe-cluster --cluster-name ml-cluster --region $AWS_REGION | jq -r '.ClusterArn | split("/")[-1]')

    aws configure set region $AWS_REGION
    ```
    Verify the content of your variables:
    ```sh
    echo "AWS_ACCOUNT is $AWS_ACCOUNT"
    echo "AWS_REGION is $AWS_REGION"
    echo "HYPERPOD_CLUSTER_NAME is $HYPERPOD_CLUSTER_NAME"
    echo "EKS_CLUSTER_NAME is $EKS_CLUSTER_NAME"
    echo "USAGE_REPORT_INSTALLER_ROLE_NAME is $USAGE_REPORT_INSTALLER_ROLE_NAME"
    echo "USAGE_REPORT_OPERATOR_NAME is $USAGE_REPORT_OPERATOR_NAME"
    echo "HYPERPOD_CLUSTER_ID is $HYPERPOD_CLUSTER_ID"
    ```
*   Set up `kubectl` authentication and context for accessing the EKS cluster
  
    * Start by running the `aws eks update-kubeconfig` command to update your local kube config file (located at ~/.kube/config) with the credentials and configuration needed to connect to your EKS cluster using the `kubectl` command.

        ```sh
        aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME
        ```

    * You can verify that you are connected to the EKS cluster by running:

        ```sh
        kubectl config current-context 
        ```

        `arn:aws:eks:$AWS_REGION:$AWS_ACCOUNT:cluster/$EKS_CLUSTER_NAME`

  * Generate and attach the required IAM policies.
    * Populate the IAM policy document for your *Installer* role from the template provided in `permissions/usage-report-installer-policy.json.template`.
      ```sh
      INPUT_FILE="permissions/usage-report-installer-policy.json.template"
      OUTPUT_FILE="permissions/usage-report-installer-policy.json"
      sed \
      -e "s/AWS_REGION/$AWS_REGION/g" \
      -e "s/AWS_ACCOUNT/$AWS_ACCOUNT/g" \
      -e "s/USAGE_REPORT_OPERATOR_NAME/$USAGE_REPORT_OPERATOR_NAME/g" \
      -e "s/HYPERPOD_CLUSTER_ID/$HYPERPOD_CLUSTER_ID/g" \
      -e "s/EKS_CLUSTER_NAME/$EKS_CLUSTER_NAME/g" \
      -e "s/USAGE_REPORT_INSTALLER_ROLE_NAME/$USAGE_REPORT_INSTALLER_ROLE_NAME/g" \
      "$INPUT_FILE" > "$OUTPUT_FILE"
      ```
    * Attach the `permissions/usage-report-installer-policy.json` IAM policy to the IAM *Installer* role that performs AWS CLI, kubectl, and helm operations. This ensures usage report installers have the required permissions to install and manage SageMaker HyperPod Usage report data capture.

      To embed the inline policy in an existing role, use the following command:

      ```sh
      aws iam put-role-policy \
      --role-name $USAGE_REPORT_INSTALLER_ROLE_NAME  \
      --policy-name sagemaker-hyperpod-usage-report \
      --policy-document file://permissions/usage-report-installer-policy.json
      ```

      To verify that the policy has been added correctly, run:

      ```sh
      aws iam get-role-policy \
      --role-name $USAGE_REPORT_INSTALLER_ROLE_NAME \
      --policy-name sagemaker-hyperpod-usage-report
      ```

* Create a dedicated Kubernetes namespace for the usage report operator:

   * In `sagemaker-hyperpod-usage-report`, run the following command to create the namespace `$USAGE_REPORT_OPERATOR_NAME`: 

      ```sh
      INPUT_FILE="permissions/usage-report-namespace.yaml.template"
      OUTPUT_FILE="permissions/usage-report-namespace.yaml"
      sed \
      -e "s/NAMESPACE/$USAGE_REPORT_OPERATOR_NAME/g" \
      "$INPUT_FILE" > "$OUTPUT_FILE"

      kubectl apply -f permissions/usage-report-namespace.yaml
      ```

* Create custom RBAC permissions for deploying the HyperPod usage report Kubernetes operator helm chart on the cluster:

    * In `sagemaker-hyperpod-usage-report`, run the following command to setup the RBAC permissions in your EKS cluster.

        ```sh
        INPUT_FILE="permissions/usage-report-installer-cluster-policy.yaml.template"
        OUTPUT_FILE="permissions/usage-report-installer-cluster-policy.yaml"
        sed \
        -e "s/NAMESPACE/$USAGE_REPORT_OPERATOR_NAME/g" \
        -e "s/ROLE_NAME/$USAGE_REPORT_INSTALLER_ROLE_NAME/g" \
        "$INPUT_FILE" > "$OUTPUT_FILE"

        kubectl apply -f permissions/usage-report-installer-cluster-policy.yaml
        ```

    * Enable the access entry for the EKS cluster.

        ```sh
        aws eks update-cluster-config --name $EKS_CLUSTER_NAME --access-config authenticationMode=API_AND_CONFIG_MAP
        ```

        Note: If you receive an error message indicating Unsupported authentication mode update, no further action is necessary as the authentication mode has already been configured.        


### Install SageMaker HyperPod Usage Report Infrastructure using CloudFormation

> The following installation assume you are using the role USAGE_REPORT_INSTALLER_ROLE_NAME you specified above.

#### Retrieve the CloudFormation Template

You can find the CloudFormation template in the `/cloudformation` directory. The template provisions the following AWS resources:

* **Storage infrastructure**: An S3 bucket (`s3://$AWS_ACCOUNT-$AWS_REGION-$HYPERPOD_CLUSTER_ID-usage-report-<random string>`) to capture usage data, with associated IAM role allowing pods to write data to the bucket.
* **Query infrastructure**: An Athena database for querying and aggregating usage data.
* **Processing infrastructure**: An AWS Lambda function triggered daily by a CloudWatch Event rule to perform automated usage data aggregation and reporting.

#### Input Parameters to the CloudFormation Template

| Parameter                  | Required | Default Value                         | Notes                                                                                       |
|----------------------------|----------|---------------------------------------|---------------------------------------------------------------------------------------------|
| EKSClusterName             | Yes      | -                                     | Name of the EKS cluster                                                                     |
| HyperPodClusterId          | Yes      | -                                     | Id of the HyperPod cluster                                                                  |
| UsageReportInstallerRoleName        | Yes      | -                                     | Name of the IAM role for usage reporting installation                                                    |
| DataRententionDays         | No       | 180                                   | Data retention days for S3 Bucket                                                           |
| InstallPodIdentityAddon    | No       | "true"                                | Whether to install the Pod Identity Addon. Allowed values: "true", "false"                  |
| UsageReportOperatorNameSpace | No      | hyperpod-usage-report       | Kubernetes cluster namespace where usage report operator is installed                       |
| OperatorServiceAccount     | No       | hyperpod-usage-report | Service account used by usage report operator pod identity for permissions to access AWS resources |

#### Deploy the Stack

Run the following stack creation command:
```sh
cd sagemaker-hyperpod-usage-report
aws cloudformation create-stack \
--region $AWS_REGION \
--stack-name $USAGE_REPORT_OPERATOR_NAME \
--template-body file://cloudformation/usage-report.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters \
ParameterKey=EKSClusterName,ParameterValue=$EKS_CLUSTER_NAME \
ParameterKey=HyperPodClusterId,ParameterValue=$HYPERPOD_CLUSTER_ID \
ParameterKey=UsageReportOperatorNameSpace,ParameterValue=$USAGE_REPORT_OPERATOR_NAME \
ParameterKey=OperatorServiceAccount,ParameterValue=$USAGE_REPORT_OPERATOR_NAME \
ParameterKey=UsageReportInstallerRoleName,ParameterValue=$USAGE_REPORT_INSTALLER_ROLE_NAME
```

Verify the CloudFormation stack creation status:
```sh
aws cloudformation describe-stacks --stack-name $USAGE_REPORT_OPERATOR_NAME \
--region $AWS_REGION --query 'Stacks[0].StackStatus' --output text
```

#### CloudFormation Outputs
| Output Name       | Description                              |
|-------------------|------------------------------------------|
| DatabaseName      | Name of the created database             |
| UsageReportBucket | Name of the created S3 Bucket            |

#### Note
* If the CloudFormation stack status indicates a `ROLLBACK` state, you can investigate the failure reason by using the AWS CLI command below or by checking the AWS CloudFormation console directly:
  ```sh
  aws cloudformation describe-stack-events \
      --stack-name $USAGE_REPORT_OPERATOR_NAME \
      --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]'
  ```
* Ensure that the `eks-auth:AssumeRoleForPodIdentity` permission is included in the IAM execution role for the SageMaker HyperPod cluster.
* If the stack creation fails with the error `eks-pod-identity-agent already exists`, recreate the stack with the additional parameters `ParameterKey=InstallPodIdentityAddon,ParameterValue=false`:
  ```sh
  aws cloudformation create-stack \
  --region $AWS_REGION \
  --stack-name $USAGE_REPORT_OPERATOR_NAME \
  --template-body file://cloudformation/usage-report.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
  ParameterKey=EKSClusterName,ParameterValue=$EKS_CLUSTER_NAME \
  ParameterKey=HyperPodClusterId,ParameterValue=$HYPERPOD_CLUSTER_ID \
  ParameterKey=UsageReportInstallerRoleName,ParameterValue=$USAGE_REPORT_INSTALLER_ROLE_NAME \
  ParameterKey=UsageReportOperatorNameSpace,ParameterValue=$USAGE_REPORT_OPERATOR_NAME \
  ParameterKey=OperatorServiceAccount,ParameterValue=$USAGE_REPORT_OPERATOR_NAME \
  ParameterKey=InstallPodIdentityAddon,ParameterValue=false
  ```


### Install the SageMaker HyperPod Usage Report Kubernetes Operator using Helm

#### Overview
The `values.yaml` Helm chart in the `/helm_chart` directory configures the SageMaker HyperPod usage report Kubernetes operator, which provisions and manages the following cluster resources:
* **Namespace**: `hyperpod-usage-report` (default)
* **Service Account**: `hyperpod-usage-report` (default)
* **RBAC rules** granting the operator cluster-scoped permissions to:
  - Monitor cluster resources (clusterqueues, workloads, namespaces, pods)
  - Retrieve node-level metadata
  - Manage leader election (if there are multiple replicas of the operator) using Kubernetes leases
* **Kubernetes operator** collecting and storing usage report data in S3.

#### Configure the Helm Chart
You can configure the Helm chart by either updating the `values.yaml` file or by providing parameters directly during the `helm install` command. Any values passed as parameters during installation override the settings in the `values.yaml` file.

| Parameter             | Description                                                                                               | Default Value                             | Required | Notes                                                                                       |
|-----------------------|-----------------------------------------------------------------------------------------------------------|-------------------------------------------|----------|---------------------------------------------------------------------------------------------|
| replicaCount          | Number of operator replicas to run                                                                        | 2                                         | No       |                                                                                             |
| namespace             | Namespace where the operator will be installed                                                            | "hyperpod-usage-report"         | No       | Can be modified to deploy in a different namespace                                          |
| serviceAccount.name   | Name of the service account                                                                               | "hyperpod-usage-report" | No       | Can be modified if using custom naming                                                      |
| s3BucketName          | Name of the S3 bucket that was created from the cloudformation template                                   |                                           | Yes      | Operator will start storing the usage report data in this bucket.                           |
| clusterName           | Name of the EKS Cluster                                                                                   |                                           | Yes      |                                                                                             |
| region                | Specify the AWS region                                                                                    |                                           | Yes      | example: us-west-2                                                                          |


#### Install the Helm Chart
To install the Helm chart, run the following command:
```sh
cd helm_chart
# retrieve s3 bucket name
USAGE_REPORT_S3_BUCKET=$(aws cloudformation describe-stack-resources \
--stack-name $USAGE_REPORT_OPERATOR_NAME \
--query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId' \
--output text)

# verification
echo $USAGE_REPORT_S3_BUCKET

helm install $USAGE_REPORT_OPERATOR_NAME \
./SageMakerHyperPodUsageReportChart \
-n $USAGE_REPORT_OPERATOR_NAME \
--set region=$AWS_REGION \
--set serviceAccount.name=$USAGE_REPORT_OPERATOR_NAME \
--set clusterName=$HYPERPOD_CLUSTER_NAME \
--set s3BucketName=$USAGE_REPORT_S3_BUCKET
```

#### Verify the Operator Installation
Verify the operator installation:
```sh
kubectl get pods -n $USAGE_REPORT_OPERATOR_NAME
```
You can start submitting jobs to the cluster. Raw job usage data is stored in the S3 bucket path `$USAGE_REPORT_S3_BUCKET/raw/`.

**Notes**
- Before install the operator through helm chart, make sure the [HyperPod Usage Report cloudformation stack](hyperpod-usage-report-sagemaker-hyperpod-usage-report-696fkl4tl) is completed.
- A pre-existing namespace `$USAGE_REPORT_OPERATOR_NAME` is required to install the helm chart (check with `kubectl get namspaces`). If you don't have it yet, please refer to [prerequisite](https://github.com/awslabs/sagemaker-hyperpod-usage-report?tab=readme-ov-file#prerequisites) to create namespace.
- When uninstalling the `$USAGE_REPORT_OPERATOR_NAME` helm chart, the associated namespace is automatically deleted, which invalidates the RBAC permissions. You must restore the namespace-level RBAC configurations previously set in the cluster by re-running the steps in the prerequisites section.


## Generate Reports

### Overview
You can use the `run.py` script to extract and export usage metrics for your SageMaker HyperPod cluster.

### Install Required Dependencies
```sh
cd sagemaker-hyperpod-usage-report/report_generation
pip install -e .

# retrieve Athena database name
USAGE_REPORT_DATABASE=$(aws cloudformation describe-stack-resources \
--stack-name $USAGE_REPORT_OPERATOR_NAME \
--query 'StackResources[?ResourceType==`AWS::Glue::Database`].PhysicalResourceId' \
--output text)

DATABASE_WORKGROUP_NAME=$(aws cloudformation describe-stack-resources \
--stack-name $USAGE_REPORT_OPERATOR_NAME \
--query 'StackResources[?ResourceType==`AWS::Athena::WorkGroup`].PhysicalResourceId' \
--output text)

# verification
echo $USAGE_REPORT_DATABASE
echo $DATABASE_WORKGROUP_NAME
```

### Generate the Report

To generate a usage report and export it to a specified S3 bucket, provide the following parameters to the `run.py` Python script:

### Parameters for the run.py Script
| Parameter             | Description                             | Example Value  | Required |
|-----------------------|-----------------------------------------|----------------|----------|
| --start-date          | Beginning date for report data         | `2025-04-15`     | Yes      |
| --end-date            | Ending date for report data            |`2025-04-17`     | Yes      |
| --format              | Output format of the report            | `csv` or `pdf`     | Yes      |
| --database-name       | Name of the database to query          | `usage_report`   | Yes      |
| --database-workgroup-name       | Name of Athena's workgroup          | `usage_report_workgroup`   | Yes      |
| --type                | Type of report to generate             | `detailed` or `summary`        | Yes      |
| --output-report-location | Directory where report will be saved | `s3://bucket-name/path` | Yes      |
| --cluster-name        | Name of the HyperPod cluster           | `my-hyperpod-cluster` | Yes      |

**Note:** 
- Select a date range that falls within the previous 180 days from the current date (unless you customized the `DataRententionDays` when installing the CloudFormation stack).

- A good practice is to create a separate folder in your S3 bucket to serve as the destination for generated usage reports.

Use the following command to generate and export the report:
```sh
python run.py \
--start-date <Start date of the report, i.e. 2025-04-22> \
--end-date <End date of the report, i.e. 2025-04-22> \
--format <csv or pdf> \
--database-name $USAGE_REPORT_DATABASE \
--database-workgroup-name $DATABASE_WORKGROUP_NAME \
--type <detailed or summary> \
--output-report-location s3://$USAGE_REPORT_S3_BUCKET/<usage report output folder> \
--cluster-name $HYPERPOD_CLUSTER_NAME
```
**Note**
* Ensure that the S3 bucket specified in `--output-report-location` has the necessary permissions to accept the report files.
* The `cluster-name` should match the name of your SageMaker HyperPod cluster.
* You can find all original captured data in the `raw` directory of your S3 bucket `$USAGE_REPORT_S3_BUCKET/raw` or in the Athena console.</para>


### Output File Naming Convention
The output file follows the naming convention: `<report-type>-report-<start-date>-<end-date>.<format>`.

For example, a summary report for the dates April 15, 2025, to April 17, 2025, in CSV format will be named `summary-report-2025-04-15-2025-04-17.csv` and will be located in the specified output directory `--output-report-location` of your S3 bucket.


## Clean Up Resources

### Overview

When you no longer need your SageMaker HyperPod usage reporting infrastructure, follow these steps to clean up Kubernetes and AWS resources (in that order). Proper resource deletion helps prevent unnecessary costs.

### Delete the Kubernetes Resources
To uninstall the Helm chart, run the following command:
```sh
cd sagemaker-hyperpod-usage-report/helm_chart
helm uninstall $USAGE_REPORT_OPERATOR_NAME --namespace $USAGE_REPORT_OPERATOR_NAME
```

Ensure that you uninstalled the SageMaker HyperPod usage report Kubernetes operator:
```sh
kubectl get pods --namespace $USAGE_REPORT_OPERATOR_NAME
```

### Delete the AWS Resources
To delete the CloudFormation stack and the resources it created, run the following command:
```sh
aws cloudformation delete-stack --region $AWS_REGION --stack-name $USAGE_REPORT_OPERATOR_NAME
```

Ensure that the stack is properly deleted:
```sh
aws cloudformation describe-stacks --region $AWS_REGION --stack-name $USAGE_REPORT_OPERATOR_NAME \
--region $AWS_REGION --query 'Stacks[0].StackStatus' --output text
```

**Note:** To prevent accidental deletion, you should delete the S3 buckets created by the CloudFormation stack manually:
- `$USAGE_REPORT_S3_BUCKET`

## Local Development

### Run Unit Tests

To run the unit tests locally:
```bash
cd report_generation
pytest
```
This will execute all test cases in the test directory. The test suite includes unit tests for all major components of the usage report functionality.

## Troubleshooting

###  Empty Reports

If your generated usage reports are empty, follow these diagnostic steps to identify and resolve the issue.

### 1. Verify Data Capture in S3

Check if raw data files exist in your S3 bucket:
```bash
aws s3 ls s3://$USAGE_REPORT_S3_BUCKET/raw/
```
If no files are present, proceed to verify the infrastructure components below.

### 2. Validate CloudFormation Stack Status

Check the status of cloudformation stack
```bash
aws cloudformation describe-stacks \
    --stack-name $USAGE_REPORT_OPERATOR_NAME \
    --query 'Stacks[0].StackStatus' \
    --output text
```

If the stack status shows ROLLBACK_COMPLETE or any failure state, investigate the failure reason:
```bash
aws cloudformation describe-stack-events \
    --stack-name $USAGE_REPORT_OPERATOR_NAME \
    --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]'
```

#### Common failure scenarios:

* S3 bucket name conflicts
* Athena table conflicts

If the stack failed, clean up existing resources and redeploy the cloudformation by following this [section](https://github.com/awslabs/sagemaker-hyperpod-usage-report?tab=readme-ov-file#set-up-usage-reporting).

### 3. Verify Kubernetes Operator Status

Connect to the Kubernetes Cluster
```bash
aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME
```

Check if the operator pods are running
```bash
kubectl get pods -n $USAGE_REPORT_OPERATOR_NAME
```

For non-running pods, examine the pod status:
```bash
kubectl describe pod <pod-name> -n $USAGE_REPORT_OPERATOR_NAME
```

Review operator logs for error messages
```bash
kubectl logs <pod-name> -n $USAGE_REPORT_OPERATOR_NAME
```

#### Common operator issues:
* Resource constraints preventing pod scheduling.
* Network connectivity issues to AWS S3 service. 

If you encounter issues not covered above, please collect the above diagnostic information and create an [issue](https://github.com/awslabs/sagemaker-hyperpod-usage-report/issues).

## Attributions and Open Source Acknowledgments
 
See [./attributions](./attributions) for credits.

## Contribute

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

