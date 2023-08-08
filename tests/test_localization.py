import os
import tempfile

import pandas as pd

import ifuntrans.api.localization as localization

test_file = os.path.join(os.path.dirname(__file__), "assets/small.xlsx")


def test_translate():
    # 翻译到英语，中文繁体（台繁），印尼语，越南语，泰语，巴西葡萄牙语，日，韩，阿拉伯，土耳其
    # langs = "en,zh-TW,id,vi,th,pt-BR,ja,ko,ar,tr"
    langs = "en,zh-TW"
    output = tempfile.NamedTemporaryFile(dir=os.path.dirname(test_file), suffix=".xlsx", delete=False)
    localization.translate_excel(test_file, output.name, langs)

    # assert sheet num
    df = pd.read_excel(output.name, sheet_name=None)
    assert len(df) == len(langs.split(",")) + 1
    # delete
    output.close()
    os.remove(output.name)
