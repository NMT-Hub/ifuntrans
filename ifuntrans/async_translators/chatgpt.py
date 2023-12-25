import asyncio
import os
import re
import typing
from itertools import chain
from typing import Dict, Iterable, List, Optional, Tuple

import langcodes
import openai
from loguru import logger
from more_itertools import windowed

from ifuntrans.async_translators.google import batch_translate_texts as google_batch_translate_texts
from ifuntrans.tokenizer import tokenizer

if typing.TYPE_CHECKING:
    from ifuntrans.tm import TranslationMemory


if os.environ.get("USE_GPT4", None):
    AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_GPT4_ENDPOINT"]
    AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_GPT4_API_KEY"]
    DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID_GPT4"]
    logger.info("Use GPT4")
else:
    AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
    AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
    DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID"]
    logger.info("Use GPT3.5")

# OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# openai.api_key = os.environ["OPENAI_API_KEY"]

openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = "2023-05-15"

MAX_LENGTH = 500

CHATGPT_DOC_TRANSLATE_PROMPT = """
{instructions}
You will be provided with sentences, and your task is to translate it into {tgt_lang}.

1. Please output the translations in the same order as the input sentences (one translation per line).
2. Please do not add or remove any punctuation marks or any numbers.
3. Please don't do any explaining.
4. Please keep the unicode character representation of roman numerals in translations. e.g.: Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ Ⅵ Ⅶ Ⅷ Ⅸ Ⅹ
"""  # TODO: Dynamic load abbreviations from database


async def create_chat_completion(order: int, messages: List[Dict[str, str]]):
    try:
        chat_completion_resp = await openai.ChatCompletion.acreate(
            messages=messages, timeout=30, deployment_id=DEPLOYMENT_ID, temperature=0.0
        )
        response = chat_completion_resp.choices[0].message.content

    except AttributeError:
        logger.warning(f"ChatGPT failed: {chat_completion_resp.choices[0]}")
        response = ""
    except Exception as e:
        logger.warning(f"ChatGPT failed: {e}")
        response = ""
    return order, response


def _fix_ordianl_numbers(src: str, tgt: str) -> str:
    """
    Filter ordinal numbers.
    """
    # filter ordianl numbers
    if re.match(r"^\d+\.", tgt) and not re.match(r"^\d+\.", src):
        tgt = re.sub(r"\d+\.", "", tgt).strip()

    if re.match(r"^\d+\.\s?\d+\.", tgt) and re.match(r"^\d+\.", src) and not re.match(r"^\d+\.\s?\d+\.", src):
        tgt = re.sub(r"\d+\.\s?(\d+\.)", r"\1", tgt).strip()

    return tgt


async def _chatgpt_translate(
    origin: List[str],
    target: List[str],
    searched_tm: List[Dict[str, str]],
    src_lang: str,
    tgt_lang: str,
    instructions="",
    max_length=MAX_LENGTH,
    **kwargs,
) -> List[str]:
    src_lang_name = langcodes.get(src_lang).display_name()
    tgt_lang_name = langcodes.get(tgt_lang).display_name()

    def chunk() -> Iterable[Tuple[List[str], List[str], List[Dict[str, str]]]]:
        source_chunk = []
        target_chunk = []
        tm_chunk = []

        cur_len = 0
        for src, tgt, sts in zip(origin, target, searched_tm):
            len_src = len(tokenizer.encode(src))
            len_tgt = 0

            source_chunk.append(src)
            target_chunk.append(tgt)
            tm_chunk.append(sts)
            cur_len += len_src + len_tgt

            if cur_len > max_length:
                yield source_chunk, target_chunk, tm_chunk
                source_chunk = []
                target_chunk = []
                tm_chunk = []
                cur_len = 0

        if source_chunk:
            yield source_chunk, target_chunk, tm_chunk

    tasks = []
    chunked = list(chunk())
    for i, (src, tgt, st) in enumerate(chunked):
        query = ""
        for s, _ in zip(src, tgt):
            # replace all blank with space
            query += s + "\n"

        merged_tm = {}
        for d in st:
            merged_tm.update(d)

        system_prompt = CHATGPT_DOC_TRANSLATE_PROMPT.format(tgt_lang=tgt_lang_name, instructions=instructions)
        messages = [{"role": "system", "content": system_prompt}]

        example_source = list(merged_tm.keys())
        example_target = list(merged_tm.values())
        if example_source and example_target:
            messages.append(
                {
                    "role": "user",
                    "content": f"Please translate these terms. And all translations must follow these terms. {src_lang_name} Source: \n"
                    + "\n".join(example_source)
                    + f"\n\n{tgt_lang_name} Translations: \n",
                }
            )
            messages.append({"role": "assistant", "content": "\n".join(example_target)})
            logger.debug(messages)

        messages.append(
            {"role": "user", "content": f"{src_lang_name} Source: \n" + query + f"\n\n{tgt_lang_name} Translations: \n"}
        )
        chat_completion_resp = create_chat_completion(
            order=i,
            messages=messages,
        )
        tasks.append(chat_completion_resp)

    fixed = []
    logger.debug(f"ChatGPT Translating {len(tasks)} chunks")

    # in case that the number of tasks is too large, we split them into windows
    for window in windowed(tasks, 10, step=10):
        # filter None
        window = [x for x in window if x is not None]
        for future in asyncio.as_completed(window):
            order, response = await future

            logger.debug(f"ChatGPT finish {len(fixed) + 1}/{len(tasks)} chunks")
            answer = response.strip().split("\n")

            src, tgt, _ = chunked[order]

            # In case that there are multiple new lines in the source sentence
            translations = []
            cur = 0
            for s in src:
                num_new_lines = s.count("\n")
                translations.append("\n".join(answer[cur : cur + num_new_lines + 1]))
                cur += num_new_lines + 1

            translations = [x.strip() for x in translations if x.strip()]
            if len(translations) != len(tgt) or cur != len(answer):
                logger.warning(
                    f"ChatGPT Doc Translate failed. Please check the following sentences: "
                    f"Source: {src} "
                    f"Target: {tgt} "
                    f"Answer: {translations} "
                )
                translations = tgt
            fixed.append((order, translations))

    fixed.sort(key=lambda x: x[0])
    fixed = list(chain.from_iterable([x[1] for x in fixed]))

    # filter ordianl numbers
    for i in range(len(fixed)):
        fixed[i] = _fix_ordianl_numbers(origin[i], fixed[i])

    return fixed


