import re

import langcodes


def default_need_translate(text):
    return bool(text)


def need_translate_zh(text):
    if not default_need_translate(text):
        return False
    # if contains no Chinese characters, return False
    if not re.search(r"[\u4e00-\u9fff]", text):
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
    # "zh": need_translate_zh,
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
