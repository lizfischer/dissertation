import numpy as np
import json
import os
import sys
from tqdm import tqdm
import cv2
import whitespaceHelpers as ws
np.set_printoptions(threshold=sys.maxsize)

BLANKNESS_THRESHOLD = 0.1
WIDTH_THRESHOLD = 70


def write_output(df, output_dir):
    s = sorted(df, key=lambda x: x["p"])
    f = f"{OUTPUT_DIR}/whitespace.json"
    with open(f, "w") as outfile:
        json.dump(s, outfile, indent=4)
    return f


def process_page(im_path, viz=False):
    page_num = int(im_path.split('/')[-1].replace(".tiff", ""))
    img, img_binary = ws.get_binary_image(im_path)
    try:
        top = int(ws.find_top(img_binary))
        horizontal_gaps = ws.find_horizontal_gaps(img_binary, width_thresh=WIDTH_THRESHOLD)
        vertical_gaps = ws.find_vertical_gaps(img_binary, width_thresh=10, blank_thresh=0.05)
        # TODO: threshold
    except IndexError:  # QUESTION: When wa1s this erroring out?
        horizontal_gaps = []
        vertical_gaps = []
    except ValueError:
        raise

    if viz:
        ws.visualize(img_binary, horizontal_gaps, vertical_gaps)

    return {"p": page_num, "image": im_path, "left_margin": int(vertical_gaps[0]), "gaps": horizontal_gaps}


def find_gaps(image_dir):
    print("\n*** Detecting margins & whitespace... ***")
    output_dir = "/".join(image_dir.split("/")[:-1])

    imgs = os.listdir(image_dir)
    all_data = []
    for im in tqdm(imgs):
        i = int(im.split('.')[0])
        image_path = f"{image_dir}/{im}"
        try:
            data = process_page(image_path)
        except ValueError:
            continue
        all_data.append(data)
        if i % 20 == 0:
            write_output(all_data, output_dir)

    return write_output(all_data, output_dir)



OUTPUT_DIR = "outputs/br/trillek"
IMAGE_DIR = f"binary_images/br"

if __name__ == "__main__":
    find_gaps(IMAGE_DIR)
