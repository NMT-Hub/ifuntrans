import pytest

from ifuntrans.async_translators.chatgpt import _fix_ordianl_numbers, batch_translate_texts, translate_text


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
