
import boto3
import time

# -------- CONFIG (must match the setup script) --------
REGION = "us-east-2"
BUCKET_NAME = "my-json-trigger-bucket-10112025"
TABLE_NAME = "MyJsonTable"
LAMBDA_NAME = "S3ToDynamoLambda"
IAM_ROLE_NAME = "LambdaS3DynamoRole"
# ------------------------------------------------------

s3 = boto3.client("s3", region_name=REGION)
dynamodb = boto3.client("dynamodb", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)

print("\n🧹 Starting cleanup of AWS resources...")

# 1️⃣ Remove S3 bucket (including objects)
print(f"Deleting S3 bucket: {BUCKET_NAME}...")
try:
    # Remove notifications first
    s3.put_bucket_notification_configuration(
        Bucket=BUCKET_NAME,
        NotificationConfiguration={}
    )
    # List and delete all objects
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
    if "Contents" in objects:
        for obj in objects["Contents"]:
            s3.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])
            print(f"  Deleted object: {obj['Key']}")
    # Delete the bucket
    s3.delete_bucket(Bucket=BUCKET_NAME)
    print("✅ S3 bucket deleted.")
except Exception as e:
    print("⚠️ Error deleting bucket (may not exist):", e)

# 2️⃣ Delete Lambda function
print(f"Deleting Lambda function: {LAMBDA_NAME}...")
try:
    lambda_client.delete_function(FunctionName=LAMBDA_NAME)
    print("✅ Lambda function deleted.")
except Exception as e:
    print("⚠️ Error deleting Lambda:", e)

# 3️⃣ Delete DynamoDB table
print(f"Deleting DynamoDB table: {TABLE_NAME}...")
try:
    dynamodb.delete_table(TableName=TABLE_NAME)
    print("Waiting for table to be deleted...")
    waiter = dynamodb.get_waiter("table_not_exists")
    waiter.wait(TableName=TABLE_NAME)
    print("✅ DynamoDB table deleted.")
except Exception as e:
    print("⚠️ Error deleting DynamoDB table:", e)

# 4️⃣ Detach and delete IAM role
print(f"Deleting IAM role: {IAM_ROLE_NAME}...")
try:
    # Detach policies
    attached_policies = iam.list_attached_role_policies(RoleName=IAM_ROLE_NAME)
    for policy in attached_policies["AttachedPolicies"]:
        iam.detach_role_policy(
            RoleName=IAM_ROLE_NAME, PolicyArn=policy["PolicyArn"]
        )
        print(f"  Detached policy: {policy['PolicyArn']}")
    # Delete role
    time.sleep(3)
    iam.delete_role(RoleName=IAM_ROLE_NAME)
    print("✅ IAM role deleted.")
except Exception as e:
    print("⚠️ Error deleting IAM role:", e)

print("\n🎉 Cleanup complete! All created AWS resources have been removed.")

