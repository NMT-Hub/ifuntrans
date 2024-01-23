import re
from typing import List


def _split_text_help_func(match_obj: re.Match):
    return re.sub(r"\s+", " ", match_obj.group(0))


def split_text(text: str):
    """
    Split text into sentences.

    Args:
        text (str): the text to be split

    Returns:
        List[str]: the sentences
    """
    text = text.replace(r"\n", "\n")
    # 这里只对较短的文本做换行符合并处理，过长的内容处理会出问题
    if len(text.split()) < 5:
      text = re.sub(r"[A-Za-z](\s*[\n|\r]+\s*)[A-Za-z]", _split_text_help_func, text)
    sents = re.split(r"([\n\r]+)", text)
    return sents


def normalize_case(text: str) -> str:
    if text.isupper():
        if len(text.split()) < 4:
            return text.title()
        else:
            return text.lower()
    else:
        return text


class Placeholder:
    def __init__(self):
        self.is_enter = False

    def enter(self, texts: List[str]) -> List[str]:
        pass

    def leave(self, texts: List[str]) -> List[str]:
        if not self.is_enter:
            raise RuntimeError("Placeholder.leave() called before Placeholder.enter()")

        self.is_enter = False
