import os

from ifuntrans.tm import TranslationMemory

test_file = os.path.join(os.path.dirname(__file__), "assets/terms.xlsx")


def test_tm():
    tm = TranslationMemory(test_file)

    result = tm.search_tm("4、射手会克制硬汉，硬汉克制骑手，骑手克制射手，运输者被以上三个兵种克制，进行战斗时多注意敌我兵种的克制，可能会有出其不意的效果。", "zh", "en")

    assert "射手" in result
    assert "骑手" in result
    assert "运输者" in result
    assert "硬汉" in result
