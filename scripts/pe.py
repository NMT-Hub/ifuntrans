# Merge worksheet from multiple Excel files into one Excel file

import argparse
import re

import langcodes
import pandas

from ifuntrans.pe import chatgpt_doc_translate, hardcode_post_edit


def _id_group_func(row):
    # replace all number by blank
    row["ID"] = re.sub(r"\d+", "", row["ID"])
    return row


def pe(input_file, output_file):
    # Read input file
    df = pandas.read_excel(input_file, sheet_name=None)
    main_sheet = df["Translation Summary"]

    for sheet_name, sheet_df in df.items():
        if sheet_name == "Translation Summary":
            continue
        columns = sheet_df.columns
        src_lang_name = columns[1]
        src_lang = langcodes.find(src_lang_name).language
        tgt_lang = langcodes.find(sheet_name).language

        results = hardcode_post_edit(sheet_df[columns[1]].tolist(), sheet_df[columns[2]].tolist(), src_lang, tgt_lang)
        df[sheet_name]["Hardcode PE"] = results

        # group by id
        group = sheet_df.apply(_id_group_func, axis=1).groupby("ID")
        for name, group_df in group:
            import ipdb

            ipdb.set_trace()

        results = chatgpt_doc_translate(sheet_df[columns[1]].tolist(), results, src_lang, tgt_lang)
        # df[sheet_name]["ChatGPT Fix Placeholder"] = results

        main_sheet[sheet_name] = results

    # Write output file
    with pandas.ExcelWriter(output_file, engine="openpyxl") as writer:
        for sheet_name, sheet_df in df.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Post Editing Translation")
    parser.add_argument("input_file", help="input file")
    parser.add_argument("output_file", help="output file")
    args = parser.parse_args()

    # Merge worksheet from multiple Excel files into one Excel file
    pe(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
