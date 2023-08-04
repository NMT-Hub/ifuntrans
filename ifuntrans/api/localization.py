import functools
import os
from typing import List

import boto3
import pandas as pd
from fastapi import BackgroundTasks

from ifuntrans.api import IfunTransModel
from ifuntrans.translate import translate

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")


def read_excel(file_path: str) -> pd.DataFrame:
    """
    Read the given excel file.
    :param file_path: The path to the excel file.
    :return: The dataframe.
    """
    dataframe = pd.read_excel(file_path)

    # assert two columns
    assert dataframe.shape[1] == 2
    return dataframe


def translate_excel(file_path: str, to_langs: List):
    df = read_excel(file_path)

    lang2df = {}
    for lang in to_langs:
        lang2df[lang] = translate(df, lang)

    with pd.ExcelWriter(file_path) as writer:
        for lang, df in lang2df.items():
            df.to_excel(writer, sheet_name=lang)


@functools.cache
def get_s3_client() -> boto3.client:
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def upload_file(
    task_id: str, bucket_name: str, object_name: str, to_langs: List[str], background_tasks: BackgroundTasks
) -> IfunTransModel:
    # download file from s3
    s3_client = get_s3_client()
    s3_client.download_file(bucket_name, object_name, f"/tmp/{task_id}.zip")


class ProgressModel(IfunTransModel):
    task_id: str
    progress: float


def progress(task_id) -> ProgressModel:
    pass


class DownloadFileModel(IfunTransModel):
    task_id: str
    url: str
    expire_time: str


def download_file(task_id) -> DownloadFileModel:
    pass
