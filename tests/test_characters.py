import pytest

from ifuntrans import characters


@pytest.mark.parametrize(
    "text, expected",
    [
        (r"你好", True),
        (r"！！。。", False),
        (r"{$thinkTips}", False),
        ("\n\r", False),
    ],
)
def test_need_translate(text, expected):
    func = characters.get_need_translate_func("zh")
    assert func(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (r"Hello world!", True),
        (r".....", False),
        (r"{$thinkTips}", False),
        (r"123ABC", False),
    ],
)
def test_need_translate_en(text, expected):
    func = characters.get_need_translate_func("en")
    assert func(text) == expected
