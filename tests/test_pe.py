import pytest

from ifuntrans.pe import post_edit


@pytest.mark.parametrize(
    "origin, target, reference, src_lang, tgt_lang",
    [
        (
            [
                "近战部队攻击Ⅰ",
                "急救包补给Ⅱ",
            ],
            [
                "Melee Troop Attack I",
                "Reconnaissance II",
            ],
            [
                "Melee Troop Attack Ⅰ",
                "Reconnaissance Ⅱ",
            ],
            "zh",
            "en",
        ),
        (
            [
                "指挥官天赋：+{0}（{1}%）",
            ],
            [
                "Komutan Yeteneği: +{0} ({1}%)",
            ],
            [
                "Komutan Yeteneği: +{0} (%{1})",
            ],
            "zh",
            "tr",
        ),
    ],
)
@pytest.mark.asyncio
async def test_post_edit(origin, target, reference, src_lang, tgt_lang):
    pe_result = await post_edit(origin, target, src_lang, tgt_lang)
    assert len(pe_result) == len(origin)

    assert pe_result == reference
