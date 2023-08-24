import pathlib

import fasttext
import re

model_path = pathlib.Path(__file__).parent.parent / "assets" / "lid.176.ftz"
# Load the pre-trained language model
model = fasttext.load_model(str(model_path))


def single_detection(text):
    text = re.sub(r"\s+", " ", text)
    predictions = model.predict(text, k=1)  # k represents number of predictions
    # Extracting language code from prediction. The output format is '__label__<lang_code>'
    lang_code = predictions[0][0].replace("__label__", "")
    return lang_code



