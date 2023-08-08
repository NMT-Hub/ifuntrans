# Merge worksheet from multiple Excel files into one Excel file

import argparse

import pandas


def merge_excel_files(input_files, output_file):
    """
    Merge worksheet from multiple Excel files into one Excel file
    :param input_files: list of input files
    :param output_file: output file
    :return: None
    """
    # Read all worksheets from input files
    all_worksheets = {}
    for input_file in input_files:
        with pandas.ExcelFile(input_file) as reader:
            for worksheet_name in reader.sheet_names:
                if worksheet_name in all_worksheets:
                    continue
                all_worksheets[worksheet_name] = pandas.read_excel(reader, worksheet_name)

    # Write all worksheets to output file with sheet name
    with pandas.ExcelWriter(output_file) as writer:
        for worksheet_name, worksheet in all_worksheets.items():
            worksheet.to_excel(writer, worksheet_name, index=False)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Merge worksheet from multiple Excel files into one Excel file")
    parser.add_argument("input_files", nargs="+", help="input files")
    parser.add_argument("output_file", help="output file")
    args = parser.parse_args()

    # Merge worksheet from multiple Excel files into one Excel file
    merge_excel_files(args.input_files, args.output_file)


if __name__ == "__main__":
    main()
