from typing import List

import langcodes
import pytest

from ifuntrans.async_translators.chatgpt import (
    _fix_ordianl_numbers,
    batch_translate_texts,
    normalize_language_code_as_iso639,
    translate_text,
)


@pytest.mark.asyncio
async def test_translate_text():
    text = "This is a test."
    result = await translate_text(text, "en", "zh-TW")
    assert "測試" in result


@pytest.mark.asyncio
async def test_batch_translate_texts():
    texts = ["This is a test.", "This is another test."]
    result = await batch_translate_texts(texts, "en", "zh-CN")
    assert len(result) == 2

    for r in result:
        assert "测试" in r


@pytest.mark.parametrize(
    "src, tgt, expected",
    [
        ("1. Hi, how are you!", "6. 1. 你好！", "1. 你好！"),
        ("1. Hi, how are you!", "6.1. 你好！", "1. 你好！"),
        ("1. Hi, how are you!", "1. 你好！", "1. 你好！"),
        ("Hi, how are you!", "1. 你好！", "你好！"),
    ],
)
def test_fix_ordianl_numbers(src: str, tgt: str, expected: str):
    result = _fix_ordianl_numbers(src, tgt)
    assert result == expected


@pytest.mark.parametrize(
    "lang, expected",
    [
        (["中文", "巴西葡萄牙语", "英语"], ["zh", "pt-BR", "en"]),
        (
            [
                "中文",
                "英文",
                "中文繁體",
                "印尼语",
                "泰语",
                "越南语",
                "葡萄牙语",
                "Russian",
                "韩语",
                "Turkish",
                "法语",
                "德语",
                "西班牙语",
                "意大利语",
                "日语",
                "阿拉伯语",
                "丹麦语",
                "挪威语",
                "瑞典语",
                "芬兰语",
                "荷兰语",
            ],
            [
                "zh",
                "en",
                "zh-Hant",
                "id",
                "th",
                "vi",
                "pt",
                "ru",
                "ko",
                "tr",
                "fr",
                "de",
                "es",
                "it",
                "ja",
                "ar",
                "da",
                "no",
                "sv",
                "fi",
                "nl",
            ],
        ),
        (
            [
                "序号",
                "路径",
                "当前展示",
                "中文",
                "英语",
                "日语",
                "韩语",
                "葡萄牙语",
                "西班牙语",
                "法语",
                "德语",
                "俄语Russian",
                "印尼语",
                "备注",
                "Unnamed: 14",
                "Unnamed: 15",
            ],
            [
                "und",
                "und",
                "und",
                "zh",
                "en",
                "ja",
                "ko",
                "pt",
                "es",
                "fr",
                "de",
                "ru",
                "id",
                "und",
                "und",
                "und",
            ],
        ),
    ],
)
@pytest.mark.asyncio
async def test_normalize_language_code_as_iso639(lang: List[str], expected: List[str]):
    iso_codes = await normalize_language_code_as_iso639(lang)

    for code, expected_code in zip(iso_codes, expected):
        assert langcodes.closest_supported_match(code, expected) == expected_code
