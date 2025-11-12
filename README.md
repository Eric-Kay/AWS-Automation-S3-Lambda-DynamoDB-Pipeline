

---

# ☁️ AWS Automation: S3 → Lambda → DynamoDB Pipeline

This repository contains a **Python automation script** that provisions a complete **AWS data ingestion pipeline**.
It automatically sets up all required resources so that **uploading a JSON file to S3** automatically **triggers a Lambda function**, which **parses and writes data into DynamoDB**.

---

## 🚀 Overview

The script automates the following:

1. **Creates an IAM Role** for Lambda with S3 and DynamoDB permissions.
2. **Creates an S3 Bucket** to store incoming JSON files.
3. **Creates a DynamoDB Table** to store parsed data.
4. **Creates a Lambda Function** that reads JSON from S3 and writes to DynamoDB.
5. **Configures S3 Event Notification** to trigger Lambda on file upload.
6. **Uploads a sample JSON file** to demonstrate the working setup.

---

## 🧩 AWS Services Used

| Service      | Purpose                                              |
| ------------ | ---------------------------------------------------- |
| **IAM**      | Creates and manages execution roles and permissions. |
| **S3**       | Stores JSON input files that trigger the Lambda.     |
| **Lambda**   | Executes code when files are uploaded to S3.         |
| **DynamoDB** | Stores parsed JSON records.                          |

---

## 🛠️ Prerequisites

Before running this script, ensure you have:

* **Python 3.8+** installed
* **boto3** installed

  ```bash
  pip install boto3
  ```
* **AWS CLI configured** with appropriate permissions:

  ```bash
  aws configure
  ```
* IAM credentials with permissions to create:

  * IAM roles and policies
  * S3 buckets
  * DynamoDB tables
  * Lambda functions

---

## ⚙️ Configuration

You can edit the top of the script to customize AWS resource names and region:

```python
# -------- CONFIG --------
REGION = "us-east-2"
BUCKET_NAME = "my-json-trigger-bucket-10112025"
TABLE_NAME = "MyJsonTable"
LAMBDA_NAME = "S3ToDynamoLambda"
IAM_ROLE_NAME = "LambdaS3DynamoRole"
# ------------------------
```

💡 **Tip:** S3 bucket names must be globally unique — update the bucket name before running.

---

## 🧠 How It Works

Here’s what happens under the hood:

1. **IAM Role Creation:**

   * Creates a role trusted by `lambda.amazonaws.com`.
   * Attaches AWS managed policies for Lambda execution, S3 read, and DynamoDB full access.

2. **S3 Bucket Creation:**

   * Creates a new S3 bucket to hold JSON files.
   * If the bucket exists, it is skipped gracefully.

3. **DynamoDB Table Creation:**

   * Creates a table with primary key `id` (string type).
   * Waits until the table is fully active.

4. **Lambda Function Creation:**

   * Packages Python code that:

     * Reads uploaded JSON from S3
     * Parses its contents
     * Inserts each record into DynamoDB
   * Deploys Lambda with environment variable `TABLE_NAME`.

5. **S3 → Lambda Trigger Configuration:**

   * Grants S3 permission to invoke the Lambda.
   * Adds event notification for `s3:ObjectCreated:*`.

6. **Sample JSON Upload:**

   * Generates and uploads a test file:

     ```json
     [
       {"id": "1", "name": "Alice", "age": "30"},
       {"id": "2", "name": "Bob", "age": "25"}
     ]
     ```
   * This triggers the Lambda and inserts data into DynamoDB.

---

## ▶️ How to Run

1. **Clone this repository:**

   ```bash
   git clone https://github.com/Eric-Kay/AWS-Automation-S3-Lambda-DynamoDB-Pipeline.git
   cd AWS-Automation-S3-Lambda-DynamoDB-Pipeline
   ```

2. **Run the script:**

   ```bash
   python serverless.py
   ```

3. **Wait for setup to complete.**
   Once done, you’ll see output like:

   ```
   ✅ COMPLETE SETUP!
   S3 Bucket: my-json-trigger-bucket-10112025
   DynamoDB Table: MyJsonTable
   Lambda Function: S3ToDynamoLambda
   IAM Role: LambdaS3DynamoRole
   ```

4. **Verify the results:**

   * Go to **AWS DynamoDB Console**
   * Open table **MyJsonTable**
   * You should see the JSON items inserted by Lambda 🎉

---

## 🧾 Example Output

```
Creating IAM Role: LambdaS3DynamoRole...
IAM Role created: arn:aws:iam::123456789012:role/LambdaS3DynamoRole
Creating S3 bucket: my-json-trigger-bucket-10112025...
Creating DynamoDB table: MyJsonTable...
Waiting for table to be active...
Creating Lambda function: S3ToDynamoLambda...
Configuring S3 trigger...
Uploading sample JSON to S3 (this will trigger Lambda)...

✅ COMPLETE SETUP!
S3 Bucket: my-json-trigger-bucket-10112025
DynamoDB Table: MyJsonTable
Lambda Function: S3ToDynamoLambda
IAM Role: LambdaS3DynamoRole
```

---

## 🧰 Clean-up Instructions

To remove all created resources:

1. Delete the **clean_up_serverless**:

   ```bash
   pytnon3 clean_up_serverless.py
   ```


## 🧩 Architecture Diagram (Conceptual)

```
          +----------------------+
          |      JSON File       |
          |     (uploaded to)    |
          |       S3 Bucket      |
          +----------+-----------+
                     |
          S3 Event: ObjectCreated
                     |
                     v
           +---------+----------+
           |      AWS Lambda     |
           | (Triggered Function)|
           +---------+-----------+
                     |
          Insert Records into DynamoDB
                     |
           +---------v----------+
           |   DynamoDB Table   |
           |   (Stores JSON)    |
           +--------------------+
```

---

## 📚 References

* [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
* [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
* [AWS DynamoDB Docs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
* [S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html)

---

## 👨‍💻 Author

**ERIC AVWORHO**
📧 [avworho.eric@gmail.com]


---


