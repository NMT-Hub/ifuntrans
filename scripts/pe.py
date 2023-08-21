# Merge worksheet from multiple Excel files into one Excel file

import argparse
import re

import langcodes
import pandas

from ifuntrans.pe import hardcode_post_edit, tokenizer

RE_NORMALIZED_NUMBER = r"-?\d{1,3}(?:,\d{3})*"


def _prefix_group_func(row):
    string = row.iloc[1]
    string = re.sub(r"\d+", "", string)
    string = re.sub(r"\s+", "", string)
    row.iloc[0] = tokenizer.decode(tokenizer.encode(string)[:3])
    return row


def _suffix_group_func(row):
    string = row.iloc[1]
    string = re.sub(r"\d+", "", string)
    string = re.sub(r"\s+", "", string)
    row.iloc[0] = tokenizer.decode(tokenizer.encode(string)[-3:])
    return row


def _duplicate_group_func(row):
    string = row.iloc[1]
    string = re.sub(RE_NORMALIZED_NUMBER, "xxx", string)
    row.iloc[0] = string
    return row


def pe(input_file, output_file):
    # Read input file
    df = pandas.read_excel(input_file, sheet_name=None)
    main_sheet = df["Translation Summary"]

    for sheet_name, sheet_df in df.items():
        if sheet_name == "Translation Summary":
            continue
        if "Taiwan" in sheet_name:
            continue
        columns = sheet_df.columns
        src_lang_name = columns[1]
        src_lang = langcodes.find(src_lang_name).language
        tgt_lang = langcodes.find(sheet_name).language

        results = hardcode_post_edit(sheet_df[columns[1]].tolist(), sheet_df[columns[-1]].tolist(), src_lang, tgt_lang)
        sheet_df["Hardcode PE"] = results
        main_sheet[sheet_name].update(sheet_df["Hardcode PE"])

        # # group by id
        # sheet_df["ChatGPT Fix Consistency"] = None
        # group_prefix = sheet_df.apply(_prefix_group_func, axis=1).groupby(columns[0])
        # group_suffix = sheet_df.apply(_suffix_group_func, axis=1).groupby(columns[0])
        # for _, group_df in chain(group_prefix, group_suffix):
        #     if group_df.shape[0] < 10:
        #         continue

        #     prev_result = group_df[columns[-1]].tolist()
        #     group_results = chatgpt_doc_translate(
        #         group_df[columns[1]].tolist(), prev_result, src_lang, tgt_lang
        #     )

        #     group_df["ChatGPT Fix Consistency"] = group_results
        #     sheet_df.update(group_df, overwrite=False)

        # main_sheet[sheet_name].update(sheet_df["ChatGPT Fix Consistency"])

        # group by duplicate
        sheet_df["HardCoding Fix Consistency"] = None
        group_duplicate = sheet_df.apply(_duplicate_group_func, axis=1).groupby(columns[0])
        for _, group_df in group_duplicate:
            if group_df.shape[0] < 2:
                continue
            template = group_df.iloc[0]
            template_tgt = template[-2]

            fixed = []
            for _, row in group_df.iterrows():
                src = row[1]
                all_nums = re.findall(RE_NORMALIZED_NUMBER, src)

                i = 0

                def _duplicate_replace_func(obj):
                    nonlocal i
                    i += 1
                    try:
                        num = all_nums[i - 1]
                    except IndexError:
                        num = obj.group(0)
                    try:
                        num = int(num)
                        num = f"{num:,}"
                    except ValueError:
                        pass
                    return num

                fixed.append(re.sub(RE_NORMALIZED_NUMBER, _duplicate_replace_func, template_tgt))

            group_df["HardCoding Fix Consistency"] = fixed
            sheet_df.update(group_df, overwrite=False)

        main_sheet[sheet_name].update(sheet_df["HardCoding Fix Consistency"])

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
