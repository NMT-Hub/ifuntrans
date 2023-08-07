import functools
import os
from typing import List

import boto3
import langcodes
import pandas as pd
from fastapi import BackgroundTasks

from ifuntrans.api import IfunTransModel
from ifuntrans.translate import translate
from ifuntrans.translators.detection import single_detection

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

    # skip first two rows
    dataframe = dataframe.iloc[2:]

    # random select 5 rows to detect language
    sample = dataframe.sample(5)
    lang = single_detection(" ".join(sample.iloc[:, 1].tolist()))

    # change column name
    dataframe.columns = ["ID", langcodes.get(lang).language_name()]

    return dataframe, lang


def translate_excel(file_path: str, saved_path: str, to_langs: List[str]):
    df, from_lang = read_excel(file_path)

    lang2df = {}
    for lang in to_langs.split(","):
        language_name = langcodes.get(lang).language_name()
        territory_name = langcodes.get(lang).territory_name()
        if territory_name:
            language_name += f" ({territory_name})"
        lang2df[language_name] = translate(df.iloc[:, 1].tolist(), from_lang, lang)

    for language_name, translations in lang2df.items():
        df[language_name] = translations

    # save to excel
    writer = pd.ExcelWriter(saved_path, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="Translation Summary", index=False)

    writer.save()


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
