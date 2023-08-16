import os
import re
from typing import Iterable, List, Tuple

import guidance
import langcodes
import tiktoken

from ifuntrans.translators import translate

AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID"]

MAX_LENGTH = 500

tokenizer = tiktoken.get_encoding("cl100k_base")


# set the default language model used to execute guidance programs
guidance.llm = guidance.llms.OpenAI(
    "gpt-4",
    api_key=AZURE_OPENAI_API_KEY,
    api_type="azure",
    api_base=AZURE_OPENAI_ENDPOINT,
    api_version="2023-05-15",
    deployment_id=DEPLOYMENT_ID,
)


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


def chunk_by_max_length(source: List[str], target: List[str]) -> Iterable[Tuple[List[str], List[str]]]:
    source_chunk = []
    target_chunk = []
    cur_len = 0
    for src, tgt in zip(source, target):
        len_src = len(tokenizer.encode(src))
        len_tgt = len(tokenizer.encode(tgt))
        if len_src + len_tgt + cur_len > MAX_LENGTH:
            yield source_chunk, target_chunk
            source_chunk = []
            target_chunk = []
            cur_len = 0
        source_chunk.append(src)
        target_chunk.append(tgt)
        cur_len += len_src + len_tgt

    if source_chunk:
        yield source_chunk, target_chunk


CHATGPT_DOC_TRANSLATE_GUIDANCE = """
{{#system~}}
You will be provided with a sentence in {{src_lang}}, and your task is to translate it into {{tgt_lang}}.

1. Please output the translations in the same order as the input sentences (one translation per line).
2. Please do not add or remove any punctuation marks.
3. Please don't do any explaining.
{{~/system}}

{{#user~}}
{{query}}
{{~/user}}

{{#assistant~}}
{{gen 'answer' temperature=0}}
{{~/assistant}}
"""


def chatgpt_doc_translate(
    origin: List[str], target: List[str], src_lang: str, tgt_lang: str, instructions=""
) -> List[str]:
    src_lang_name = langcodes.get(src_lang).display_name()
    tgt_lang_name = langcodes.get(tgt_lang).display_name()

    # filter out the sentence pair that has different number of placeholders
    mask = [varify_placeholders(s, t) for s, t in zip(origin, target)]
    filtered = [(s, t) for m, s, t in zip(mask, origin, target) if not m]
    if not filtered:
        return target
    target_backup = target
    origin, target = zip(*filtered)

    fixed = []

    for src, tgt in chunk_by_max_length(origin, target):
        query = ""
        for i, (s, t) in enumerate(zip(src, tgt)):
            # replace all blank with space
            s = re.sub(r"\s+", " ", s)
            t = re.sub(r"\s+", " ", t)
            query += "\t".join([s, t]) + "\n"

        guide = guidance(CHATGPT_DOC_TRANSLATE_GUIDANCE)
        result = guide(
            instructions=instructions,
            src_lang=src_lang_name,
            tgt_lang=tgt_lang_name,
            query=query,
        )
        answer = result.get("answer", "").split("\n")
        if len(answer) != len(origin):
            fixed.extend(tgt)
        else:
            fixed.extend(answer)

    all_result = []
    i = 0
    for m, t in zip(mask, target_backup):
        if not m:
            all_result.append(fixed[i])
            i += 1
        else:
            all_result.append(t)

    return all_result


def _normalize_placeholder(matched_obj: re.Match) -> str:
    """
    Normalize placeholder. Remove all blank.
    """
    return re.sub(r"\s+", "", matched_obj.group(0))


def hardcode_post_edit(origin: List[str], target: List[str], src_lang: str, tgt_lang: str) -> List[str]:
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

            for seg in re.finditer(spliter, src):
                start, end = seg.span()
                if src[:start]:
                    tgt += translate(src[:start], src_lang, tgt_lang)

                groups = seg.groupdict()

                if groups["colorprefix"]:
                    tgt += (
                        groups["colorprefix"]
                        + translate(groups["colorcontent"], src_lang, tgt_lang)
                        + groups["colorsuffix"]
                    )
                elif groups["boldprefix"]:
                    tgt += (
                        groups["boldprefix"]
                        + translate(groups["boldcontent"], src_lang, tgt_lang)
                        + groups["boldsuffix"]
                    )

            if src[end:]:
                tgt += translate(src[end:], src_lang, tgt_lang)

        # Upper case First letter
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
