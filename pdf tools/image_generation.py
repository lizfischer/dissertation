import pdf2image
import os
import os, pathlib
import shutil
import cv2
from tqdm import tqdm

from models import Page


def split_images(project, split_pct=.5):
    pdf_images = project.get_image_dir()
    split_folder = input_folder

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

    info = pdf2image.pdfinfo_from_path(input_file, userpw=None, poppler_path=None)
    maxPages = info["Pages"]
    i = 1
    for page in range(1, maxPages + 1, 10):
        pil_images = pdf2image.convert_from_path(input_file, use_cropbox=True, dpi=200, first_page=page, last_page=min(page + 10 - 1, maxPages))
        print(f"*** Saving images {page}-{page+9}... ***")
        for image in tqdm(pil_images):
            image.save(f"{output_dir}/{i}.jpg")
            i += 1
    return output_dir


if __name__ == "__main__":
    INPUT_FILE = "input/trillek.pdf"
    # pdf_im = export_pdf_images(INPUT_FILE)
    export_binary_images("interface/static/projects/trillek/pdf_images")
