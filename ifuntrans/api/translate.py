from typing import Annotated, Optional

import fastapi
import pydantic

from ifuntrans.api import IfunTransModel
from ifuntrans.api.localization import translate_s3_excel_task
from ifuntrans.utils import get_s3_key_from_id
import ifuntrans.async_translators as translators
from ifuntrans.lang_detection import single_detection

SUPPORTED_ENGINES = {
    "google": "Google翻译",
    # "deepl": "DeepL",
    # "baidu": "百度翻译",
    # "tencent": "腾讯翻译君",
    # "microsoft": "微软Bing翻译",
    # "yandex": "Yandex",
    "chatgpt": "ChatGPT",
}


class TranslationRequest(IfunTransModel):
    """model for a base request that require a source & target language and a text to translate"""

    sourceLan: str = "auto"
    targetLan: str = "en"
    translateSource: str
    type: str = "text"
    id: int = 0
    engine: Optional[str] = "google"

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

    @pydantic.field_validator("sourceLan")
    def check_age(cls, sourceLan: str):
        if not sourceLan:
            return "auto"
        return sourceLan

    @pydantic.field_validator("engine")
    def check_engine(cls, engine: str, values: dict):
        if values.data["type"] == "html":
            return "google"
        if not engine:
            return "google"
        if engine not in SUPPORTED_ENGINES:
            return "google"
        return engine


class TranslationResponse(IfunTransModel):
    """model for a base response that contain a translated text"""

    data: str
    sourceLan: str
    targetLan: str
    engine: str = "google"

    model_config = {
        "json_schema_extra": {
            "examples": [{"code": 200, "message": "请求成功", "data": "Hello World", "sourceLan": "fr", "targetLan": "en", "engine": "google"}]
        }
    }


async def translate(
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
        sourceLan = request.sourceLan
        if sourceLan == "auto":
            sourceLan = single_detection(request.translateSource)
        engine = getattr(translators, request.engine)
        translation = await engine.translate_text(request.translateSource, sourceLan, request.targetLan)
        return TranslationResponse(
            data=translation,
            sourceLan=request.sourceLan,
            targetLan=request.targetLan,
            engine=request.engine,
        )
    else:
        background_tasks.add_task(translate_s3_excel_task, request.id, request.translateSource, request.targetLan)
        return TranslationResponse(
            data=get_s3_key_from_id(request.id),
            sourceLan="",
            targetLan="",
        )
