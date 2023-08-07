"""
Translate all in one.
"""
from typing import List

import langcodes

from ifuntrans.translators import GoogleTranslator


def chatgpt_post_edit(texts: List[str], from_lang: str, to_lang: str, prompt="") -> List[str]:
    pass


def translate(texts: List[str], from_lang: str, to_lang: str) -> List[str]:
    """
    Translate the given dataframe to the given languages.
    :param texts: The texts to translate.
    :param to_langs: The languages to translate to.
    :return: The translated dataframe.
    """
    need_translate_mask = []
    if langcodes.closest_supported_match(from_lang, ["en"]) is not None:
        need_translate_mask = [True] * len(texts)

    else:
        # if only contains ascii characters and number of word is less than 2, then don't translate
        for text in texts:
            if text.isascii() and len(text.split()) <= 2:
                need_translate_mask.append(False)
            else:
                need_translate_mask.append(True)

    translator = GoogleTranslator(from_lang, to_lang)
    translation = translator.translate_batch(texts)

    translation = [t if need_translate_mask[i] else texts[i] for i, t in enumerate(translation)]
    return translation
