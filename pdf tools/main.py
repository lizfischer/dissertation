import image_generation
import find_gaps
import tesseract
import dump_to_txt
from whitespaceHelpers import test_thresholds
import split_pages


def process_pdf(input_file):
    pdf_im = image_generation.export_pdf_images(input_file)
    binary_images = image_generation.export_binary_images(pdf_im, cleanup=True)
    margins = find_gaps.find_gaps(binary_images)
    ocr = tesseract.do_recognize(margins)
    dump_to_txt.save_txt(ocr)


def test_mode(input_file):
    pdf_im = image_generation.export_pdf_images(input_file)
    binary_images = image_generation.export_binary_images(pdf_im)
    test_thresholds(binary_images)


def new_process_pdf(input_file_name, splitPages):
    working_file_name = input_file_name
    # Step One - Do pages need to be split apart?
    if splitPages:
        PAGE_SPLIT_POINT = 0.5
        working_file_name = split_pages.split_pdf(working_file_name, PAGE_SPLIT_POINT)

    # Step Two - Generate Images from PDF
    pdf_image_directory = image_generation.export_pdf_images(working_file_name)

    # Step Three - Binarize Images
    binary_image_directory = image_generation.export_binary_images(pdf_image_directory, cleanup=False)

    # Step Four - Find Margins
    margins = find_gaps.find_gaps(binary_image_directory) #TODO more generalization needed here


if __name__ == "__main__":
    pdf = "testfiles/sample.pdf"
    new_process_pdf(pdf, True)
