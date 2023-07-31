from typing import Annotated, List

import fastapi

from ifuntrans.api import IfunTransModel

__all__ = ["translate", "get_avaliable_engines", "get_avaliable_languages"]


SUPPORTED_ENGINES = ["google", "deepl", "bing", "yandex", "baidu", "tencent", "chatgpt"]


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
    pass


def get_avaliable_engines(
    source: Annotated[str, fastapi.Query(..., description="source language", example="fr")],
    target: Annotated[str, fastapi.Query(..., description="target language", example="en")],
) -> List[str]:
    return SUPPORTED_ENGINES


def get_supported_languages(engine: str = "google"):
    return {"languages": ["en", "zh", "fr", "de", "ja", "ko", "es", "pt", "it", "ru", "vi", "id", "th", "ms", "ar"]}
