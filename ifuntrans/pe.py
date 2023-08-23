import re
from typing import List

from ifuntrans.async_translators.google import translate_text


def varify_placeholders(src: str, tgt: str):
    re_num_placeholder = r"\{(\d+)\}"
    re_color_placeholder = r"\[color=#([0-9A-F]{6})\].*?\[/color\]"
    re_bold_placeholder = r"\[b\].*?\[/b\]"

    for regx in [re_num_placeholder, re_color_placeholder, re_bold_placeholder]:
        src_match = re.findall(regx, src)
        tgt_match = re.findall(regx, tgt)
        if len(src_match) != len(tgt_match):
            return False

    return True


def _normalize_placeholder(matched_obj: re.Match) -> str:
    """
    Normalize placeholder. Remove all blank.
    """
    return re.sub(r"\s+", "", matched_obj.group(0))


async def hardcode_post_edit(origin: List[str], target: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    """
    Hardcode post edit.
    """
    answer = []
    for src, tgt in zip(origin, target):
        # Normalize placeholders
        if not varify_placeholders(src, tgt):
            tgt = re.sub(r"\[/[\x20-\x7E]+?\]", _normalize_placeholder, tgt)
            tgt = re.sub(r"\[color[\x20-\x7E]+?\]", _normalize_placeholder, tgt)
            while re.search(r"[\[\]\{\}/]\s+[\[\]\{\}/]", tgt):
                tgt = re.sub(r"[\[\]\{\}/]\s+[\[\]\{\}/]", _normalize_placeholder, tgt)

        re_num_placeholder = r"\{(\d+)\}"
        re_color_placeholder = (
            r"(?P<colorprefix>\[color=#([0-9A-F]{6})\])(?P<colorcontent>.*?)(?P<colorsuffix>\[/color\])"
        )
        re_bold_placeholder = r"(?P<boldprefix>\[b\])(?P<boldcontent>.*?)(?P<boldsuffix>\[/b\])"
        spliter = re_color_placeholder + "|" + re_bold_placeholder

        if not varify_placeholders(src, tgt):
            tgt = ""

            start, end = 0, 0
            for seg in re.finditer(spliter, src):
                start, end = seg.span()
                if src[:start]:
                    tgt += await translate_text(src[:start], src_lang, tgt_lang)

                groups = seg.groupdict()

                if groups["colorprefix"]:
                    tgt += (
                        groups["colorprefix"]
                        + await translate_text(groups["colorcontent"], src_lang, tgt_lang)
                        + groups["colorsuffix"]
                    )
                elif groups["boldprefix"]:
                    tgt += (
                        groups["boldprefix"]
                        + await translate_text(groups["boldcontent"], src_lang, tgt_lang)
                        + groups["boldsuffix"]
                    )

            if src[end:]:
                tgt += await translate_text(src[end:], src_lang, tgt_lang)

        # Upper case First letter
        if tgt:  # In case of empty string
            tgt = tgt[0].upper() + tgt[1:]

        # Normalize Roman number
        tgt = re.sub(r"Ⅰ", "I", tgt)
        tgt = re.sub(r"Ⅱ", "II", tgt)
        tgt = re.sub(r"Ⅲ", "III", tgt)
        tgt = re.sub(r"Ⅳ", "IV", tgt)
        tgt = re.sub(r"Ⅴ", "V", tgt)
        tgt = re.sub(r"Ⅵ", "VI", tgt)
        tgt = re.sub(r"Ⅶ", "VII", tgt)
        tgt = re.sub(r"Ⅷ", "VIII", tgt)
        tgt = re.sub(r"Ⅸ", "IX", tgt)
        tgt = re.sub(r"Ⅹ", "X", tgt)
        tgt = re.sub(r"Ⅺ", "XI", tgt)
        tgt = re.sub(r"Ⅻ", "XII", tgt)
        answer.append(tgt)
    return answer
