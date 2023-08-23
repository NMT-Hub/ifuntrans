import asyncio
import os
import re
import warnings
from itertools import chain
from typing import Dict, Iterable, List, Tuple

import guidance
import langcodes
import openai
import tiktoken

AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# set the default language model used to execute guidance programs
guidance.llm = guidance.llms.OpenAI(
    # "gpt-3.5-turbo",
    # api_key=OPENAI_API_KEY,
    "gpt-4",
    api_key=AZURE_OPENAI_API_KEY,
    api_type="azure",
    api_base=AZURE_OPENAI_ENDPOINT,
    api_version="2023-05-15",
    deployment_id=DEPLOYMENT_ID,
)


MAX_LENGTH = 500
# openai.api_key = os.environ["OPENAI_API_KEY"]

openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = "2023-05-15"

tokenizer = tiktoken.encoding_for_model("gpt-4")


def chunk(source: List[str], target: List[str]) -> Iterable[Tuple[List[str], List[str]]]:
    source_chunk = []
    target_chunk = []
    cur_len = 0
    for src, tgt in zip(source, target):
        len_src = len(tokenizer.encode(src))
        # len_tgt = len(tokenizer.encode(tgt))
        len_tgt = 0
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


CHATGPT_DOC_TRANSLATE_PROMPT = """
{instructions}
You will be provided with a sentence in {src_lang}, and your task is to translate it into {tgt_lang}.

1. Please output the translations in the same order as the input sentences (one translation per line).
2. Please do not add or remove any punctuation marks.
3. Please don't do any explaining.
"""


async def create_chat_completion(order: int, messages: List[Dict[str, str]]):
    chat_completion_resp = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo", messages=messages, timeout=60, deployment_id=DEPLOYMENT_ID, temperature=0.0
    )
    return order, chat_completion_resp


async def _chatgpt_translate(
    origin: List[str], target: List[str], src_lang: str, tgt_lang: str, instructions=""
) -> List[str]:
    src_lang_name = langcodes.get(src_lang).display_name()
    tgt_lang_name = langcodes.get(tgt_lang).display_name()

    tasks = []
    chunked = list(chunk(origin, target))
    for i, (src, tgt) in enumerate(chunked):
        query = ""
        for s, t in zip(src, tgt):
            # replace all blank with space
            s = re.sub(r"\s+", " ", s)
            query += s + "\n"

        system_prompt = CHATGPT_DOC_TRANSLATE_PROMPT.format(
            src_lang=src_lang_name, tgt_lang=tgt_lang_name, instructions=instructions
        )
        chat_completion_resp = create_chat_completion(
            order=i,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
        )
        tasks.append(chat_completion_resp)

    fixed = []
    for future in asyncio.as_completed(tasks):
        order, chat_completion_resp = await future
        response = chat_completion_resp.choices[0].message.content
        answer = response.strip().split("\n")

        src, tgt = chunked[order]
        
        # In case that there are multiple new lines in the source sentence
        translations = []
        cur = 0
        for s in src:
            num_new_lines = s.count("\n")
            translations.append("\n".join(answer[cur : cur + num_new_lines + 1]))
            cur += num_new_lines + 1

        if len(translations) != len(tgt):
            warnings.warn(
                f"ChatGPT Doc Translate failed. Please check the following sentences:\n"
                f"Source: {src}\n"
                f"Target: {tgt}\n"
                f"Answer: {translations}\n"
            )
            translations = tgt
        fixed.append((order, translations))

    fixed.sort(key=lambda x: x[0])
    fixed = list(chain.from_iterable([x[1] for x in fixed]))
    return fixed


async def batch_translate_texts(texts: List[str], source_language_code: str, target_language_codes: str) -> List[str]:
    mock_target = ["Openai 翻译失败"] * len(texts)
    return await _chatgpt_translate(texts, mock_target, source_language_code, target_language_codes)


async def translate_text(text, source_language_code, target_language_code):
    translatons = await batch_translate_texts([text], source_language_code, target_language_code)
    return translatons[0]
