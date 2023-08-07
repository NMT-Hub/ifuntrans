import argparse

import ifuntrans.api.localization as localization


def main():
    parser = argparse.ArgumentParser(description="Translate excel file")
    parser.add_argument("file", help="The excel file to translate")
    parser.add_argument("output", help="The output file")
    parser.add_argument(
        "--languages", help="The languages to translate to", default="en,zh-TW,id,vi,th,pt-BR,ja,ko,ar,tr"
    )
    args = parser.parse_args()
    localization.translate_excel(args.file, args.output, args.languages)


if __name__ == "__main__":
    main()
