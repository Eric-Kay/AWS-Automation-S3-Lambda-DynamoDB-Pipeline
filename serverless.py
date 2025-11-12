import boto3
import json
import zipfile
import io
import time
import os

# -------- CONFIG --------
REGION = "us-east-2"
BUCKET_NAME = "my-json-trigger-bucket-10112025"
TABLE_NAME = "MyJsonTable"
LAMBDA_NAME = "S3ToDynamoLambda"
IAM_ROLE_NAME = "LambdaS3DynamoRole"
# ------------------------

iam = boto3.client("iam", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
dynamodb = boto3.client("dynamodb", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

# 1️⃣ Create IAM Role for Lambda
print(f"Creating IAM Role: {IAM_ROLE_NAME}...")
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}

try:
    role = iam.create_role(
        RoleName=IAM_ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy),
        Description="Role for Lambda with S3 and DynamoDB access"
    )
    role_arn = role["Role"]["Arn"]
    print(f"IAM Role created: {role_arn}")

    print("Attaching policies to role...")
    iam.attach_role_policy(
        RoleName=IAM_ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    )
    iam.attach_role_policy(
        RoleName=IAM_ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    )
    iam.attach_role_policy(
        RoleName=IAM_ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
    )

    # Wait for role propagation
    print("Waiting for IAM role to become active...")
    time.sleep(15)
except iam.exceptions.EntityAlreadyExistsException:
    print("IAM Role already exists, fetching ARN...")
    role_arn = iam.get_role(RoleName=IAM_ROLE_NAME)["Role"]["Arn"]

# 2️⃣ Create S3 bucket
print(f"Creating S3 bucket: {BUCKET_NAME}...")
try:
    s3.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={'LocationConstraint': REGION}
    )
except s3.exceptions.BucketAlreadyOwnedByYou:
    print("Bucket already exists, skipping.")
except Exception as e:
    print("Error creating bucket:", e)

# 3️⃣ Create DynamoDB table
print(f"Creating DynamoDB table: {TABLE_NAME}...")
try:
    dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    print("Waiting for table to be active...")
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=TABLE_NAME)
except dynamodb.exceptions.ResourceInUseException:
    print("Table already exists, skipping.")

# 4️⃣ Create Lambda function code
lambda_code = '''
import json
import boto3
import os

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

def lambda_handler(event, context):
    table_name = os.environ["TABLE_NAME"]
    table = dynamodb.Table(table_name)
    
    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    
    response = s3.get_object(Bucket=bucket, Key=key)
    file_content = response["Body"].read().decode("utf-8")
    data = json.loads(file_content)
    
    if isinstance(data, list):
        for item in data:
            table.put_item(Item=item)
    else:
        table.put_item(Item=data)
    
    return {"status": "success", "inserted": len(data) if isinstance(data, list) else 1}
'''

# Package Lambda code as zip in memory
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w') as z:
    z.writestr("lambda_function.py", lambda_code)
zip_buffer.seek(0)

# 5️⃣ Create Lambda function
print(f"Creating Lambda function: {LAMBDA_NAME}...")
try:
    lambda_client.create_function(
        FunctionName=LAMBDA_NAME,
        Runtime="python3.12",
        Role=role_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": zip_buffer.read()},
        Environment={'Variables': {'TABLE_NAME': TABLE_NAME}},
        Timeout=30,
    )
except lambda_client.exceptions.ResourceConflictException:
    print("Lambda function already exists, skipping.")
except Exception as e:
    print("Error creating Lambda:", e)

time.sleep(5)

# 6️⃣ Configure S3 trigger for Lambda
print("Configuring S3 trigger...")
lambda_arn = lambda_client.get_function(FunctionName=LAMBDA_NAME)['Configuration']['FunctionArn']

# Add permission so S3 can invoke Lambda
try:
    lambda_client.add_permission(
        FunctionName=LAMBDA_NAME,
        StatementId='S3InvokePermission',
        Action='lambda:InvokeFunction',
        Principal='s3.amazonaws.com',
        SourceArn=f"arn:aws:s3:::{BUCKET_NAME}"
    )
except Exception as e:
    if "already exists" in str(e):
        print("Permission already added.")
    else:
        print("Error adding permission:", e)

# Set event notification
s3.put_bucket_notification_configuration(
    Bucket=BUCKET_NAME,
    NotificationConfiguration={
        'LambdaFunctionConfigurations': [
            {
                'LambdaFunctionArn': lambda_arn,
                'Events': ['s3:ObjectCreated:*']
            }
        ]
    }
)

# 7️⃣ Upload JSON file to trigger Lambda
sample_data = [
    {"id": "1", "name": "Alice", "age": "30"},
    {"id": "2", "name": "Bob", "age": "25"}
]
file_name = "sample_data.json"
with open(file_name, "w") as f:
    json.dump(sample_data, f)

print("Uploading sample JSON to S3 (this will trigger Lambda)...")
s3.upload_file(file_name, BUCKET_NAME, file_name)

print("\n✅ COMPLETE SETUP!")
print(f"S3 Bucket: {BUCKET_NAME}")
print(f"DynamoDB Table: {TABLE_NAME}")
print(f"Lambda Function: {LAMBDA_NAME}")
print(f"IAM Role: {IAM_ROLE_NAME}")
print("\nCheck your DynamoDB table after a minute to see inserted data.")

