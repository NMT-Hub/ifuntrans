from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from ifuntrans.metadata import (__version__, contact, description,
                                license_info, title)


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
    app.get("/", summary="show SwaggerUI (this page)")(home)
    return app
