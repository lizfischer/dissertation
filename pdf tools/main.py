import image_generation
import find_gaps
import tesseract_horizontalSpace
import dump_to_txt
from whitespaceHelpers import test_thresholds


def process_pdf(input_file):
    pdf_im = image_generation.export_pdf_images(input_file)
    binary_images = image_generation.export_binary_images(pdf_im)
    margins = find_gaps.find_gaps(binary_images)
    ocr = tesseract_horizontalSpace.do_recognize(margins)
    dump_to_txt.save_txt(ocr)


def test_mode(input_file):
    pdf_im = image_generation.export_pdf_images(input_file)
    binary_images = image_generation.export_binary_images(pdf_im)
    test_thresholds(binary_images)


if __name__ == "__main__":
    pdf = "input/swinfield.pdf"
    process_pdf(pdf)
