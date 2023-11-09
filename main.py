import argparse
import asyncio
import tempfile
import warnings

import openpyxl

import ifuntrans.api.localization as localization


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
    parser.add_argument(
        "--languages", help="The languages to translate to", default="en,zh-TW,id,vi,th,pt-BR,ja,ko,ar,tr"
    )
    parser.add_argument("--source-column", help="The source column", default=1, type=int)
    parser.add_argument("--sheet-names", nargs="*", help="The sheet names", default=None, type=str)
    parser.add_argument("-tm", "--translate-memory-file", help="The translate memory file", default=None, type=str)

    args = parser.parse_args()

    all_sheet_names = get_sheet_names(args.file)
    if not args.sheet_names:
        sheet_names = all_sheet_names
    else:
        sheet_names = args.sheet_names

    with tempfile.TemporaryDirectory() as tmpdir:
        for sheet_name in sheet_names:
            temp_file = f"{tmpdir}/{sheet_name}.xlsx"
            if sheet_name not in all_sheet_names:
                warnings.warn(f"Sheet name {sheet_name} not found in excel file {args.file}")
                continue
            await localization.translate_excel(
                args.file,
                temp_file,
                args.languages,
                source_column=args.source_column,
                sheet_name=sheet_name,
                tm_file=args.translate_memory_file,
            )

        workbook = openpyxl.load_workbook(args.file)
        for sheet_name in sheet_names:
            if sheet_name not in all_sheet_names:
                continue
            sheet = workbook[sheet_name]
            temp_file = f"{tmpdir}/{sheet_name}.xlsx"
            temp_workbook = openpyxl.load_workbook(temp_file)
            temp_sheet = temp_workbook.active

            # copy the translated content to the original workbook, and keep the formatting
            # only copy the translated column
            for i in range(1, sheet.max_row + 1):
                format_template_cell = sheet.cell(row=i, column=sheet.max_column)
                for j in range(sheet.max_column + 1, temp_sheet.max_column + 1):
                    source_cell = temp_sheet.cell(row=i, column=j)
                    target_cell = sheet.cell(row=i, column=j)
                    target_cell.value = source_cell.value
                    copy_format(format_template_cell, target_cell)

            temp_workbook.close()

        workbook.save(args.output)


if __name__ == "__main__":
    asyncio.run(main())
