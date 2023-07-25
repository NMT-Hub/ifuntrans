__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

from ifuntrans.translators.base import BaseTranslator

__engines__ = {
    translator.__name__.replace("Translator", "").lower(): translator
    for translator in BaseTranslator.__subclasses__()
}
