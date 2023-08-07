import os

import ifuntrans.api.localization as localization

test_file = os.path.join(os.path.dirname(__file__), "assets/origin.xlsx")


def test_translate():
    dataframe = localization.read_excel(test_file)
    assert dataframe is not None
