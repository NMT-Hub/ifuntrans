from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ifuntrans.metadata import __version__, contact, license_info, title


class IfunTransModel(BaseModel):
    @classmethod
    def get_examples(cls):
        return cls.model_config["json_schema_extra"]["examples"]

    @classmethod
    def get_example(cls):
        return cls.get_examples()[0]

    model_config = {
        "json_schema_extra": {
            "examples": [],
        },
    }


def home():
    """redirect user to the swagger api"""
    return RedirectResponse("/docs")


def create_app():
    """create the FastAPI app"""
    # app object
    app = FastAPI(
        title=title,
        version=__version__,
        description="Ifun Translation API",
        contact=contact,
        license_info=license_info,
    )

    import ifuntrans.api.translate as translate

    app.get("/", summary="SwaggerUI (当前页面)")(home)
    app.post(
        "/translate",
        response_model=translate.TranslationResponse,
        summary="翻译接口, 传递引擎名称，翻译源语言，翻译目标语言，翻译内容，返回翻译结果",
        responses={200: translate.TranslationResponse.get_example()},
    )(translate.translate)
    app.get("/translate/supported_languages", summary="获得某个引擎支持的语种编码")(translate.get_supported_languages)
    app.get("/translate/avaliable_engines", summary="获得所有支持的引擎名称")(translate.get_avaliable_engines)
    return app
