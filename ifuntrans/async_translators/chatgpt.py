import asyncio
import os
import re
import warnings
from itertools import chain
from typing import Dict, Iterable, List, Tuple

import langcodes
import openai
from tenacity import retry, stop_after_attempt, wait_fixed

from ifuntrans.async_translators.google import batch_translate_texts as google_batch_translate_texts
from ifuntrans.tm import search_tm
from ifuntrans.tokenizer import tokenizer

AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# set the default language model used to execute guidance programs
# guidance.llm = guidance.llms.OpenAI(
#     # "gpt-3.5-turbo",
#     # api_key=OPENAI_API_KEY,
#     "gpt-4",
#     api_key=AZURE_OPENAI_API_KEY,
#     api_type="azure",
#     api_base=AZURE_OPENAI_ENDPOINT,
#     api_version="2023-05-15",
#     deployment_id=DEPLOYMENT_ID,
# )


MAX_LENGTH = 500
# openai.api_key = os.environ["OPENAI_API_KEY"]

openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = "2023-05-15"


def chunk(source: List[str], target: List[str], max_length=MAX_LENGTH) -> Iterable[Tuple[List[str], List[str]]]:
    source_chunk = []
    target_chunk = []
    cur_len = 0
    for src, tgt in zip(source, target):
        len_src = len(tokenizer.encode(src))
        # len_tgt = len(tokenizer.encode(tgt))
        len_tgt = 0

        source_chunk.append(src)
        target_chunk.append(tgt)
        cur_len += len_src + len_tgt

        if cur_len > max_length:
            yield source_chunk, target_chunk
            source_chunk = []
            target_chunk = []
            cur_len = 0

    if source_chunk:
        yield source_chunk, target_chunk


CHATGPT_DOC_TRANSLATE_PROMPT = """
{instructions}
You will be provided with sentences, and your task is to translate it into {tgt_lang}.

1. Please output the translations in the same order as the input sentences (one translation per line).
2. Please do not add or remove any punctuation marks or any numbers.
3. Please don't do any explaining.
4. Please keep the unicode character representation of roman numerals in translations. e.g.: Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ Ⅵ Ⅶ Ⅷ Ⅸ Ⅹ
"""  # TODO: Dynamic load abbreviations from database


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), retry_error_callback=lambda _: print("ChatGPT retrying"))
async def create_chat_completion(order: int, messages: List[Dict[str, str]]):
    chat_completion_resp = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo", messages=messages, timeout=30, deployment_id=DEPLOYMENT_ID, temperature=0.0
    )
    return order, chat_completion_resp


async def _chatgpt_translate(
    origin: List[str], target: List[str], src_lang: str, tgt_lang: str, instructions="", max_length=MAX_LENGTH
) -> List[str]:
    langcodes.get(src_lang).display_name()
    tgt_lang_name = langcodes.get(tgt_lang).display_name()

    tasks = []
    chunked = list(chunk(origin, target, max_length=max_length))
    for i, (src, tgt) in enumerate(chunked):
        query = ""
        for s, t in zip(src, tgt):
            # replace all blank with space
            query += s + "\n"

        system_prompt = CHATGPT_DOC_TRANSLATE_PROMPT.format(tgt_lang=tgt_lang_name, instructions=instructions)
        example_source = []
        example_target = []
        for s in src:
            es, et = search_tm(s, src_lang, tgt_lang)
            if not es or not et:
                continue
            example_source.append(es)
            example_target.append(et)
        messages = [{"role": "system", "content": system_prompt}]

        if example_source and example_target:
            messages.append(
                {
                    "role": "user",
                    "content": "Source: \n" + "\n".join(example_source) + f"\n{tgt_lang_name} Translation: \n",
                }
            )
            messages.append({"role": "assistant", "content": "\n".join(example_target)})

        messages.append({"role": "user", "content": "Source: \n" + query + f"\n{tgt_lang_name} Translation: \n"})
        chat_completion_resp = create_chat_completion(
            order=i,
            messages=messages,
        )
        tasks.append(chat_completion_resp)

    fixed = []
    print(f"ChatGPT Translating {len(tasks)} chunks")
    for future in asyncio.as_completed(tasks):
        order, chat_completion_resp = await future
        print(f"ChatGPT finish {len(fixed) + 1}/{len(tasks)} chunks")
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

        translations = [x.strip() for x in translations if x.strip()]
        if len(translations) != len(tgt) or cur != len(answer):
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

    # filter ordianl numbers
    for i in range(len(fixed)):
        if re.match(r"\d+\.", fixed[i]) and not re.match(r"\d+\.", origin[i]):
            fixed[i] = re.sub(r"\d+\.", "", fixed[i]).strip()

    return fixed


TRANSLATION_FAILURE = "<|Openai 翻译失败|>"


async def batch_translate_texts(texts: List[str], source_language_code: str, target_language_code: str) -> List[str]:
    mock_target = [TRANSLATION_FAILURE] * len(texts)
    translations = mock_target

    max_length = MAX_LENGTH
    while TRANSLATION_FAILURE in translations and max_length > 0:
        failure_indices = [i for i, x in enumerate(translations) if x == TRANSLATION_FAILURE]
        cur_texts = [texts[i] for i in failure_indices]
        cur_target = [mock_target[i] for i in failure_indices]
        cur_translations = await _chatgpt_translate(
            cur_texts, cur_target, source_language_code, target_language_code, max_length=max_length
        )
        max_length = max_length - 200

        for i, x in zip(failure_indices, cur_translations):
            translations[i] = x

    # If still failed, use google translate
    if TRANSLATION_FAILURE in translations:
        failure_indices = [i for i, x in enumerate(translations) if x == TRANSLATION_FAILURE]
        cur_texts = [texts[i] for i in failure_indices]
        cur_translations = await google_batch_translate_texts(cur_texts, source_language_code, target_language_code)
        for i, x in zip(failure_indices, cur_translations):
            translations[i] = x

    return translations


async def translate_text(text, source_language_code, target_language_code):
    translatons = await batch_translate_texts([text], source_language_code, target_language_code)
    return translatons[0]
