"""
Translate all in one.
"""
from typing import List

import langcodes
from opencc import OpenCC

from ifuntrans.translators import GoogleTranslator

opencc_mapping = {
    "s2hk": OpenCC("s2hk.json"),
    "hk2s": OpenCC("hk2s.json"),
    "tw2sp": OpenCC("tw2sp.json"),
    "s2twp": OpenCC("s2twp.json"),
    "s2t": OpenCC("s2t.json"),
    "t2s": OpenCC("t2s.json"),
}


def opencc_convert(text, lang_from, lang_to):
    """
    Convert text from one Chinese format to another using opencc.

    Args:
        text (str): the text to be converted
        lang_from (langcodes.Language): the language of the text
        lang_to (langcodes.Language): the language to convert to

    Returns:
        str: the converted text
    """
    if (not lang_from.territory and not lang_from.script) or lang_from.script == "Hans":
        lang_from.territory = "CN"
    if (not lang_to.territory and not lang_to.script) or lang_to.script == "Hans":
        lang_to.territory = "CN"

    if lang_from.territory == "CN" and lang_to.territory in ("HK", "MO"):
        cccode = "s2hk"
    elif lang_from.territory in ("HK", "MO") and lang_to.territory == "CN":
        cccode = "hk2s"
    elif lang_from.territory == "TW" and lang_to.territory == "CN":
        cccode = "tw2sp"
    elif lang_from.territory == "CN" and lang_to.territory == "TW":
        cccode = "s2twp"
    elif lang_from.territory == "CN" and lang_to.script == "Hant":
        cccode = "s2t"
    elif lang_from.script == "Hant" and lang_to.territory == "CN":
        cccode = "t2s"
    else:
        return text

    result = opencc_mapping.get(cccode).convert(text)
    return result


def translate(texts: List[str], from_lang: str, to_lang: str) -> List[str]:
    """
    Translate the given dataframe to the given languages.
    :param texts: The texts to translate.
    :param to_langs: The languages to translate to.
    :return: The translated dataframe.
    """
    from_lang_code = langcodes.get(from_lang)
    to_lang_code = langcodes.get(to_lang)
    if from_lang_code.language == "zh" and to_lang_code.language == "zh":
        return [opencc_convert(text, from_lang_code, to_lang_code) for text in texts]

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
