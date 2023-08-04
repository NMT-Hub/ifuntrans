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

    data: str
    source: str
    target: str

    model_config = {
        "json_schema_extra": {
            "examples": [{"code": 200, "message": "请求成功", "data": "Hello world", "source": "fr", "target": "en"}]
        }
    }


def translate(
    request: Annotated[
        TranslationRequest,
        fastapi.Body(
            ...,
            embed=False,
            examples=TranslationRequest.get_examples(),
        ),
    ]
) -> TranslationResponse:
    translator = get_translator(request.engine, request.source, request.target)
    return TranslationResponse(
        data=translator.translate(request.text),
        source=request.source,
        target=request.target,
    )


class AvaliableEngineResponse(IfunTransModel):
    """model for a base response that contain a translated text"""

    engines: Dict[str, str]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": 200,
                    "message": "请求成功",
                    "engines": {"google": "Google", "baidu": "Baidu", "tencent": "Tencent"},
                }
            ]
        }
    }


def get_avaliable_engines(
    # source: Annotated[str, fastapi.Query(..., description="source language", example="fr")],
    # target: Annotated[str, fastapi.Query(..., description="target language", example="en")],
) -> AvaliableEngineResponse:
    return AvaliableEngineResponse(engines=SUPPORTED_ENGINES)


class SupportedLanguagesResponse(IfunTransModel):
    """model for a base response that contain a translated text"""

    languages: List[str]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": 200,
                    "message": "请求成功",
                    "languages": ["en", "fr", "zh-CN", "zh-TW"],
                }
            ]
        }
    }


def get_supported_languages(engine: str = "google") -> SupportedLanguagesResponse:
    translator = get_translator(engine, "auto", "en")
    return SupportedLanguagesResponse(languages=translator.get_supported_languages())
