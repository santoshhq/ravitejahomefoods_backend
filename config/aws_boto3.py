import boto3
from dotenv import load_dotenv
import os
load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("YOUR_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("YOUR_SECRET_KEY"),
    region_name="us-east-1"
)
BUCKET_NAME = "weetshop-images"

