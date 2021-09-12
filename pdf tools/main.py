import image_generation
import find_gaps
import tesseract_horizontalSpace
import dump_to_txt


input_file = "input/trillek.pdf"
# pdf_im = image_generation.export_pdf_images(input_file)
pdf_im = "outputs/br/trillek/pdf_images"
# binary_images = image_generation.export_binary_images(pdf_im)
binary_images = "outputs/br/trillek/binary_images"
# margins = find_gaps.find_gaps(binary_images)
margins = "outputs/br/trillek/whitespace.json"
ocr = tesseract_horizontalSpace.do_recognize(margins)
dump_to_txt.save_txt(ocr)
