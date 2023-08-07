import os
import tempfile
from typing import List

import boto3
import langcodes
import pandas as pd
import requests
from fastapi import BackgroundTasks

from ifuntrans.api import IfunTransModel
from ifuntrans.translate import translate
from ifuntrans.translators.detection import single_detection

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
IFUN_CALLBACK_URL = os.environ.get("IFUN_CALLBACK_URL")
IFUN_DEFAULT_BUCKET = os.environ.get("IFUN_DEFAULT_BUCKET")


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


def get_s3_key_from_id(task_id: str) -> str:
    return f"{task_id}.xlsx"


def callback(task_id: str, status: int, message: str, file_name: str) -> None:
    # status 1: success, 2: failed, 3: in progress
    requests.post(
        IFUN_CALLBACK_URL,
        json={
            "id": task_id,
            "status": status,
            "message": message,
            "translateTarget": get_s3_key_from_id(task_id),
        },
    )



def translate_s3_excel_task(task_id: str, file_name: str, to_langs: List[str]):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    # download file
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as temp_file:
        try:
            s3_client.download_file(IFUN_DEFAULT_BUCKET, file_name, temp_file.name)
            callback(task_id, file_name, 3, "In progress...")

            # translate
            translate_excel(temp_file.name, temp_file.name, to_langs)

            # upload file
            s3_client.upload_file(temp_file.name, IFUN_DEFAULT_BUCKET)

            callback(task_id, 1, "Success")
        except Exception as e:
            callback(task_id, 2, str(e))
