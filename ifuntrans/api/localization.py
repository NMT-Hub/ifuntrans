import tempfile
from typing import Tuple

import httpx
import langcodes
import pandas as pd

from ifuntrans.lang_detection import single_detection
from ifuntrans.pe import hardcode_post_edit
from ifuntrans.translate import translate
from ifuntrans.utils import IFUN_CALLBACK_URL, S3_DEFAULT_BUCKET, S3Client, get_s3_key_from_id


def read_excel(file_path: str) -> Tuple[pd.DataFrame, str]:
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


async def translate_excel(file_path: str, saved_path: str, to_langs: str):
    df, from_lang = read_excel(file_path)
    ids = df.iloc[:, 0].tolist()
    source = df.iloc[:, 1].tolist()
    to_langs = to_langs.split(",")

    lang2translations = {}
    for lang in to_langs:
        language_name = langcodes.get(lang).language_name()
        territory_name = langcodes.get(lang).territory_name()
        if territory_name:
            language_name += f" ({territory_name})"
        translations = await translate(source, from_lang, lang)
        lang2translations[language_name] = hardcode_post_edit(source, translations, from_lang, lang)

    # save to excel
    writer = pd.ExcelWriter(saved_path, engine="xlsxwriter")
    df_final = df.copy()
    for language_name, translations in lang2translations.items():
        df_final[language_name] = translations
    df_final.to_excel(writer, sheet_name="Translation Summary", index=False)
    for language_name, translations in lang2translations.items():
        temp_df = df.copy()
        temp_df["Machine Translation"] = translations
        temp_df.to_excel(writer, sheet_name=language_name, index=False)
    writer.close()


async def callback(task_id: int, status: int, message: str) -> None:
    # status 1: success, 2: failed, 3: in progress
    async with httpx.AsyncClient() as client:
        response = await client.post(
            IFUN_CALLBACK_URL,
            json={
                "id": task_id,
                "status": status,
                "message": message,
                "translateTarget": get_s3_key_from_id(task_id),
            },
        )
        response.raise_for_status()


async def translate_s3_excel_task(task_id: str, file_name: str, to_langs: str):
    async with S3Client() as s3_client:
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as temp_file:
            try:
                await s3_client.download_file(S3_DEFAULT_BUCKET, file_name, temp_file.name)
                await callback(task_id, 3, "In progress...")

                # translate
                await translate_excel(temp_file.name, temp_file.name, to_langs)

                # upload file
                s3_file_key = get_s3_key_from_id(task_id)
                await s3_client.upload_file(temp_file.name, S3_DEFAULT_BUCKET, s3_file_key)

                await callback(task_id, 1, "Success")
            except Exception as e:
                await callback(task_id, 2, str(e))
                raise e
