import importlib
from typing import List

from ifuntrans.pe.general import hardcode_post_edit as general_hardcode_post_edit


async def hardcode_post_edit(origin: List[str], target: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    try:
        pe_module = importlib.import_module(f"ifuntrans.pe.{tgt_lang}")
        target = await pe_module.hardcode_post_edit(origin, target, src_lang, tgt_lang)
    except ModuleNotFoundError:
        pass
    return await general_hardcode_post_edit(origin, target, src_lang, tgt_lang)


async def post_edit(origin: List[str], target: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    """
    Post edit.
    """
    target = await hardcode_post_edit(origin, target, src_lang, tgt_lang)
    return target
