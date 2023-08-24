"""Translation Memory"""
import os
import pathlib
import shutil
from functools import cache
from typing import Annotated, List

import fastapi
import langcodes
import pandas
from whoosh.fields import ID, TEXT, Schema
from whoosh.index import create_in, open_dir
from whoosh.qparser import OrGroup, QueryParser


@cache
def get_index_path():
    return (pathlib.Path(__file__).parent.parent / ".index").resolve().as_posix()


@cache
def get_tm_path():
    return (pathlib.Path(__file__).parent.parent / "assets" / "tm.xlsx").resolve().as_posix()


def init_tm_indexing(force_reload=False):
    global IX
    if os.path.exists(get_index_path()) and not force_reload:
        IX = open_dir(get_index_path())
        return IX

    if force_reload:
        shutil.rmtree(get_index_path(), ignore_errors=True)

    tm_df = pandas.read_excel(get_tm_path())

    # skip first two rows
    tm_df = tm_df.iloc[1:]

    langs = tm_df.columns[1:].tolist()

    columns = {}
    for lang in langs:
        try:
            lang_code = langcodes.find_name("language", lang, "zh")
        except:
            continue
        columns[lang_code.language] = TEXT(stored=True)

    os.makedirs(os.path.dirname(get_index_path()), exist_ok=True)
    schema = Schema(
        id=ID(stored=True),
        **columns,
    )
    os.mkdir(get_index_path())
    IX = create_in(
        get_index_path(),
        schema,
    )

    writer = IX.writer()
    for _, row in tm_df.iterrows():
        import ipdb; ipdb.set_trace()
        writer.add_document(
            id=str(row.iloc[0]),
            **{lang_code: row[lang] for lang, lang_code in columns.items()},
        )

    writer.commit()


def delete_semantic_words(
    group_ids: Annotated[
        List[str],
        fastapi.Body(..., embed=True, example=["1677149648288296961", "1677149648288296962"]),
    ],
):
    writer = IX.writer()
    for group_id in group_ids:
        writer.delete_by_term("group_id", group_id)
    writer.commit()


def match_semantic_words(
    context: Annotated[str, fastapi.Body(..., embed=True, example="我要投诉")],
):
    with IX.searcher() as searcher:
        # query = jieba.lcut(context)
        query = " OR ".join(query)
        parser = QueryParser("content", IX.schema, group=OrGroup)
        query = parser.parse(query)
        results = searcher.search(query, limit=10)
