import pytest

from ifuntrans.async_translators.google import batch_translate_texts, translate_text


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
        assert "测试" in r or "。" in r
