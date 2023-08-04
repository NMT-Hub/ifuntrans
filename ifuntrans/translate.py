"""
Translate all in one.
"""
import pandas as pd


def translate(df: pd.DataFrame, to_lang: str) -> pd.DataFrame:
    """
    Translate the given dataframe to the given languages.
    :param df: The dataframe to translate.
    :param to_langs: The languages to translate to.
    :return: The translated dataframe.
    """
