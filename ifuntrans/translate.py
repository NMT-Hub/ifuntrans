"""
Translate all in one.
"""
from typing import List
from unittest.mock import DEFAULT

import langcodes
from opencc import OpenCC

from ifuntrans.translators import GoogleTranslator

DEFAULT_PROMPT = """
现在我要对一个游戏中的文本进行翻译，现在我通过google翻译得到了机翻译文，但是该译文不太完美，请根据我的要对该译文进行修改，使其更加完美。
1.中文句式一致的，其他语言麻烦尽量保持翻译句式一致。
2.大小写问题，建筑，工具，按键，名字等等需要首字母大写（针对有字母的语言）
3.句子首字母保持大写
4.罗马数字写法统一，比如不要Ⅱ和II都用，直接用Ⅱ
5.如果有特殊符号，需要保留原格式，不能改变字符或者添加空格。如`{0}`，`[color=#FFFFFF]`
6.特殊翻译最好使用缩写，比如攻击力ATK，防御力DEF，生命HP，经验EXP

修改结果请以json格式提交，格式如下：
```
[
    "修改后译文1"
    "修改后译文2"
]
```
"""

def chatgpt_post_edit(texts: List[str], from_lang: str, to_lang: str, prompt="") -> List[str]:
    pass


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
