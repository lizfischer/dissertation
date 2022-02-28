import copy
import sys, os
from PyPDF2 import PdfFileReader, PdfFileWriter


def split_pdf(file, out_dir, splitPCT=.5):
    with open(file, "rb") as infile:
        pdfIn = PdfFileReader(infile)
        pdfOut = PdfFileWriter()

        numPages = pdfIn.getNumPages()

        for i in range(numPages):
            pageLeft = pdfIn.getPage(i)
            pageRight = copy.copy(pageLeft)

            w = float(pageLeft.mediaBox[2])
            h = float(pageLeft.mediaBox[3])

            pageLeft.cropBox.lowerLeft = (0, h)
            pageLeft.cropBox.upperRight = (w * splitPCT, 0)
            pdfOut.addPage(pageLeft)

            pageRight.cropBox.lowerLeft = (w * splitPCT, h)
            pageRight.cropBox.upperRight = (w, 0)
            pdfOut.addPage(pageRight)

        file_name = os.path.basename(file).split('.')[0]
        outfile_name = f"{file_name}_split.pdf"
        outfile_full = os.path.join(out_dir, outfile_name)

        with open(outfile_full, "wb") as outfile:
            pdfOut.write(outfile)
            return outfile_full, outfile_name


def main():
    args = sys.argv
    print(args)
    #splitPages("input/Pforzheimer_Vol3.pdf")


if __name__ == '__main__':
     main()
