import re

import langcodes
import regex


def default_need_translate(text):
    if not text.strip():
        return False

    if re.match(r"\{\$[a-zA-Z0-9_]*\}$", text):
        return False

    if regex.match(r"^[^\p{L}]+$", text):
        return False
    return bool(text)


def need_translate_zh(text):
    if not default_need_translate(text):
        return False

    # if only contains non-Chinese characters, and the length of continue A-Z and a-z is less than 2, return False
    if regex.search(r"\p{Han}", text) is None:
        all_chars = re.findall("[A-Za-z]+", text)
        if all_chars and max(map(len, all_chars)) < 2:
            return False

    return True


def need_translate_en(text):
    if not default_need_translate(text):
        return False
    # if only contains Numbers, Roman numerals, and Upper case letters, return False
    if not re.search(r"[^0-9A-Z]", text):
        return False
    return True


MAPPING = {
    "zh": need_translate_zh,
    "en": need_translate_en,
}


def get_need_translate_func(lang):
    """
    Get the function to determine whether the text needs to be translated.
    """
    matched = langcodes.closest_supported_match(lang, MAPPING.keys())
    if matched is None:
        return default_need_translate
    else:
        return MAPPING[matched]
