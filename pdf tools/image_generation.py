import pdf2image
import os
import shutil
import cv2
from tqdm import tqdm


def export_binary_images(in_dir, cleanup=False):
    print("\n*** Binarizing images... ***")
    output_dir = in_dir.replace("pdf_images", "binary_images")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    imgs = os.listdir(in_dir)

    for i in tqdm(range(len(imgs))):
        img = cv2.imread(f'{in_dir}/{imgs[i]}', cv2.IMREAD_GRAYSCALE)
        (thresh, im_bw) = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)

        cv2.imwrite(f"{output_dir}/{imgs[i].replace('.jpg', '.tiff')}", im_bw)
    if cleanup:
        shutil.rmtree(in_dir)
    return output_dir


def export_pdf_images(input_file):
    print("\n*** Converting PDF to images... ****")

    name = input_file.split_pdf("/")[-1].replace(".pdf", "")
    output_dir = f"projects/{name}/pdf_images"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pil_images = pdf2image.convert_from_path(input_file, use_cropbox=True, thread_count=5)

    i = 1
    print("*** Saving images... ***")
    for image in tqdm(pil_images):
        image.save(f"{output_dir}/{i}.jpg")
        i += 1
    return output_dir


if __name__ == "__main__":
    INPUT_FILE = "input/trillek.pdf"
    # pdf_im = export_pdf_images(INPUT_FILE)
    export_binary_images("projects/trillek/pdf_images")

