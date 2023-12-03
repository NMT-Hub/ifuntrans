import argparse
import asyncio
import warnings
from typing import List

import langcodes
import openpyxl
import pandas as pd

from ifuntrans.async_translators.chatgpt import normalize_language_code_as_iso639
from ifuntrans.translate import translate


def get_sheet_names(file_path):
    wb = openpyxl.load_workbook(file_path)
    return wb.sheetnames


def copy_format(source_cell, target_cell):
    """Copy the formatting from the source cell to the target cell."""
    if source_cell.has_style:
        target_cell.font = source_cell.font.copy()
        target_cell.border = source_cell.border.copy()
        target_cell.fill = source_cell.fill.copy()
        target_cell.number_format = source_cell.number_format
        target_cell.protection = source_cell.protection.copy()
        target_cell.alignment = source_cell.alignment.copy()


async def main():
    parser = argparse.ArgumentParser(description="Translate excel file")
    parser.add_argument("file", help="The excel file to translate")
    parser.add_argument("output", help="The output file")
    parser.add_argument("-tm", "--translate-memory-file", help="The translate memory file", default=None, type=str)

    args = parser.parse_args()

    sheet_names = get_sheet_names(args.file)

    sheet_2_dataframes = {}
    for sheet_name in sheet_names:
        # incase "None" replace by pd.NA
        dataframe = pd.read_excel(args.file, sheet_name=sheet_name, keep_default_na=False)
        # convert all columns to string
        dataframe = dataframe.astype(str)
        # apply str.strip to all columns
        dataframe = dataframe.apply(lambda x: x.str.strip())
        # manually replace "" with pd.NA
        dataframe.replace("", pd.NA, inplace=True)
        columns = dataframe.columns

        # normalize the language code
        iso_codes = await normalize_language_code_as_iso639(columns)
        columns_2_langcodes = {}
        for column, code in zip(columns, iso_codes):
            if code == "und":
                continue
            columns_2_langcodes[column] = code
        langcodes_2_columns = {v: k for k, v in columns_2_langcodes.items()}

        # find the most common language code. more specifically, "zh" and "en"
        # zh and en will translate to each other
        # the others will be translated from these two languages
        try:
            zh_lang_code = langcodes.closest_supported_match("zh", langcodes_2_columns.keys())
            zh_column = langcodes_2_columns[zh_lang_code]
        except KeyError:
            warnings.warn(f"No Chinese column found in sheet {sheet_name}. Skip this sheet")
            continue

        try:
            en_lang_code = langcodes.closest_supported_match("en", langcodes_2_columns.keys())
            en_column = langcodes_2_columns[en_lang_code]
        except KeyError:
            warnings.warn(f"No English column found in sheet {sheet_name}. Skip this sheet")
            continue
        # select rows that zh_column is empty and en_column is not empty
        # these rows will be translated from English to Chinese
        zh_empty_rows = dataframe[dataframe[zh_column].isnull() & dataframe[en_column].notnull()]
        zh_empty_rows_en_translation: List[str] = await translate(
            zh_empty_rows[en_column].tolist(),
            from_lang="en",
            to_lang="zh",
            tm=None,
        )
        dataframe.loc[zh_empty_rows.index, zh_column] = zh_empty_rows_en_translation

        # slecet rows that en_column is empty and zh_column is not empty
        # these rows will be translated from Chinese to English
        dataframe[dataframe[en_column].isnull() & dataframe[zh_column].notnull()]
        en_empty_rows = dataframe[dataframe[en_column].isnull() & dataframe[zh_column].notnull()]
        en_empty_rows_zh_translation: List[str] = await translate(
            en_empty_rows[zh_column].tolist(),
            from_lang="zh",
            to_lang="en",
            tm=None,
        )
        dataframe.loc[en_empty_rows.index, en_column] = en_empty_rows_zh_translation

        for column in columns_2_langcodes.keys():
            if column in [zh_column, en_column]:
                continue
            lang_code = columns_2_langcodes[column]

            if langcodes.get(lang_code).language in ["zh", "ja", "ko"]:
                # for cjk languages, we translate from Chinese
                empty_rows = dataframe[dataframe[column].isnull()]
                empty_rows_zh_translation: List[str] = await translate(
                    empty_rows[zh_column].tolist(),
                    from_lang="zh",
                    to_lang=lang_code,
                    tm=None,
                )
                dataframe.loc[empty_rows.index, column] = empty_rows_zh_translation
            else:
                # for other languages, we translate from English
                empty_rows = dataframe[dataframe[column].isnull()]
                empty_rows_en_translation: List[str] = await translate(
                    empty_rows[en_column].tolist(),
                    from_lang="en",
                    to_lang=lang_code,
                    tm=None,
                )
                dataframe.loc[empty_rows.index, column] = empty_rows_en_translation

        sheet_2_dataframes[sheet_name] = dataframe

    with pd.ExcelWriter(args.output) as writer:
        for sheet_name, dataframe in sheet_2_dataframes.items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)


if __name__ == "__main__":
    asyncio.run(main())
