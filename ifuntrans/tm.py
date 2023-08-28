"""Translation Memory"""
import pathlib
from functools import cache
from typing import Tuple

import pandas
from whoosh.fields import ID, TEXT, Schema
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import OrGroup, QueryParser

from ifuntrans.tokenizer import detokenize, tokenize


@cache
def get_index_path():
    # return (pathlib.Path(__file__).parent.parent / ".index").resolve().as_posix()
    return ":memory:"


@cache
def get_tm_path():
    return (pathlib.Path(__file__).parent.parent / "assets" / "tm.xlsx").resolve().as_posix()


def init_tm_indexing():
    global IX
    tm_df = pandas.read_excel(get_tm_path())

    # skip first two rows
    tm_df = tm_df.iloc[1:]

    langs = tm_df.columns[1:].tolist()
    columns = {lang: TEXT(stored=True) for lang in langs}
    schema = Schema(
        STR_ID=ID(stored=True),
        **columns,
    )

    st = RamStorage()
    IX = st.create_index(
        schema,
    )

    writer = IX.writer()
    for _, row in tm_df.iterrows():
        docs = {}
        for lang in langs:
            string = str(row[lang])
            docs[lang] = tokenize(string)

        # tokenized data
        writer.add_document(
            STR_ID=str(row.iloc[0]),
            **docs,
        )
    writer.commit()


def search_tm(text: str, source_lang: str, target_lang: str, limit=1) -> Tuple[str, str]:
    with IX.searcher() as searcher:
        tokens = tokenize(text)
        query = QueryParser(source_lang, IX.schema, group=OrGroup).parse(tokens)
        results = searcher.search(query, limit=limit)
        if len(results) == 0:
            return "", ""
        searched_source = detokenize(results[0][source_lang])
        searched_target = detokenize(results[0][target_lang])
        return searched_source, searched_target


init_tm_indexing()
