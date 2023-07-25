from ifuntrans.api import app

__all__ = ["doc_translate"]


@app.route("/doc_translate", methods=["POST"])
def doc_translate():
    return "Hello, World!"
