"""Translation Memory"""
import asyncio
import pathlib
from typing import Dict

import langcodes
import pandas
from whoosh.fields import ID, TEXT, Schema
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import OrGroup, QueryParser

from ifuntrans.async_translators.chatgpt import normalize_language_code_as_iso639
from ifuntrans.tokenizer import detokenize, tokenize

DEFAULT_TM_PATH = (pathlib.Path(__file__).parent.parent / "assets" / "tm.xlsx").resolve().as_posix()


class TranslationMemory(object):
    @property
    def index_path(self):
        # return (pathlib.Path(__file__).parent.parent / ".index").resolve().as_posix()
        return ":memory:"

    def __init__(self, tm_path: str):
        # TODO: empty tm_path with only langs
        self.tm_path = tm_path

        tm_df = (
            pandas.read_excel(self.tm_path, engine="openpyxl")
            .fillna("")
            .astype(str)
            .drop_duplicates()
            # .applymap(str.lower)
        )
        langs = asyncio.run(normalize_language_code_as_iso639(tm_df.columns.tolist()))

        # 第一列应该是id,这里强制设置为und
        langs[0] = "und"
        tm_df.columns = langs

        self.langs = [lang for lang in langs if lang != "und"]

        columns = {lang: TEXT(stored=True) for lang in self.langs}
        schema = Schema(
            STR_ID=ID(stored=True),
            **columns,
        )

        st = RamStorage()
        self.ix = st.create_index(
            schema,
        )

        writer = self.ix.writer()
        for _, row in tm_df.iterrows():
            docs = {}
            for lang in self.langs:
                string = row[lang]
                docs[lang] = tokenize(string)

            # tokenized data
            writer.add_document(
                STR_ID=str(row.iloc[0]),
                **docs,
            )
        writer.commit()

    def add(self, str_id: str, source: str, target: str, source_lang: str, target_lang: str):
        # if str_id in ix, update, else add
        with self.ix.writer() as writer:
            writer.update_document(
                STR_ID=str_id,
                **{source_lang: tokenize(source), target_lang: tokenize(target)},
            )

    def search_tm(self, text: str, source_lang: str, target_lang: str, limit=5) -> Dict[str, str]:
        if source_lang not in self.langs:
            source_lang = langcodes.closest_supported_match(source_lang, self.langs)
        if target_lang not in self.langs:
            target_lang = langcodes.closest_supported_match(target_lang, self.langs)

        if not source_lang or not target_lang:
            return {}

        with self.ix.searcher() as searcher:
            tokens = tokenize(text)
            query = QueryParser(source_lang, self.ix.schema, group=OrGroup).parse(tokens)
            results = searcher.search(query, limit=limit)
            if len(results) == 0:
                return {}

            result = {detokenize(result[source_lang]): detokenize(result[target_lang]) for result in results}

        result = {k: v for k, v in result.items() if k in text}
        return result
