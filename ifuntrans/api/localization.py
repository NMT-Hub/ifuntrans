from ifuntrans.api import app

__all__ = ["localization"]


@app.route("/localization", methods=["POST"])
def localization():
    pass
