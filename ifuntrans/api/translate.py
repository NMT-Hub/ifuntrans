from typing import Annotated

import fastapi
from pydantic import BaseModel

from ifuntrans.api import app

__all__ = ["translate", "get_avaliable_engines", "get_avaliable_languages"]


class TranslationRequest(BaseModel):
    """model for a base request that require a source & target language and a text to translate"""

    engine: str = "google"
    source: str = "auto"
    target: str
    text: str


def translate(
    request: Annotated[
        TranslationRequest,
        fastapi.Body(
            ...,
            embed=True,
            examples=[{"engine": "google", "source": "auto", "target": "en", "text": "Bonjour le monde"}],
        ),
    ]
):
    pass


def get_avaliable_engines():
    return ["google", "deepl", "bing"]


@app.route("/get_supported_languages", methods=["GET"])
def get_supported_languages():
    return "Hello, World!"
