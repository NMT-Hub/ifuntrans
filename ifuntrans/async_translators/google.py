import functools
import os
from typing import List

import httpx
import langcodes

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


async def batch_translate_texts(texts: List[str], source_language_code: str, target_language_code: str) -> List[str]:
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

    payload = {"q": texts, "target": target_language_code, "source": source_language_code}
    async with httpx.AsyncClient() as client:
        response = await client.post(URL, json=payload)
        data = response.json()
        return [d["translatedText"] for d in data["data"]["translations"]]


async def translate_text(text, source_language_code, target_language_code):
    translatons = await batch_translate_texts([text], source_language_code, target_language_code)
    return translatons[0]
