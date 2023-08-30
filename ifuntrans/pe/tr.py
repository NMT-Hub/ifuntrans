import re
from typing import List


async def hardcode_post_edit(origin: List[str], target: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    for i in range(len(origin)):
        if re.search(r"(\{\d+\})(\s*)%", target[i]):
            target[i] = re.sub(r"(\{\d+\})(\s*)%", r"%\1\2", target[i])
    return target
