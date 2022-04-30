import numpy as np
import json
import os
import sys
from tqdm import tqdm
import cv2
import whitespaceHelpers as ws
np.set_printoptions(threshold=sys.maxsize)


##
# Saves a dataframe to the given directory with the name "whitespace.json"
# Returns the file name
def write_output(df, output_dir, thresholds, thresholds_in_filename=False):
    sorted_pages = sorted(df, key=lambda x: x["num"])
    if thresholds_in_filename:
        filename = f"{output_dir}/whitespace_{thresholds.h_width}-{thresholds.h_blank}-" \
               f"{thresholds.v_width}-{thresholds.v_blank}.json"
    else:
        filename = f"{output_dir}/whitespace.json"
    output = { "thresholds": thresholds.toJSON(), "pages": sorted_pages}
    with open(filename, "w") as outfile:
        json.dump(output, outfile, indent=4)
    return filename


##
# Given an image and a set of threshold values, find the whitespace on a page
#
# Thresholds should contain:
# h_width: the minimum width of a horizontal space (in px)
# h_blank: The % of pixels in a horizontal line that are blank to "count" the line as blank
# v_width: the minimum width of a vertical space (in px)
# v_blank: the % of pixels in a horizontal line that are blank to "count" the line as blank
#
# Returns ALL the qualifying gaps on a page. This can be used to later classify
# different kinds of gaps (margin, header, etc)
def process_page(im_path, thresholds, viz=False):
    page_num = int(im_path.split('/')[-1].replace(".tiff", ""))  # TODO: make this more robust
    img, img_binary = ws.get_binary_image(im_path)
    height, width = img_binary.shape
    try:
        horizontal_gaps = ws.find_gaps_directional(img_binary, 1, width_thresh=thresholds.h_width,
                                                  blank_thresh=thresholds.h_blank)
        vertical_gaps = ws.find_gaps_directional(img_binary, 0, width_thresh=thresholds.v_width,
                                                  blank_thresh=thresholds.v_blank)
    except IndexError:  # FIXME: When was this erroring out?
        horizontal_gaps = []
        vertical_gaps = []
    except ValueError:
        raise

    if viz:
        ws.visualize(img_binary, horizontal_gaps, vertical_gaps)

    return {"image": im_path,
            "num": page_num,
            "height": height,
            "width": width,
            "vertical_gaps": vertical_gaps,
            "horizontal_gaps": horizontal_gaps}


def find_gaps(image_dir, thresholds=ws.Thresholds(),
              viz=False, thresholds_in_filename=False, return_data=False, verbose = True):
    if verbose:
        print("\n*** Detecting margins & whitespace... ***")
    output_dir = "/".join(image_dir.split("/")[:-1])

    imgs = os.listdir(image_dir) # List all images in the given directory
    all_data = [] # empty data container
    for im in tqdm(imgs): # for every image (showing progress bar)
        i = int(im.split('.')[0]) # get the image number from the file name
        image_path = f"{image_dir}/{im}" # get the path of the image
        try:
            data = process_page(image_path, thresholds, viz=viz) # Try to process the page
        except ValueError:
            continue # If you can't, skip it
        all_data.append(data) # add this image's data to the list of data
        if i % 20 == 0: # Every 20 images, save the output
            write_output(all_data, output_dir, thresholds)

    # For getting the data straight in memory, not writing to file
    if return_data:
        sorted_pages = sorted(all_data, key=lambda x: x["num"])
        return sorted_pages

    return write_output(all_data, output_dir, thresholds, thresholds_in_filename=thresholds_in_filename) # save all the output & return the file path


if __name__ == "__main__":
    IMAGE_DIR = f"interface/static/projects/sample/binary_images"
    find_gaps(IMAGE_DIR)
