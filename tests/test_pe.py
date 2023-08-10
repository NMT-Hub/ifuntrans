from ifuntrans.pe import chatgpt_post_edit, hardcode_post_edit


def test_chatgpt_post_edit():
    """
    Post edit with chatgpt.
    """
    origin = [
        "近战部队攻击Ⅰ",
        "远程部队攻击Ⅰ",
        "急救包补给Ⅰ",
        "侦察Ⅱ",
        "行军速度Ⅱ",
    ]
    target = [
        "Melee Troop Attack I",
        "Ranged Troop Attack I",
        "First Aid Kit Supplies Ⅰ",
        "Reconnaissance II",
        "marching speed Ⅱ",  # Title Case
    ]
    pe_result = chatgpt_post_edit(
        origin, target, src_lang="zh", tgt_lang="en", instructions="整个游戏现在大概说明，背景是关于未来战争题材的，大战之后玩家重建家园，召集人才"
    )
    assert len(pe_result) == len(origin)

    for item in pe_result:
        assert not item.islower()
        assert "Ⅰ" not in item
        assert "Ⅱ" not in item


def test_hardcode_post_edit():
    origin = [
        "近战部队攻击Ⅰ",
        "远程部队攻击Ⅰ",
        "急救包补给Ⅰ",
        "侦察Ⅱ",
        "行军速度Ⅱ",
    ]
    target = [
        "Melee Troop Attack I",
        "Ranged Troop Attack I",
        "First Aid Kit Supplies Ⅰ",
        "Reconnaissance II",
        "marching speed Ⅱ",  # Title Case
    ]
    pe_result = hardcode_post_edit(origin, target, src_lang="zh", tgt_lang="en")
    assert len(pe_result) == len(origin)

    for item in pe_result:
        assert not item.islower()
        assert "Ⅰ" not in item
        assert "Ⅱ" not in item
