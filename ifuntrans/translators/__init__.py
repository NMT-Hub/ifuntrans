"""Top-level package for Deep Translator"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

from ifuntrans.translators.baidu import BaiduTranslator
from ifuntrans.translators.chatgpt import ChatGptTranslator
from ifuntrans.translators.deepl import DeeplTranslator
from ifuntrans.translators.detection import batch_detection, single_detection
from ifuntrans.translators.google import GoogleTranslator
from ifuntrans.translators.libre import LibreTranslator
from ifuntrans.translators.linguee import LingueeTranslator
from ifuntrans.translators.microsoft import MicrosoftTranslator
from ifuntrans.translators.mymemory import MyMemoryTranslator
from ifuntrans.translators.papago import PapagoTranslator
from ifuntrans.translators.pons import PonsTranslator
from ifuntrans.translators.qcri import QcriTranslator
from ifuntrans.translators.tencent import TencentTranslator
from ifuntrans.translators.yandex import YandexTranslator

__author__ = """Han Bing"""
__email__ = "beatmight@gmail.com"
__version__ = "1.9.1"

__all__ = [
    "GoogleTranslator",
    "PonsTranslator",
    "LingueeTranslator",
    "MyMemoryTranslator",
    "YandexTranslator",
    "MicrosoftTranslator",
    "QcriTranslator",
    "DeeplTranslator",
    "LibreTranslator",
    "PapagoTranslator",
    "ChatGptTranslator",
    "TencentTranslator",
    "BaiduTranslator",
    "single_detection",
    "batch_detection",
]
