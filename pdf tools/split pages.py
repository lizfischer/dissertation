import copy
import sys, os
from PyPDF2 import PdfFileReader, PdfFileWriter


def splitPages(file):
    file_name = file.split('/')
    file_name = file_name[len(file_name)-1].split('.')[0]
    print(file_name)
    with open(file, "rb") as infile:
        pdfIn = PdfFileReader(infile)
        pdfOut = PdfFileWriter()

        numPages = pdfIn.getNumPages()

        for i in range(numPages):
            pageLeft = pdfIn.getPage(i)
            pageRight = copy.copy(pageLeft)

            w = pageLeft.mediaBox[2]
            h = pageLeft.mediaBox[3]

            pageLeft.cropBox.lowerLeft = (0, h)
            pageLeft.cropBox.upperRight = (w / 2, 0)
            pdfOut.addPage(pageLeft)

            pageRight.cropBox.lowerLeft = (w/2, h)
            pageRight.cropBox.upperRight = (w, 0)
            pdfOut.addPage(pageRight)

        with open(f"outputs/{file_name}_split.pdf", "wb") as outfile:
            pdfOut.write(outfile)


def main():
    args = sys.argv
    print(args)
    #splitPages("input/Pforzheimer_Vol3.pdf")


if __name__ == '__main__':
     main()
