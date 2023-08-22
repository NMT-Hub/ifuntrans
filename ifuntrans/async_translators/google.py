import os
from typing import List

import httpx

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
URL = f"https://translation.googleapis.com/language/translate/v2?key={GOOGLE_API_KEY}"


async def batch_translate_texts(
    texts: List[str], source_language_code: str, target_language_codes: str
) -> List[str]:
    payload = {"q": texts, "source": source_language_code, "target": target_language_codes}
    async with httpx.AsyncClient() as client:
        response = await client.post(URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return [d["translatedText"] for d in data["data"]["translations"]]


async def translate_text(text, source_language_code, target_language_code):
    translatons = await batch_translate_texts([text], source_language_code, target_language_code)
    return translatons[0]
