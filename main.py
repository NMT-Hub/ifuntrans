import argparse
import asyncio

import ifuntrans.api.localization as localization


async def main():
    parser = argparse.ArgumentParser(description="Translate excel file")
    parser.add_argument("file", help="The excel file to translate")
    parser.add_argument("output", help="The output file")
    parser.add_argument(
        "--languages", help="The languages to translate to", default="en,zh-TW,id,vi,th,pt-BR,ja,ko,ar,tr"
    )
    parser.add_argument("--source-column", help="The source column", default=1, type=int)
    args = parser.parse_args()

    await localization.translate_excel(args.file, args.output, args.languages, source_column=args.source_column)


if __name__ == "__main__":
    asyncio.run(main())
