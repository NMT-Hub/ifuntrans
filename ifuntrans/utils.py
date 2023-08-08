import datetime
import os

import boto3

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
IFUN_CALLBACK_URL = os.environ.get("IFUN_CALLBACK_URL")
S3_DEFAULT_BUCKET = os.environ.get("S3_DEFAULT_BUCKET")


def get_s3_key_from_id(task_id: str) -> str:
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    return f"ai-translate/target/{date_str}/{task_id}.xlsx"


def get_s3_client():
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    return s3_client