TRANSLATION_FAILURE = "<|Openai 翻译失败|>"


async def batch_translate_texts(
    texts: List[str],
    source_language_code: str,
    target_language_code: str,
    tm: Optional["TranslationMemory"] = None,
    **kwargs,
) -> List[str]:
    mock_target = [TRANSLATION_FAILURE] * len(texts)
    translations = mock_target

    # search from TM
    searched_tm = []

    for i, text in enumerate(texts):
        if tm is None:
            searched_tm.append({})
        else:
            search_result = tm.search_tm(text, source_language_code, target_language_code)
            if text in search_result:
                translations[i] = search_result[text]
            searched_tm.append(search_result)

    max_length = MAX_LENGTH
    prev_failures_indices = []
    while TRANSLATION_FAILURE in translations and max_length > 20:
        failure_indices = [i for i, x in enumerate(translations) if x == TRANSLATION_FAILURE]

        # If prev_failures_indices is empty, it means that the first time to translate, don't need to log
        if prev_failures_indices:
            logger.debug(f"From {source_language_code} to {target_language_code}. Failed indices: {failure_indices}")

        prev_failures_indices = failure_indices
        cur_texts = [texts[i] for i in failure_indices]
        cur_target = [mock_target[i] for i in failure_indices]
        cur_tm = [searched_tm[i] for i in failure_indices]
        cur_translations = await _chatgpt_translate(
            cur_texts,
            cur_target,
            cur_tm,
            source_language_code,
            target_language_code,
            max_length=max_length,
            **kwargs,
        )
        max_length = max_length // 2

        for i, x in zip(failure_indices, cur_translations):
            translations[i] = x

    # If still failed, use google translate
    if TRANSLATION_FAILURE in translations:
        failure_indices = [i for i, x in enumerate(translations) if x == TRANSLATION_FAILURE]
        cur_texts = [texts[i] for i in failure_indices]
        logger.warning(f"ChatGPT failed. Use Google Translate instead. {len(cur_texts)} sentences. {cur_texts}")
        cur_translations = await google_batch_translate_texts(cur_texts, source_language_code, target_language_code)
        for i, x in zip(failure_indices, cur_translations):
            translations[i] = x

    return translations


async def translate_text(text, *args, **kwargs):
    texts = re.split(r"(\n+)", text)
    input_texts = [text for text in texts if text.strip()]

    translatons = await batch_translate_texts(input_texts, *args, **kwargs)

    output_texts = []
    for text in texts:
        if text.strip():
            output_texts.append(translatons.pop(0))
        else:
            output_texts.append(text)

    return "".join(output_texts)


async def normalize_language_code_as_iso639(langs: List[str]) -> List[str]:
    system_prompt = """
    Please normalize the language name to ISO 639-2 format. If the language name is not a valid ISO 639 language name, please use "not a valid ISO 639 language name" instead.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": ", ".join(["STR_ID", "路径", "序号", "cn", "英文", "tw", "印尼语", "备注"])},
        {
            "role": "assistant",
            "content": "\n".join(
                [
                    "STR_ID: not a valid ISO 639 language name",
                    "路径: not a valid ISO 639 language name",
                    "序号: not a valid ISO 639 language name",
                    "cn: zh",
                    "英文: en",
                    "tw: zh-TW",
                    "印尼语: id",
                    "备注: not a valid ISO 639 language name",
                ]
            ),
        },
        {"role": "user", "content": ", ".join(langs)},
    ]

    chat_completion_resp = await openai.ChatCompletion.acreate(
        model="gpt-4", messages=messages, timeout=30, deployment_id=DEPLOYMENT_ID, temperature=0.0
    )
    response = chat_completion_resp.choices[0].message.content

    iso_codes = [re.sub(".*: ", "", x) for x in response.strip().split("\n")]

    if len(iso_codes) != len(langs):
        mappings = {re.sub(": .*", "", x): re.sub(".*: ", "", x) for x in response.strip().split("\n")}
        iso_codes = [mappings.get(x, "und") for x in langs]

    iso_codes = [
        y if y.isascii() and len(y) <= 8 and langcodes.get(y).is_valid() else "und" for _, y in zip(langs, iso_codes)
    ]
    return iso_codes
