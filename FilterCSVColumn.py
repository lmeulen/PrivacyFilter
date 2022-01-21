import argparse
import os
import pandas as pd
from PrivacyFilter import PrivacyFilter


def parse_csv_file(inputfile, outputfile, columns, privacyfilter, seperator=';'):
    print("Opening input file:")
    print('  Filename         : ' + inputfile)
    df = pd.read_csv(inputfile, sep=seperator, encoding="ISO-8859-1")  # , usecols=[0, 1, 2, 3, 4, 5, 6])
    print('  Rows             : ' + str(len(df)))

    for column in columns:
        columnName = df.columns[column]
        print('  Column to filter : ' + columnName)
        print("    Applying filter")
        df[columnName] = df.apply(lambda row: privacyfilter.filter(str(row[columnName])), axis=1)
        print()

    print("Saving output file")
    print('  Filename         : ' + outputfile)
    df.to_csv(outputfile, sep=seperator, encoding="ISO-8859-1", index=False)


def main_file(inputfile, outputfile, columns):
    print("Initializing filter")
    pfilter_nlp = PrivacyFilter()
    pfilter_nlp.initialize(clean_accents=True, nlp_filter=True, wordlist_filter=True, regular_expressions=True)

    parse_csv_file(inputfile, outputfile, columns, pfilter_nlp)


def main_directory(directory, columns):
    print("Initializing filter")
    pfilter_nlp = PrivacyFilter()
    pfilter_nlp.initialize(clean_accents=True, nlp_filter=True, wordlist_filter=True, regular_expressions=True)

    if not os.path.isdir(directory):
        print('Please specify a directory as parameter')
        return

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                inputfile = os.path.join(directory, file)
                name, ext = os.path.splitext(file)
                outputfile = os.path.join(directory, name + '_filtered' + ext)
                parse_csv_file(inputfile, outputfile, columns, pfilter_nlp, seperator=',')
                print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, required=False, help='Input filename or directory')
    parser.add_argument('--output', '-o', type=str, required=False, help='Output filename')
    parser.add_argument('--directory', '-d', type=str, required=False, help='Input directory')
    parser.add_argument('--column', '-c', type=int, required=True, nargs="+",
                        help='Column number(s) seperated by space')
    args = parser.parse_args()
    print(args)
    if args.input and args.output:
        print('Parse file')
        main_file(args.input, args.output, args.column)
    elif args.directory:
        print('Parse directory')
        main_directory(args.directory, args.column)
    else:
        print('Specify input/output files or directory')
