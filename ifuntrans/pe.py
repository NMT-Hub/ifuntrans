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


FIX_PLACEHOLDER_GUIDANCE = """
{{#system~}}
{{instructions}}
现在我要对这个游戏中的文本进行翻译，翻译方向为由{{src_lang}}到{{tgt_lang}}现在我通过google翻译得到了机翻译文，但是该译文不太完美。

在游戏资源文件或其他类型的格式化文本中，这些特殊的标记（如 [b], [color], [/color], [/b] 以及 {0}, {1}）通常被称为“标签”或“格式标记”。

[b] 和 [/b] 通常代表文本的开始和结束加粗。
[color=#df9300] 和 [/color] 是用于指定文本颜色的标签，其中 #df9300 是一个特定的颜色编码。
{0} 和 {1} 是占位符，它们通常在字符串格式化中使用，代表在运行时会被相应的值替换。

译文中的特殊符号，并没有保留原格式，请帮我修复它，并直接输出修改后的{{tgt_lang}}译文，不要做出过多的解释。
{{~/system}}

{{#user~}}
{{query}}
{{~/user}}

{{#assistant~}}
{{gen 'answer' temperature=0}}
{{~/assistant}}
"""


def chatgpt_fix_placeholder(
    origin: List[str], target: List[str], src_lang: str, tgt_lang: str, instructions=""
) -> List[str]:
    src_lang = langcodes.get(src_lang).display_name()
    tgt_lang = langcodes.get(tgt_lang).display_name()

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

        guide = guidance(FIX_PLACEHOLDER_GUIDANCE)
        result = guide(
            instructions=instructions,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
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


GUIDANCE = """
{{#system~}}
{{instructions}}
现在我要对这个游戏中的文本进行翻译，翻译方向为由{{src_lang}}到{{tgt_lang}}现在我通过google翻译得到了机翻译文，但是该译文不太完美，请根据我的要对该译文进行修改，使其更加完美。
1.中文句式一致的，其他语言麻烦尽量保持翻译句式一致。
2.大小写问题，建筑，工具，按键，名字等等需要首字母大写（针对有字母的语言）
3.句子首字母保持大写
4.罗马数字写法统一，比如不要Ⅱ和II都用，直接用Ⅱ
5.如果有特殊符号，需要保留原格式，不能改变字符或者添加空格。如`{0}`，`[color=#FFFFFF]`
6.特殊翻译最好使用缩写，比如攻击力ATK，防御力DEF，生命HP，经验EXP
{{~/system}}

{{#user~}}
{{query}}
请输出修改后的译文结果
{{~/user}}

{{#assistant~}}
{{gen 'answer' temperature=0}}
{{~/assistant}}
"""


def chatgpt_post_edit(origin: List[str], target: List[str], src_lang: str, tgt_lang: str, instructions="") -> List[str]:
    """
    Post edit with chatgpt.
    """
    template = GUIDANCE

    query = ""
    for i, (src, tgt) in enumerate(zip(origin, target)):
        query += "\t".join([src, tgt]) + "\n"

    guide = guidance(template)
    result = guide(
        instructions=instructions,
        src_lang=langcodes.get(src_lang).display_name(),
        tgt_lang=langcodes.get(tgt_lang).display_name(),
        query=query,
    )

    answer = result.get("answer", "").split("\n")
    if len(answer) != len(origin):
        return target
    else:
        return answer


def normalize_placeholder(matched_obj: re.Match) -> str:
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
            tgt = re.sub(r"\[/[\x20-\x7E]+?\]", normalize_placeholder, tgt)
            tgt = re.sub(r"\[color[\x20-\x7E]+?\]", normalize_placeholder, tgt)
            while re.search(r"[\[\]\{\}/]\s+[\[\]\{\}/]", tgt):
                tgt = re.sub(r"[\[\]\{\}/]\s+[\[\]\{\}/]", normalize_placeholder, tgt)

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
