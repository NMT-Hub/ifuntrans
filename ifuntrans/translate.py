"""
Translate all in one.
"""
import re
from itertools import chain
from typing import List

import langcodes
from opencc import OpenCC

from ifuntrans.async_translators.chatgpt import batch_translate_texts
from ifuntrans.characters import get_need_translate_func
from ifuntrans.pe import post_edit

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


async def translate(texts: List[str], from_lang: str, to_lang: str, **kwargs) -> List[str]:
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

    splited_texts = [re.split(r"([\n\r]+)", text) for text in texts]
    splited_texts_len = [len(text) for text in splited_texts]
    texts = list(chain.from_iterable(splited_texts))

    need_translate_func = get_need_translate_func(from_lang)
    need_translate_mask = [need_translate_func(text) for text in texts]
    need_translate_texts = [t for t, m in zip(texts, need_translate_mask) if m]
    translation = await batch_translate_texts(need_translate_texts, from_lang, to_lang, **kwargs)
    translation = await post_edit(need_translate_texts, translation, from_lang, to_lang)

    result = []
    j = 0
    for i in range(len(texts)):
        if need_translate_mask[i]:
            result.append(translation[j])
            j += 1
        else:
            result.append(texts[i])

    # merge the splited texts
    final_result = []
    cur = 0
    for i in range(len(splited_texts)):
        final_result.append("".join(result[cur : cur + splited_texts_len[i]]))
        cur += splited_texts_len[i]

    return final_result
