from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ifuntrans.metadata import (__version__, contact, description,
                                license_info, title)


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
        description=description,
        contact=contact,
        license_info=license_info,
    )

    import ifuntrans.api.translate as translate

    app.get("/", summary="show SwaggerUI (this page)")(home)
    app.post(
        "/translate",
        response_model=translate.TranslationResponse,
        summary="translate text",
        responses={200: translate.TranslationResponse.get_example()},
    )(translate.translate)
    app.get("/translate/supported_languages", summary="get supported languages")(translate.get_supported_languages)
    app.get("/translate/avaliable_engines", summary="get avaliable engines")(translate.get_avaliable_engines)
    return app
