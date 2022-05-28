import mongoengine
import pdf2image
import os, pathlib
import shutil
import cv2
from tqdm import tqdm

from models import Page


def split_images(project, split_pct=.5):
    image_dir = project.get_image_dir()

    # Save original, un-split page data
    project.modify(original_pages=project.pages)
    project.modify(pull_all__pages=project.pages)

    seq = 1
    for page in project.original_pages:
        path = pathlib.Path(page.get_img())
        name = str(path.name)
        print(path)
        # Read the image
        img = cv2.imread(str(path))
        height = img.shape[0]
        width = img.shape[1]

        # Cut the image @ pct point
        width_cutoff = int(width * split_pct)
        a_img = img[:, :width_cutoff]
        b_img = img[:, width_cutoff:]

        new_a = f"{path.stem}-a{path.suffix}"
        new_b = f"{path.stem}-b{path.suffix}"
        cv2.imwrite(str(path).replace(name, new_a), a_img)
        cv2.imwrite(str(path).replace(name, new_b), b_img)

        a_half = Page(parent_id=project.id, sequence=seq, image=new_a)
        b_half = Page(parent_id=project.id, sequence=seq+1, image=new_b)

        project.pages.append(a_half)
        project.pages.append(b_half)
        project.save()

        seq += 2
    project.update(is_split=True)
    return True


def export_binary_images(project):
    print("\n*** Binarizing images... ***")
    image_dir = project.get_image_dir()

    for page in project.pages:
        img_path = page.get_img()
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        (thresh, im_bw) = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
        cv2.imwrite(img_path.replace('.jpg', '.tiff'), im_bw)
        page.height, page.width = img.shape
        project.save()

    project.modify(is_binarized=True)
    return True


def export_pdf_images(project):
    print("\n*** Converting PDF to images... ****")

    input_file = project.get_pdf()
    output_dir = project.get_image_dir()

    # Make images folder
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get pdf info
    info = pdf2image.pdfinfo_from_path(input_file, userpw=None, poppler_path=None)

    # Iterate pages, saving 10 at a time
    maxPages = info["Pages"]
    i = 1
    for page in range(1, maxPages + 1, 10):
        pil_images = pdf2image.convert_from_path(input_file, use_cropbox=True, dpi=200, first_page=page, last_page=min(page + 10 - 1, maxPages))
        print(f"*** Saving images {page}-{page+9}... ***")
        for image in tqdm(pil_images):
            # Save file to disk
            file_name = f"{i}.jpg"
            image_path = os.path.join(output_dir, file_name)
            image.save(image_path)
            # Save page to databse
            page = Page(parent_id=project.id, sequence=i, image=file_name)
            project.pages.append(page)
            project.save()
            i += 1
    return output_dir


if __name__ == "__main__":
    INPUT_FILE = "input/trillek.pdf"
    # pdf_im = export_pdf_images(INPUT_FILE)
    export_binary_images("interface/static/projects/trillek/pdf_images")
