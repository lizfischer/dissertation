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

    images = os.listdir(in_dir)

    for i in tqdm(range(len(images))):
        img = cv2.imread(f'{in_dir}/{images[i]}', cv2.IMREAD_GRAYSCALE)
        (thresh, im_bw) = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)

        cv2.imwrite(f"{output_dir}/{images[i].replace('.jpg', '.tiff')}", im_bw)
    if cleanup:
        shutil.rmtree(in_dir)
    return output_dir


def export_pdf_images(input_file, project_id):
    print("\n*** Converting PDF to images... ****")

    output_dir = f"interface/static/projects/{project_id}/pdf_images"

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
    export_binary_images("interface/static/projects/trillek/pdf_images")
