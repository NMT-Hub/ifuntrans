import os
import re
from typing import List

import guidance
import langcodes

AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID"]


# set the default language model used to execute guidance programs
guidance.llm = guidance.llms.OpenAI(
    "gpt-4",
    api_key=AZURE_OPENAI_API_KEY,
    api_type="azure",
    api_base=AZURE_OPENAI_ENDPOINT,
    api_version="2023-05-15",
    deployment_id=DEPLOYMENT_ID,
)


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


def hardcode_post_edit(origin: List[str], target: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    """
    Hardcode post edit.
    """
    answer = []
    for src, tgt in zip(origin, target):
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
