import os
import sys
import glob
import pandas as pd


def merge(indir, outfile):
    os.chdir(indir)
    extension = 'csv'
    all_filenames = [i for i in glob.glob('*.{}'.format(extension))]

    #combine all files in the list
    combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames ])
    #export to csv
    combined_csv.to_csv(outfile, index=False, encoding='utf-8-sig')


def main():
    print((sys.argv[1]))
    if len(sys.argv) < 3:
        print("Usage: python combine_csvs.py [directory to merge] [name of merged file]")
        return

    indir = sys.argv[1]
    outfile = sys.argv[2]
    merge(indir, outfile)


if __name__ == '__main__':
    main()