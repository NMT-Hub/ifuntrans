import argparse
import asyncio
import warnings
from typing import List

import langcodes
import openpyxl
import pandas as pd
from openpyxl.styles import Font

from ifuntrans.async_translators.chatgpt import normalize_language_code_as_iso639
from ifuntrans.tm import create_tm_from_excel
from ifuntrans.translate import translate


async def main():
    parser = argparse.ArgumentParser(description="Translate excel file")
    parser.add_argument("file", help="The excel file to translate")
    parser.add_argument("--output", help="The output file", default=None, type=str)
    parser.add_argument("-l", "--language", nargs="+", help="The additional languages to translate to", default=[])
    parser.add_argument("-tm", "--translate-memory-file", help="The translate memory file", default=None, type=str)

    args = parser.parse_args()
    if args.translate_memory_file is not None:
        tm = await create_tm_from_excel(args.translate_memory_file)
    else:
        tm = None

    if args.output is None:
        args.output = args.file

    workbook = openpyxl.load_workbook(args.file)
    sheet_names = workbook.sheetnames

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
        dataframe.replace("nan", pd.NA, inplace=True)
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
            tm=tm,
        )
        dataframe.loc[en_empty_rows.index, en_column] = en_empty_rows_zh_translation

        for column in columns_2_langcodes.keys():
            if column in [zh_column, en_column]:
                continue
            lang_code = columns_2_langcodes[column]

            if langcodes.get(lang_code).language in ["zh", "ja", "ko"]:
                # for cjk languages, we translate from Chinese
                empty_rows = dataframe[dataframe[column].isnull() & dataframe[zh_column].notnull()]
                empty_rows_zh_translation: List[str] = await translate(
                    empty_rows[zh_column].tolist(),
                    from_lang="zh",
                    to_lang=lang_code,
                    tm=tm,
                )
                dataframe.loc[empty_rows.index, column] = empty_rows_zh_translation
            else:
                # for other languages, we translate from English
                empty_rows = dataframe[dataframe[column].isnull() & dataframe[en_column].notnull()]
                empty_rows_en_translation: List[str] = await translate(
                    empty_rows[en_column].tolist(),
                    from_lang="en",
                    to_lang=lang_code,
                    tm=tm,
                )
                dataframe.loc[empty_rows.index, column] = empty_rows_en_translation

        sheet_2_dataframes[sheet_name] = dataframe

    for sheet_name, dataframe in sheet_2_dataframes.items():
        ws = workbook[sheet_name]
        dataframe = sheet_2_dataframes[sheet_name]
        # Update the localization workbook
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None:
                    try:
                        cell.value = dataframe.iloc[cell.row - 2, cell.column - 1]
                    except (IndexError, ValueError):
                        continue
                    cell.font = Font(color="FF0000")
    workbook.save(args.output)


if __name__ == "__main__":
    asyncio.run(main())
