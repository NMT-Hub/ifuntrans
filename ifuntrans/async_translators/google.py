import functools
import os
import re
from typing import List

import httpx
import langcodes
from more_itertools import chunked

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
URL = f"https://translation.googleapis.com/language/translate/v2?key={GOOGLE_API_KEY}"


@functools.cache
def get_supported_languages() -> List[str]:
    # Get the supported languages from Google
    url = "https://translation.googleapis.com/language/translate/v2/languages"
    params = {"key": GOOGLE_API_KEY}
    response = httpx.get(url, params=params)
    data = response.json()
    return [d["language"] for d in data["data"]["languages"]]


async def batch_translate_texts(texts: List[str], source_language_code: str, target_language_code: str, **kwargs) -> List[str]:
    supported_languages = get_supported_languages()
    if target_language_code not in supported_languages:
        target_language_code = langcodes.closest_supported_match(target_language_code, supported_languages)
        if not target_language_code:
            raise ValueError(f"Language code {target_language_code} is not supported by Google Translate.")

    if source_language_code not in supported_languages:
        source_language_code = langcodes.closest_supported_match(source_language_code, supported_languages)
        if not source_language_code:
            raise ValueError(f"Language code {source_language_code} is not supported by Google Translate.")

    if source_language_code == target_language_code:
        return texts

    translations = []
    for chunk in chunked(texts, 128):  # Google Translate API has a limit of 128 texts per request
        payload = {"q": chunk, "target": target_language_code, "source": source_language_code}
        async with httpx.AsyncClient() as client:
            response = await client.post(URL, json=payload)
            data = response.json()
            translations.extend([d["translatedText"] for d in data["data"]["translations"]])

    return translations


async def translate_text(text, source_language_code, target_language_code):
    texts = re.split(r"(\n+)", text)
    input_texts = [text for text in texts if text.strip()]
    translatons = await batch_translate_texts(input_texts, source_language_code, target_language_code)

    output_texts = []
    for text in texts:
        if text.strip():
            output_texts.append(translatons.pop(0))
        else:
            output_texts.append(text)

    return "".join(output_texts)
