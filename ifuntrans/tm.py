"""Translation Memory"""
import pathlib
from typing import List, Optional, Tuple

import langcodes
import pandas
from whoosh.fields import ID, TEXT, Schema
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import OrGroup, QueryParser

from ifuntrans.tokenizer import detokenize, tokenize

DEFAULT_TM_PATH = (pathlib.Path(__file__).parent.parent / "assets" / "tm.xlsx").resolve().as_posix()


class TranslationMemory(object):
    @property
    def index_path(self):
        # return (pathlib.Path(__file__).parent.parent / ".index").resolve().as_posix()
        return ":memory:"

    def __init__(self, langs: List[str], tm_path: Optional[str] = None):
        self.tm_path = tm_path
        self.langs = langs

        columns = {lang: TEXT(stored=True) for lang in langs}
        schema = Schema(
            STR_ID=ID(stored=True),
            **columns,
        )

        st = RamStorage()
        self.ix = st.create_index(
            schema,
        )

        if not self.tm_path:
            return

        tm_df = (
            pandas.read_excel(self.tm_path, engine="openpyxl")
            .fillna("")
            .astype(str)
            .drop_duplicates()
            .applymap(str.lower)
        )
        columns = tm_df.columns.tolist()

        writer = self.ix.writer()
        for _, row in tm_df.iterrows():
            docs = {}
            for lang in langs:
                string = row[lang]
                docs[lang] = tokenize(string)

            # tokenized data
            writer.add_document(
                STR_ID=str(row.iloc[0]),
                **docs,
            )
        writer.commit()

    def add(self, str_id: str, source: str, target: str, source_lang: str, target_lang: str):
        source = source.lower()
        target = target.lower()

        # if str_id in ix, update, else add
        with self.ix.writer() as writer:
            writer.update_document(
                STR_ID=str_id,
                **{source_lang: tokenize(source), target_lang: tokenize(target)},
            )

    def search_tm(self, text: str, source_lang: str, target_lang: str, limit=1) -> Tuple[str, str]:
        if source_lang not in self.langs:
            source_lang = langcodes.closest_supported_match(source_lang, self.langs)
        if target_lang not in self.langs:
            target_lang = langcodes.closest_supported_match(target_lang, self.langs)

        if not source_lang or not target_lang:
            return "", ""

        with self.ix.searcher() as searcher:
            tokens = tokenize(text)
            query = QueryParser(source_lang, self.ix.schema, group=OrGroup).parse(tokens)
            results = searcher.search(query, limit=limit)
            if len(results) == 0:
                return "", ""
            searched_source = detokenize(results[0][source_lang])
            searched_target = detokenize(results[0][target_lang])
            return searched_source, searched_target
