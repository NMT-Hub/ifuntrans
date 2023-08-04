import os
from os import environ as env

import boto3


class S3:
    def __init__(self):
        self.aws_access_key_id = env.get("AWS_ACCESS_KEY")
        self.aws_secret_access_key = env.get("AWS_SECRET_ACCESS_KEY")
        self.s3 = self.conn_s3()

    # 获取S3连接
    def conn_s3(self, region=None):
        if region is None:
            s3 = boto3.client(
                service_name="s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
            )
        else:
            s3 = boto3.client(
                service_name="s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=region,
            )
        return s3

    # 查看所有bucket中对象
    def list_bucket_keys(self, bucket_name):
        result = self.s3.list_objects(Bucket=bucket_name).get("Contents")
        obj_lis = []
        for _ in result:
            obj_lis.append(_.get("Key"))
            print(_.get("Key"))
        return obj_lis

    # 创建bucket
    def create_bucket(self, bucket_name):
        # Create bucket
        if region is None:
            self.s3.create_bucket(Bucket=bucket_name)
        else:
            s3_other = boto3.client(
                service_name="s3",
                aws_access_key_id="AKIAYDFF4KH5MGBIZ6ON",
                aws_secret_access_key="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",
                region_name=region,
            )
            location = {"LocationConstraint": region}
            s3_other.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)

    # 上传文件
    def upload_file(self, s3, file_name, bucket, object_name=None):
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            # 将上传文件的名字赋予上传后的对象名
            object_name = os.path.basename(file_name)

        # Upload the file
        s3.upload_file(file_name, Bucket=bucket, Key=object_name)

    # 下载文件
    def download_file(self, s3, bucket_name, file_name, local_file, file):
        result = s3.download_file(bucket_name, file_name, local_file + file)
        return result

    # 创建临时访问s3对象的连接
    def create_presigned_url(self, s3, bucket_name, object_name, expiration=3600):
        # Generate a presigned URL for the S3 object
        response = s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": object_name}, ExpiresIn=expiration
        )
        return response

    # 将s3调用方法的结果对外生成访问连接
    def create_presigned_url_expanded(
        self, s3, client_method_name, method_parameters=None, expiration=3600, http_method="GET"
    ):
        response = s3.generate_presigned_url(
            ClientMethod=client_method_name, Params=method_parameters, ExpiresIn=expiration, HttpMethod=http_method
        )
        return response

    # 将上传s3的方法封装在post中，可以通过post往s3中上传数据。此外，也可以采用HTML方式上传
    def create_presigned_post(self, s3, bucket_name, object_name, fields=None, conditions=None, expiration=3600):
        response = s3.generate_presigned_post(
            bucket_name, object_name, Fields=fields, Conditions=conditions, ExpiresIn=expiration
        )
        return response

    # 获取bucket安全策略
    def get_bucket_policy(self, s3, bucket):
        result = s3.get_bucket_policy(Bucket=bucket)
        return result["Policy"]

    # 定义bucket安全策略
    def put_bucket_policy(self, s3, bucket, policy):
        s3.put_bucket_policy(Bucket=bucket, Policy=policy)
