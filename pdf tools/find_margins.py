import numpy as np
import json
import os
import sys
import cv2
from tqdm import tqdm
import whitespaceHelpers as ws
np.set_printoptions(threshold=sys.maxsize)

BLANKNESS_THRESHOLD = 0.02
IMAGE_DIR = "outputs/binary_images/br"
OUTPUT_DIR = "outputs/br"


def find_left(img_binary):
    n_rows, n_cols = img_binary.shape
    column_pcts = img_binary.sum(axis=0)/n_rows
    first_large_column = np.nonzero(column_pcts > BLANKNESS_THRESHOLD)[0][0]
    consecutive_zeroes = ws.find_consecutive_zeroes(column_pcts)
    return int(consecutive_zeroes[1][0]), int(first_large_column)


def visualize(image, top, left_char, left_margin):
    image[top, :] = 155
    image[:, left_char] = 155
    image[:, left_margin] = 155
    cv2.imshow("test", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def process_page(im_path, viz=False):
    num = int(im_path.split('/')[-1].split(".")[0])

    image = cv2.imread(im_path, cv2.IMREAD_GRAYSCALE)
    img_binary = cv2.bitwise_not(image)/255.0

    try:
        left_char, left_margin = find_left(img_binary)
        top = int(ws.find_top(img_binary))
        if left_char > left_margin:
            left_char = 0
    except IndexError:
        top = -1
        left_char = -1
        left_margin = -1

    if viz:
        visualize(image, top, left_char, left_margin)

    return {"p": num,
            "image": im_path, "left_char": left_char, "left_margin": left_margin, "top": top}


def find_margins(image_directory):
    print("\n*** Detecting margins & whitespace... ***")
    out_file = "/".join(image_directory.split("/")[:-1])+"/margins_out.json"
    images = os.listdir(image_directory)

    all_data = []
    for img in tqdm(images):
        image_path = f"{image_directory}/{img}"
        data = process_page(image_path)
        all_data.append(data)

    sorted_data = sorted(all_data, key=lambda x: x["p"])

    with open(out_file, "w") as o:
        json.dump(sorted_data, o, indent=4)

    return out_file


if __name__ == "__main__":
    find_margins(IMAGE_DIR)
