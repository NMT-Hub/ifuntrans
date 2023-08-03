from typing import Annotated, List

import fastapi

from ifuntrans.api import app

__all__ = ["doc_translate"]


@app.route("/doc_translate", methods=["POST"])
def doc_translate(
    file: Annotated[bytes, fastapi.File(description="The xlsx files as UploadFile")],
    from_lang: Annotated[str, fastapi.Form("auto", description="The language to translate from")],
    to_langs: Annotated[List[str], fastapi.Form(["en"], description="The languages to translate to")],
):
    return "Hello, World!"
