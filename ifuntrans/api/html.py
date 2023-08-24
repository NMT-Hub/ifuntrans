import re

from bs4 import BeautifulSoup, Comment

from ifuntrans.async_translators.google import batch_translate_texts
from ifuntrans.lang_detection import single_detection

NON_TRANSLATEABLE_TAGS = [
    "address",
    "applet",
    "audio",
    "canvas",
    "code",
    "embed",
    "script",
    "style",
    "time",
    "video",
]


async def translate_html(html_content: str, source_language: str, target_language: str) -> str:
    """Translate all text within an HTML content without changing the structure, but ignore specified tags."""
    soup = BeautifulSoup(html_content, "html.parser")
    all_text = []

    # Recursive function to traverse and translate text nodes
    def extract_text(node):
        # If it's a tag that shouldn't be translated, return
        if (
            node.name in NON_TRANSLATEABLE_TAGS
            or isinstance(node, Comment)
            or (node.string and re.match(r"^\s*$", node.string))
        ):
            return
        # If the current node is a tag, recurse into its children
        if node.name:
            for child in node.children:
                extract_text(child)
        else:
            # If it's a text node, translate it
            all_text.append(node.string)

    extract_text(soup)
    if source_language == "auto":
        source_language = await single_detection("".join(all_text))
    translations = await batch_translate_texts(all_text, source_language, target_language)

    def replace_text(node):
        if (
            node.name in NON_TRANSLATEABLE_TAGS
            or isinstance(node, Comment)
            or (node.string and re.match(r"^\s*$", node.string))
        ):
            return
        if node.name:
            for child in node.children:
                replace_text(child)
        else:
            node.replace_with(translations.pop(0))

    replace_text(soup)
    return str(soup), source_language
