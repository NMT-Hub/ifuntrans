"""
Translate all in one.
"""
from typing import List

from ifuntrans.translators import GoogleTranslator


def translate(data: List[str], from_lang: str, to_lang: str, prompt="") -> List[str]:
    """
    Translate the given dataframe to the given languages.
    :param df: The dataframe to translate.
    :param to_langs: The languages to translate to.
    :return: The translated dataframe.
    """
    translator = GoogleTranslator(from_lang, to_lang)
    return translator.translate_batch(data)
