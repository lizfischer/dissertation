import copy
import os, pathlib
import sys
import PyPDF2
from interface import app
import cv2

def split_images(project_id, split_pct=.5):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
    pdf_images = os.path.join(project_folder, "pdf_images")
    split_folder = os.path.join(project_folder, "split_images")

    if not os.path.exists(split_folder):
        os.mkdir(split_folder)

    for file in os.listdir(pdf_images):
        path = os.path.join(pdf_images, file)
        name = pathlib.Path(path).stem
        print(path)
        # Read the image
        img = cv2.imread(path)
        print(img.shape)
        height = img.shape[0]
        width = img.shape[1]

        # Cut the image in half
        width_cutoff = int(width * split_pct)
        s1 = img[:, :width_cutoff]
        s2 = img[:, width_cutoff:]

        a_half = os.path.join(split_folder, file.replace(name, name+"-a"))
        b_half = os.path.join(split_folder, file.replace(name, name+"-b"))
        cv2.imwrite(a_half, s1)
        cv2.imwrite(b_half, s2)
    return split_folder

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
