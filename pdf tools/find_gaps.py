import numpy as np
import json
import sys
import whitespaceHelpers as ws
np.set_printoptions(threshold=sys.maxsize)
from models import *
import random, string

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
# Turn the output of gap detection into annotations for Annotorious
##

class Annotation:
    def __init__(self, x, y, w, h, text=""):
        self.id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))  # TODO: Make unique
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.json = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f"#{self.id}",
            "type": "Annotation",
            "body": [{
                "type": "TextualBody",
                "value": f"{self.text}"
            }],
            "target": {
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": f"xywh=pixel:{x},{y},{w},{h}"
                }
            }
        }

# Old annotation function

# def whitespace_to_annotations(pages_data, project_id):
#     project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
#     annotation_folder = os.path.join(project_folder, "annotations")
#     if not os.path.exists(annotation_folder):
#         os.mkdir(annotation_folder)
#
#     for image in pages_data:
#         num = image["num"]
#         annotations = []
#         anno_file = os.path.join(annotation_folder, f"{num}-annotations.json")
#
#         # First vertical gap, start at end of the gap
#         annotation = Annotation(image["vertical_gaps"][0]["end"], 0, 1, image['height'])
#         annotations.append(annotation.json)
#         # NOTE: SHOWING ONLY the first gap since this is only needed for left-margin detection atm...
#         # Middle gaps, give the midpoint
#         # for v in image["vertical_gaps"][1:-1]:
#         #    x = v['start'] + v['width'] / 2
#         #    annotation = Annotation(x, 0, 1, image['height'])
#         #    annotations.append(annotation.json)
#         # Last vertical gap, start at start of the gap
#         #if len(image["vertical_gaps"]) > 2 :
#         #    annotation = Annotation(image["vertical_gaps"][-1]["start"], 0, 1, image['height'])
#         #annotations.append(annotation.json)
#
#         # First horizontal gap, start at end of the gap
#         # annotation = Annotation(0, image["horizontal_gaps"][0]["end"], image['width'], 1)
#         # annotations.append(annotation.json)
#         # Middle gaps, give the midpoint
#         for h in image["horizontal_gaps"][1:-1]:
#             y = h['start'] + h["width"] / 2
#             annotation = Annotation(0, y, image['width'], 1, text=h["width"])
#             annotations.append(annotation.json)
#         # Last horizontal gap, start at start of the gap
#         # annotation = Annotation(0, image["horizontal_gaps"][-1]["start"], image['width'], 1)
#         # annotations.append(annotation.json)
#
#         # Save file
#         with open(anno_file, "w") as outfile:
#             json.dump(annotations, outfile, indent=4)
#     return annotation_folder

def whitespace_to_annotations(data, page):
    annotations = []
    # First vertical gap, start at end of the gap
    annotation = Annotation(data["vertical_gaps"][0]["end"], 0, 1, page.height)
    annotations.append(annotation.json)

    # Middle vertical gaps, give the midpoint
    for v in data["vertical_gaps"][1:-1]:
       x = v['start'] + v['width'] / 2
       annotation = Annotation(x, 0, 1, page.height)
       annotations.append(annotation.json)

    # Last vertical gap, start at start of the gap
    if len(data["vertical_gaps"]) > 2 :
       annotation = Annotation(data["vertical_gaps"][-1]["start"], 0, 1, page.height)
    annotations.append(annotation.json)

    # First horizontal gap, start at end of the gap
    annotation = Annotation(0, data["horizontal_gaps"][0]["end"], page.width, 1)
    annotations.append(annotation.json)

    # Middle horizontal gaps, give the midpoint
    for h in data["horizontal_gaps"][1:-1]:
        y = h['start'] + h["width"] / 2
        annotation = Annotation(0, y,  page.width, 1, text=h["width"])
        annotations.append(annotation.json)

    # Last horizontal gap, start at start of the gap
    annotation = Annotation(0, data["horizontal_gaps"][-1]["start"],  page.width, 1)
    annotations.append(annotation.json)

    return json.dumps(annotations)

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

    return {"height": height,
            "width": width,
            "vertical_gaps": vertical_gaps,
            "horizontal_gaps": horizontal_gaps}


def find_gaps(project, thresh=Thresholds(),
              viz=False, thresholds_in_filename=False, return_data=False, verbose = True):
    if verbose:
        print("\n*** Detecting margins & whitespace... ***")

    for page in project.pages: # for every page
        image_path = page.get_binary()
        try:
            data = process_page(image_path, thresh, viz=viz) # Try to process the page
        except ValueError:
            continue # If you can't, skip it

        whitespace = PageWhitespace(image_path=image_path, threshold=thresh, sequence=page.sequence)

        for gap in data["vertical_gaps"]:
            g = Gap(start=gap["start"], end=gap["end"], width=gap["width"], direction="vertical")
            whitespace.gaps.append(g)
        for gap in data["horizontal_gaps"]:
            g = Gap(start=gap["start"], end=gap["end"], width=gap["width"], direction="horizontal")
            whitespace.gaps.append(g)
        whitespace.annotation = whitespace_to_annotations(data, page)
        page.whitespace = whitespace
        project.has_gaps = True
        project.save()

    return True
