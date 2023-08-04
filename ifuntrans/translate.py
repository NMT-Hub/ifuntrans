"""
Translate all in one.
"""
from typing import List

import pandas as pd


def read_excel(file_path: str) -> pd.DataFrame:
    """
    Read the given excel file.
    :param file_path: The path to the excel file.
    :return: The dataframe.
    """
    df = pd.read_excel(file_path)

    # assert two columns
    assert df.shape[1] == 2


def translate_excel(file_path: str, to_langs: List):
    df = read_excel(file_path)

    lang2df = {}
    for lang in to_langs:
        lang2df[lang] = translate(df, lang)

    with pd.ExcelWriter(file_path) as writer:
        for lang, df in lang2df.items():
            df.to_excel(writer, sheet_name=lang)


def translate(df: pd.DataFrame, to_lang: str) -> pd.DataFrame:
    """
    Translate the given dataframe to the given languages.
    :param df: The dataframe to translate.
    :param to_langs: The languages to translate to.
    :return: The translated dataframe.
    """
