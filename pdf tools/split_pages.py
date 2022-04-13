import copy
import os
import sys
import PyPDF2


def split_pdf(file, out_dir, split_pct=.5):
    with open(file, "rb") as infile:
        pdf_in = PyPDF2.PdfFileReader(infile)
        pdf_out = PyPDF2.PdfFileWriter()

        numPages = pdf_in.getNumPages()

        for i in range(numPages):
            pageLeft = pdf_in.getPage(i)
            pageRight = copy.copy(pageLeft)

            w = float(pageLeft.mediaBox[2])
            h = float(pageLeft.mediaBox[3])

            pageLeft.cropBox.lowerLeft = (0, h)
            pageLeft.cropBox.upperRight = (w * split_pct, 0)
            pdf_out.addPage(pageLeft)

            pageRight.cropBox.lowerLeft = (w * split_pct, h)
            pageRight.cropBox.upperRight = (w, 0)
            pdf_out.addPage(pageRight)

        file_name = os.path.basename(file).split('.')[0]
        outfile_name = f"{file_name}_split.pdf"
        outfile_full = os.path.join(out_dir, outfile_name)

        with open(outfile_full, "wb") as outfile:
            pdf_out.write(outfile)
            return outfile_full, outfile_name


def main():
    args = sys.argv
    print(args)
    # split_pages_bool("input/Pforzheimer_Vol3.pdf")


if __name__ == '__main__':
    main()
