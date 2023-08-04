from typing import Annotated, Dict, List

import fastapi

from ifuntrans.api import IfunTransModel
from ifuntrans.translators import get_translator

__all__ = ["translate", "get_avaliable_engines", "get_avaliable_languages"]


SUPPORTED_ENGINES = {
    "google": "Google翻译",
    "deepl": "DeepL",
    "baidu": "百度翻译",
    "tencent": "腾讯翻译君",
    "microsoft": "微软Bing翻译",
    "yandex": "Yandex",
    "chatgpt": "ChatGPT",
}


class TranslationRequest(IfunTransModel):
    """model for a base request that require a source & target language and a text to translate"""

    engine: str = "google"
    source: str = "auto"
    target: str
    text: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "engine": "google",
                    "source": "auto",
                    "target": "en",
                    "text": "Bonjour le monde",
                }
            ]
        }
    }


class TranslationResponse(IfunTransModel):
    """model for a base response that contain a translated text"""

    translation: str
    source: str
    target: str

    model_config = {"json_schema_extra": {"examples": [{"translation": "Hello world", "source": "fr", "target": "en"}]}}


def translate(
    request: Annotated[
        TranslationRequest,
        fastapi.Body(
            ...,
            embed=True,
            examples=TranslationRequest.get_examples(),
        ),
    ]
) -> TranslationResponse:
    translator = get_translator(request.engine, request.source, request.target)
    return TranslationResponse(
        translation=translator.translate(request.text),
        source=request.source,
        target=request.target,
    )


def get_avaliable_engines(
    source: Annotated[str, fastapi.Query(..., description="source language", example="fr")],
    target: Annotated[str, fastapi.Query(..., description="target language", example="en")],
) -> Dict[str, str]:
    return SUPPORTED_ENGINES


def get_supported_languages(engine: str = "google") -> List[str]:
    translator = get_translator(engine, "auto", "en")
    return translator.get_supported_languages()
