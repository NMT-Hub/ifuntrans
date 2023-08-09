import os
from typing import List

import guidance

AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
DEPLOYMENT_ID=os.environ["DEPLOYMENT_ID"]


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
现在我要对这个游戏中的文本进行翻译，现在我通过google翻译得到了机翻译文，但是该译文不太完美，请根据我的要对该译文进行修改，使其更加完美。
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
{{gen 'answer' temperature=0 max_tokens=500}}
{{~/assistant}}
"""


def chatgpt_post_edit(origin: List[str], target: List[str], instructions="") -> List[str]:
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
        query=query,
    )
    import ipdb
    ipdb.set_trace()

    return result
