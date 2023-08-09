from ifuntrans.pe import chatgpt_post_edit


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
    chatgpt_post_edit(origin, target, instructions="整个游戏现在大概说明，背景是关于未来战争题材的，大战之后玩家重建家园，召集人才")
    import ipdb
    ipdb.set_trace()
    pass

