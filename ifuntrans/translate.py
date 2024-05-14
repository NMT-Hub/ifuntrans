"""
Translate all in one.
"""
import os
from itertools import chain
from typing import Iterable, List

import langcodes
from opencc import OpenCC

import ifuntrans.async_translators.chatgpt as chatgpt
import ifuntrans.async_translators.google as google
from ifuntrans.characters import get_need_translate_func
from ifuntrans.pe import post_edit
from ifuntrans.placeholder import split_text

opencc_mapping = {
    "s2hk": OpenCC("s2hk.json"),
    "hk2s": OpenCC("hk2s.json"),
    "tw2sp": OpenCC("tw2sp.json"),
    "s2twp": OpenCC("s2twp.json"),
    "s2t": OpenCC("s2t.json"),
    "t2s": OpenCC("t2s.json"),
}

ENGEIN = os.environ.get("IFUNTRANS_ENGINE", "chatgpt")

if ENGEIN == "chatgpt":
    batch_translate_texts = chatgpt.batch_translate_texts
elif ENGEIN == "google":
    batch_translate_texts = google.batch_translate_texts
else:
    raise ValueError(f"Unknown engine {ENGEIN}")


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


async def translate(texts: Iterable[str], from_lang: str, to_lang: str, **kwargs) -> List[str]:
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

    # split the texts by '\n'. In case of '\\n', replace it with '\n' first
    splited_texts = [split_text(text) for text in texts]
    splited_texts_len = [len(text) for text in splited_texts]
    texts = [text for text in chain.from_iterable(splited_texts)]

    need_translate_func = get_need_translate_func(from_lang)
    need_translate_mask = [need_translate_func(text) for text in texts]
    need_translate_texts = [t for t, m in zip(texts, need_translate_mask) if m]
    translation = await batch_translate_texts(need_translate_texts, from_lang, to_lang, **kwargs)
    # TODO: Temporarily disabled post-editing, because it's error-prone
    # translation = await post_edit(need_translate_texts, translation, from_lang, to_lang)

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
        final_result.append("".join(result[cur : cur + splited_texts_len[i]]).strip())
        cur += splited_texts_len[i]

    return final_result
