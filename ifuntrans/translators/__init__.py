"""Top-level package for Deep Translator"""
import functools

from ifuntrans.translators.baidu import BaiduTranslator
from ifuntrans.translators.base import BaseTranslator
from ifuntrans.translators.chatgpt import ChatGptTranslator
from ifuntrans.translators.deepl import DeeplTranslator
from ifuntrans.translators.google import GoogleTranslator
from ifuntrans.translators.linguee import LingueeTranslator
from ifuntrans.translators.microsoft import MicrosoftTranslator
from ifuntrans.translators.mymemory import MyMemoryTranslator
from ifuntrans.translators.papago import PapagoTranslator
from ifuntrans.translators.pons import PonsTranslator
from ifuntrans.translators.qcri import QcriTranslator
from ifuntrans.translators.tencent import TencentTranslator
from ifuntrans.translators.yandex import YandexTranslator

name2translator = {
    "google": GoogleTranslator,
    "deepl": DeeplTranslator,
    "microsoft": MicrosoftTranslator,
    "baidu": BaiduTranslator,
    "tencent": TencentTranslator,
    "yandex": YandexTranslator,
    "my_memory": MyMemoryTranslator,
    "linguee": LingueeTranslator,
    "pons": PonsTranslator,
    "qcri": QcriTranslator,
    "papago": PapagoTranslator,
    "chatgpt": ChatGptTranslator,
}


@functools.lru_cache(maxsize=128)
def get_translator(name: str, source: str, target: str) -> "BaseTranslator":
    """Get translator by name"""
    translator = name2translator.get(name)
    if translator is None:
        raise ValueError(f"Translator {name} not found")
    return translator(source=source, target=target)
