from typing import Annotated, Optional

import fastapi
import pydantic

from ifuntrans.api import IfunTransModel
from ifuntrans.api.localization import translate_s3_excel_task
from ifuntrans.translators import get_translator
from ifuntrans.utils import get_s3_key_from_id

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

    engine: Optional[str] = "google"
    sourceLan: str = "auto"
    targetLan: str = "en"
    translateSource: str
    type: str = "text"
    id: int = 0

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "engine": "google",
                    "sourceLan": "auto",
                    "targetLan": "en",
                    "translateSource": "Bonjour le monde",
                }
            ]
        }
    }

    @pydantic.validator("sourceLan")
    def check_age(cls, sourceLan: str):
        if not sourceLan:
            return "auto"
        return sourceLan

    @pydantic.validator("engine")
    def check_engine(cls, engine: str):
        if not engine:
            return "google"
        return engine


class TranslationResponse(IfunTransModel):
    """model for a base response that contain a translated text"""

    data: str
    sourceLan: str
    targetLan: str

    model_config = {
        "json_schema_extra": {
            "examples": [{"code": 200, "message": "请求成功", "data": "Hello World", "sourceLan": "fr", "targetLan": "en"}]
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
    ],
    background_tasks: fastapi.BackgroundTasks,
) -> TranslationResponse:
    if request.type == "text":
        translator = get_translator(request.engine, request.sourceLan, request.targetLan)
        return TranslationResponse(
            data=translator.translate(request.translateSource),
            sourceLan=translator.source,
            targetLan=request.targetLan,
        )
    else:
        background_tasks.add_task(translate_s3_excel_task, request.id, request.translateSource, request.targetLan)
        return TranslationResponse(
            data=get_s3_key_from_id(request.id),
            sourceLan="",
            targetLan="",
        )
