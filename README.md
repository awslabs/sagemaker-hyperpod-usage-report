# HyperPod Cluster Usage Report

Usage reporting in SageMaker HyperPod EKS-orchestrated clusters provides visibility into compute resource consumption. The capability allows organizations to implement transparent cost attribution, allocating cluster costs to teams, projects, or departments **based on their actual usage**. By tracking metrics such as GPU/CPU hours, and Neuron Core utilization over time, usage reporting complements SageMaker HyperPod's [Task Governance](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance.html) functionality, ensuring fair cost attribution in shared multi-tenant clusters by: 
- Eliminating guesswork in cost allocation
- Directly linking expenses to measurable resource consumption
- Enforcing usage-based accountability in shared infrastructure environments



**Table of contents**

- [Set up Usage Reporting](#set-up-usage-reporting)
  - [Prerequisites](#prerequisites)
  - [Install Usage Report Infrastructure using CloudFormation](#install-usage-report-infrastructure-using-cloudformation)
  - [Install Usage Report Kubernetes Operator using Helm](#install-usage-report-kubernetes-operator-using-helm)
- [Generate Reports](#generate-reports)
- [Clean Up Resources](#clean-up-resources)
- [Local Development](#local-development) 
- [Attributions and Open Source Acknowledgments](#attributions-and-open-source-acknowledgments)
- [Contributing](#contributing)
- [License](#license)



## Set up Usage Reporting

### Overview

Usage reporting in SageMaker HyperPod requires deploying the SageMaker HyperPod usage report infrastructure using a CloudFormation stack and installing the SageMaker HyperPod usage report Kubernetes operator using a Helm chart.

To successfully deploy and use the SageMaker HyperPod usage report, you should meet the following prerequisites.

### Prerequisites

* Have a running EKS-orchestrated SageMaker HyperPod cluster (Kubernetes version >= 1.30) with the [Task Governance](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks-operate-console-ui-governance-setup.html) add-on.

* Have AWS CLI, kubectl, and Helm (package manager for Kubernetes - version >= 3.17.1) installed.

* A Python environment (version >= 3.10).

* Clone the GitHub repository sagemaker-hyperpod-usage-report.

    ```sh
    git clone https://github.com/awslabs/sagemaker-hyperpod-usage-report
    ```

* Attach the `usage-report-admin-policy.json` IAM policy to the IAM Admin role who performs AWS CLI and helm operations. This ensures Administrators have the required permissions to install and manage SageMaker HyperPod Usage report data capture.

    You can find the JSON file of this policy in `sagemaker-hyperpod-usage-report/permissions/usage-report-admin-policy.json`.


    To embed the inline policy in an existing role, use the following command:

    ```sh
    aws iam put-role-policy \
    --role-name <Your usage report admin role name> \
    --policy-name SageMakerHyperPodUsageReportPolicy \
    --policy-document file://permissions/usage-report-admin-policy.json
    ```

    To verify that the policy has been added correctly, run the following AWS CLI command:

    ```sh
    aws iam get-role-policy \
    --role-name <Your usage report admin role name> \
    --policy-name SageMakerHyperPodUsageReportPolicy
    ```

* Set the following local environment variables in your terminal:

    ```sh
    # Set up the environment variable
    export AWS_ACCOUNT=<account number>
    export AWS_REGION=<region>
    export HYPERPOD_CLUSTER_NAME=<hyperpod cluster name>
    export EKS_CLUSTER_NAME=<eks cluster name>
    export USAGE_REPORT_ROLE_NAME=<usage report IAM role name>
    export USAGE_REPORT_CFN_STACK_NAME=sagemaker-hyperpod-usage-report
    export HYPERPOD_CLUSTER_ID=$(aws sagemaker describe-cluster --cluster-name ml-cluster --region $AWS_REGION | jq -r '.ClusterArn | split("/")[-1]')

    aws configure set region $AWS_REGION
    ```
* Create a dedicated Kubernetes namespace for the usage report operator:

    In `sagemaker-hyperpod-usage-report`, run the following command: 

    ```sh
    kubectl apply -f permissions/usage-report-namespace.yaml
    ```

* Create custom RBAC permissions for deploying the HyperPod usage report Kubernetes operator helm chart on the cluster:

    * Run the aws eks update-kubeconfig command to update your local kube config file (located at ~/.kube/config) with the credentials and configuration needed to connect to your EKS cluster using the kubectl command.

        ```sh
        aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME
        ```

    * You can verify that you are connected to the EKS cluster by running this commands:

        ```sh
        kubectl config current-context 
        ```

        `arn:aws:eks:us-west-2:xxxxxxxxxxxx:cluster/hyperpod-eks-cluster`

    * In `sagemaker-hyperpod-usage-report`, run the following command to setup the RBAC permissions in your EKS cluster.

        ```sh
        kubectl apply -f permissions/usage-report-admin-cluster-policy.yaml
        ```

    * Enable the access entry for the EKS cluster.

        ```sh
        aws eks update-cluster-config --name $EKS_CLUSTER_NAME --access-config authenticationMode=API_AND_CONFIG_MAP
        ```

        Note: If you receive an error message indicating Unsupported authentication mode update, no further action is necessary as the authentication mode has already been configured.        


### Install SageMaker HyperPod Usage Report Infrastructure using CloudFormation

#### Retrieve the CloudFormation Template

You can find the CloudFormation template in the `/cloudformation` directory. The template provisions the following AWS resources:

* **Storage infrastructure**: An S3 bucket (`s3://$AWS_ACCOUNT-$AWS_REGION-$HYPERPOD_CLUSTER_ID-usage-report`) to capture usage data, with associated IAM role allowing pods to write data to the bucket.
* **Query infrastructure**: An Athena database for querying and aggregating usage data.
* **Processing infrastructure**: An AWS Lambda function triggered daily by a CloudWatch Event rule to perform automated usage data aggregation and reporting.

#### Input Parameters to the CloudFormation Template

| Parameter                  | Required | Default Value                         | Notes                                                                                       |
|----------------------------|----------|---------------------------------------|---------------------------------------------------------------------------------------------|
| EKSClusterName             | Yes      | -                                     | Name of the EKS cluster                                                                     |
| HyperPodClusterId          | Yes      | -                                     | Id of the HyperPod cluster                                                                  |
| UsageReportRoleName        | Yes      | -                                     | Name of the IAM role for usage reporting                                                    |
| AthenaDBName               | No       | usage_report                          | Name of S3 Athena database                                                                  |
| DataRententionDays         | No       | 180                                   | Data retention days for S3 Bucket                                                           |
| InstallPodIdentityAddon    | No       | "true"                                | Whether to install the Pod Identity Addon. Allowed values: "true", "false"                  |
| UsageReportOperatorNameSpace | No      | sagemaker-hyperpod-usage-report       | Kubernetes cluster namespace where usage report operator is installed                       |
| OperatorServiceAccount     | No       | sagemaker-hyperpod-usage-report-service-account | Service account used by usage report operator pod identity for permissions to access AWS resources |

#### Deploy the Stack

Run the following stack creation command:
```sh
cd sagemaker-hyperpod-usage-report
aws cloudformation create-stack \
--region $AWS_REGION \
--stack-name $USAGE_REPORT_CFN_STACK_NAME \
--template-body file://cloudformation/usage-report.yaml \
--capabilities CAPABILITY_NAMED_IAM \
--parameters \
ParameterKey=EKSClusterName,ParameterValue=$EKS_CLUSTER_NAME \
ParameterKey=HyperPodClusterId,ParameterValue=$HYPERPOD_CLUSTER_ID \
ParameterKey=UsageReportRoleName,ParameterValue=$USAGE_REPORT_ROLE_NAME
```

Verify the CloudFormation stack creation status:
```sh
aws cloudformation describe-stacks --stack-name $USAGE_REPORT_CFN_STACK_NAME \
--region $AWS_REGION --query 'Stacks[0].StackStatus' --output text
```

#### CloudFormation Outputs
| Output Name       | Description                              |
|-------------------|------------------------------------------|
| DatabaseName      | Name of the created database             |
| UsageReportBucket | Name of the created S3 Bucket            |
| AthenaRoleArn     | ARN of the IAM role for Athena           |

#### Note
* If the CloudFormation stack status indicates a `ROLLBACK` state, you can investigate the failure reason by using the AWS CLI command below or by checking the AWS CloudFormation console directly:
  ```sh
  aws cloudformation describe-stack-events \
      --stack-name $USAGE_REPORT_CFN_STACK_NAME \
      --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]'
  ```
* Ensure that the `eks-auth:AssumeRoleForPodIdentity` permission is included in the IAM execution role for the SageMaker HyperPod cluster.
* If the stack creation fails with the error `eks-pod-identity-agent already exists`, recreate the stack with the additional parameters `ParameterKey=InstallPodIdentityAddon,ParameterValue=false`:
  ```sh
  aws cloudformation create-stack \
  --region $AWS_REGION \
  --stack-name $USAGE_REPORT_CFN_STACK_NAME \
  --template-body file://cloudformation/usage-report.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
  ParameterKey=EKSClusterName,ParameterValue=$EKS_CLUSTER_NAME \
  ParameterKey=HyperPodClusterId,ParameterValue=$HYPERPOD_CLUSTER_ID \
  ParameterKey=UsageReportRoleName,ParameterValue=$USAGE_REPORT_ROLE_NAME \
  ParameterKey=InstallPodIdentityAddon,ParameterValue=false
  ```
* If you have previously created CloudFormation resources in the same region and account, and you encounter issues with your Athena tables, you may need to run the `MSCK REPAIR TABLE` command in the Athena query editor to repair the resources.


### Install the SageMaker HyperPod Usage Report Kubernetes Operator using Helm

#### Overview
The `values.yaml` Helm chart in the `/helm_chart` directory configures the SageMaker HyperPod usage report Kubernetes operator, which provisions and manages the following cluster resources:
* **Namespace**: `sagemaker-hyperpod-usage-report` (default)
* **Service Account**: `sagemaker-hyperpod-usage-report-service-account` (default)
* **RBAC rules** granting the operator cluster-scoped permissions to:
  - Monitor cluster resources (clusterqueues, workloads, namespaces, pods)
  - Retrieve node-level metadata
  - Manage leader election (if there are multiple replicas of the operator) using Kubernetes leases
* **Kubernetes operator** collecting and storing usage report data in S3.

#### Configure the Helm Chart
You can configure the Helm chart by either updating the `values.yaml` file or by providing parameters directly during the `helm install` command. Any values passed as parameters during installation override the settings in the `values.yaml` file.

| Parameter             | Description                                                                                               | Default Value                             | Required | Notes                                                                                       |
|-----------------------|-----------------------------------------------------------------------------------------------------------|-------------------------------------------|----------|---------------------------------------------------------------------------------------------|
| replicaCount          | Number of operator replicas to run                                                                        | 1                                         | No       |                                                                                             |
| namespace             | Namespace where the operator will be installed                                                            | "sagemaker-hyperpod-usage-report"         | No       | Can be modified to deploy in a different namespace                                          |
| serviceAccount.name   | Name of the service account                                                                               | "sagemaker-hyperpod-usage-report-service-account" | No       | Can be modified if using custom naming                                                      |
| s3BucketName          | Name of the S3 bucket that was created from the cloudformation template                                   |                                           | Yes      | Operator will start storing the usage report data in this bucket.                           |
| clusterName           | Name of the EKS Cluster                                                                                   |                                           | Yes      |                                                                                             |
| region                | Specify the AWS region                                                                                    |                                           | Yes      | example: us-west-2                                                                          |


#### Install the Helm Chart
To install the Helm chart, run the following command:
```sh
cd helm_chart
helm install sagemaker-hyperpod-usage-report \
./SageMakerHyperPodUsageReportChart \
--set region=$AWS_REGION \
--set clusterName=$HYPERPOD_CLUSTER_NAME \
--set s3BucketName=$AWS_ACCOUNT-$AWS_REGION-$HYPERPOD_CLUSTER_ID-usage-report
```

#### Verify the Operator Installation
Verify the operator installation:
```sh
kubectl logs -n sagemaker-hyperpod-usage-report \
$(kubectl get pods -n sagemaker-hyperpod-usage-report -o name \
| grep "^pod/sagemaker-hyperpod-usage-report-" | sed -n '2p')
```

**Important**

  When uninstalling the `sagemaker-hyperpod-usage-report` helm chart, the associated namespace is automatically deleted, which invalidates the RBAC permissions. You must restore the namespace-level RBAC configurations previously set in the cluster by re-running the steps in the prerequisites section.


## Generate Reports

### Overview
You can use the `run.py` script to extract and export usage metrics for your SageMaker HyperPod cluster.

### Install Required Dependencies
```sh
cd sagemaker-hyperpod-usage-report/report_generation
pip install -e .
```

### Generate the Report
To generate a usage report and export it to a specified S3 bucket, provide the following parameters to the `run.py` Python script:

### Parameters for the run.py Script
| Parameter             | Description                             | Example Value  | Required |
|-----------------------|-----------------------------------------|----------------|----------|
| --start-date          | Beginning date for report data         | 2025-04-15     | Yes      |
| --end-date            | Ending date for report data            | 2025-04-17     | Yes      |
| --format              | Output format of the report            | csv            | Yes      |
| --database-name       | Name of the database to query          | usage_report   | Yes      |
| --type                | Type of report to generate             | summary        | Yes      |
| --output-report-location | Directory where report will be saved | s3://bucket-name/path | Yes      |
| --cluster-name        | Name of the HyperPod cluster           | my-hyperpod-cluster | Yes      |

**Note:** Select a date range that falls within the previous 180 days from the current date (unless you customized the `DataRententionDays` when installing the CloudFormation stack).

Use the following command to generate and export the report:
```sh
python run.py \
--start-date <Start date of the report, i.e. 2025-04-22> \
--end-date <End date of the report, i.e. 2025-04-22> \
--format csv \
--database-name usage_report \
--type summary \
--output-report-location s3://$AWS_ACCOUNT-$AWS_REGION-$HYPERPOD_CLUSTER_ID-usage-report/<usage_report_output/> \
--cluster-name $HYPERPOD_CLUSTER_NAME
```

**Note:** A good practice is to create a separate folder in your S3 bucket to serve as the destination for generated usage reports.

### Output File Naming Convention
The output file follows the naming convention: `<report-type>-report-<start-date>-<end-date>.<format>`.

For example, a summary report for the dates April 15, 2025, to April 17, 2025, in CSV format will be named `summary-report-2025-04-15-2025-04-17.csv` and will be located in the specified output directory of your S3 bucket.

Here's an example command to generate a summary report in CSV format for the dates April 15, 2025, to April 17, 2025:
```sh
python run.py \ 
--start-date 2025-04-15 \ 
--end-date 2025-04-17 \ 
--format csv \ 
--database-name usage_report \ 
--type summary \ 
--output-report-location s3://$AWS_ACCOUNT-$AWS_REGION-$HYPERPOD_CLUSTER_ID-usage-report/<usage_report_output/> \
--cluster-name my-hyperpod-cluster
```

This creates a file named `summary-report-2025-04-15-2025-04-17.csv` in the S3 bucket specified by the `--output-report-location` parameter.

**Note**
* Ensure that the S3 bucket specified in `--output-report-location` has the necessary permissions to accept the report files.
* The `cluster-name` should match the name of your SageMaker HyperPod cluster.


## Clean Up Resources

### Overview

When you no longer need your SageMaker HyperPod usage reporting infrastructure, use these steps to clean up AWS and Kubernetes resources. Proper resource deletion helps prevent unnecessary costs.

### Delete the AWS Resources
To delete the CloudFormation stack and the resources it created, run the following command:
```sh
aws cloudformation delete-stack --region $AWS_REGION --stack-name $USAGE_REPORT_CFN_STACK_NAME
```

Ensure that the stack is properly deleted:
```sh
aws cloudformation describe-stacks --region $AWS_REGION --stack-name $USAGE_REPORT_CFN_STACK_NAME \
--region $AWS_REGION --query 'Stacks[0].StackStatus' --output text
```

**Note:** To prevent accidental deletion, you should delete the S3 buckets created by the CloudFormation stack manually:
- `$AWS_ACCOUNT-$AWS_REGION-$HYPERPOD_ID-usage-report`
- `aws-athena-query-results-$AWS_ACCOUNT-$AWS_REGION`

### Delete the Kubernetes Resources
To uninstall the Helm chart, run the following command:
```sh
cd sagemaker-hyperpod-usage-report/helm_chart
helm uninstall sagemaker-hyperpod-usage-report
```

Ensure that you uninstalled the SageMaker HyperPod usage report Kubernetes operator:
```sh
kubectl logs -n sagemaker-hyperpod-usage-report \
$(kubectl get pods -n sagemaker-hyperpod-usage-report -o name \
| grep "^pod/sagemaker-hyperpod-usage-report-" | head -n 1)
```

## Local Development

### Running Unit Tests

To run the unit tests locally:
```bash
pytest
```
This will execute all test cases in the test directory. The test suite includes unit tests for all major components of the usage report functionality.

## Attributions and Open Source Acknowledgments
 
See [./attributions](./attributions) for credits.

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

