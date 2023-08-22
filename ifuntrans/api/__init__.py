import fastapi
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ifuntrans.api.constants import LANG_EN_TO_CODE
from ifuntrans.metadata import __version__, contact, license_info, title


class IfunTransModel(BaseModel):
    message: str = "请求成功"
    code: int = 200
    data: str = ""

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


async def logging_request_data(request: fastapi.Request):
    body = await request.body()
    print(f"request body: {body}")


async def redirect_trailing_slash(request: fastapi.Request, call_next):
    if request.url.path.endswith("/") and not request.url.path == "/":
        # Remove the trailing slash and create a new URL without it
        new_url = str(request.url)[:-1]
        # Create a redirect response to the new URL
        return RedirectResponse(url=new_url)
    # If there's no trailing slash or it's the root "/", proceed as usual
    response = await call_next(request)
    return response


async def custom_exception_handler(request: fastapi.Request, exc: Exception):
    return fastapi.responses.JSONResponse(
        content={"message": "服务器内部错误", "code": 500, "data": ""},
    )


def home():
    """redirect user to the swagger api"""
    return RedirectResponse("/docs")


def get_lang_codes_en():
    """get all supported language codes"""
    return LANG_EN_TO_CODE

def get_lang_codes_zh():
    """get all supported language codes"""
    return LANG_EN_TO_CODE


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

    app.exception_handler(Exception)(custom_exception_handler)
    app.middleware("http")(redirect_trailing_slash)
    app.get("/", summary="SwaggerUI (当前页面)")(home)
    app.get("/lang_codes_en", summary="获取所有支持的语言代码（英语版本）")(get_lang_codes_en)
    app.get("/lang_codes_zh", summary="获取所有支持的语言代码（中文版本）")(get_lang_codes_zh)
    app.post(
        "/translate",
        summary="翻译接口, 传递引擎名称，翻译源语言，翻译目标语言，翻译内容，返回翻译结果",
        responses={200: translate.TranslationResponse.get_example()},
        dependencies=[fastapi.Depends(logging_request_data)],
    )(translate.translate)

    return app
