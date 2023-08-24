import os

import httpx

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
URL = f"https://translation.googleapis.com/language/translate/v2/detect"


async def single_detection(text):
    params = {"q": text, "key": GOOGLE_API_KEY}
    async with httpx.AsyncClient() as client:
        response = await client.get(URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data["data"]["detections"][0][0]["language"]
