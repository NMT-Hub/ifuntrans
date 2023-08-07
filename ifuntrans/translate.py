"""
Translate all in one.
"""
import langcodes
import pandas as pd

from ifuntrans.translators import GoogleTranslator


def translate(data, to_lang: str) -> pd.DataFrame:
    """
    Translate the given dataframe to the given languages.
    :param df: The dataframe to translate.
    :param to_langs: The languages to translate to.
    :return: The translated dataframe.
    """
    translator = GoogleTranslator(to_lang)
    language_name = langcodes.get(to_lang).language_name()
    df[language_name] = df.iloc[:, 1].apply(translator.translate)
    return df
