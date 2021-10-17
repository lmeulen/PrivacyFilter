import argparse
import pandas as pd
from PrivacyFilter import PrivacyFilter


def main(args):
    print("Opening input file:")
    df = pd.read_csv(args.input, sep=';', encoding="ISO-8859-1")
    columnName = df.columns[args.column]
    print('  Filename         : ' + args.input)
    print('  Column to filter : ' + columnName)
    print('  Rows             : ' + str(len(df)))

    print("Initializing filter")
    pfilter_nlp = PrivacyFilter()
    pfilter_nlp.initialize(clean_accents=True, nlp_filter=True, wordlist_filter=True)

    print("Applying filter")
    df[columnName] = df.apply(lambda row: pfilter_nlp.filter(row[columnName]), axis=1)

    print("Saving output file")
    print('  Filename         : ' + args.output)
    df.to_csv(args.output, sep=';', encoding="ISO-8859-1", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, required=True, help='Input filename')
    parser.add_argument('--output', '-o', type=str, required=True, help='Output filename')
    parser.add_argument('--column', '-c', type=int, required=True, help='Column number')
    main(parser.parse_args())
