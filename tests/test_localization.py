import os

import ifuntrans.api.localization as localization

test_file = os.path.join(os.path.dirname(__file__), "assets/small.xlsx")


def test_translate():
    # 翻译到英语，中文繁体（台繁），印尼语，越南语，泰语，巴西葡萄牙语，日，韩，阿拉伯，土耳其
    output_file = "~/Desktop/translated.xlsx"
    localization.translate_excel(test_file, output_file, "en,zh-TW,id,vi,th,pt-BR,ja,ko,ar,tr")
    # localization.translate_excel(test_file, output_file, "en")
