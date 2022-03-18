# Given a gaps file & some rules, break a series of images into TODO

from find_gaps import find_gaps, process_page
from whitespaceHelpers import Thresholds
from tesseract import get_formatted_text
import pytesseract
from PIL import Image
import pandas as pd
pd.set_option("display.max_rows", 10, "display.max_columns", None)
import re

# direction: positive is above, negative is below
def ignore_helper(projectID, direction, n_gaps, min_size, blank_thresh):
    thresh = Thresholds(h_width=min_size, h_blank=blank_thresh)
    binary_im_dir = f"interface/static/projects/{projectID}/binary_images"
    page_data = find_gaps(binary_im_dir, thresholds=thresh, return_data=True)

    boundaries = {}
    for page in page_data:
        if direction >= 0:  # ignore text above
            # The 0-start gap is ALWAYS ignored because it is a margin with no text detected at this threshold
            capture_start = page["horizontal_gaps"][n_gaps]["start"] + page["horizontal_gaps"][n_gaps]["width"]/2
            boundaries[page["num"]]=capture_start
        else:  # ignore text below
            # The last gap is ALWAYS ignored because it is a margin with no text detected at this threshold
            capture_end = page["horizontal_gaps"][-n_gaps-1]["start"] + page["horizontal_gaps"][n_gaps-1]["width"]/2
            boundaries[page["num"]]=capture_end
    return boundaries


# rule1 and rule 2 should each take the form {direction: 'above'|'below', n_gaps: #, min_size: #, blank_thresh: #}
def ignore(projectID, rule1, rule2=None):
    starts = None
    ends = None
    if rule1["direction"] == "above":
        starts = ignore_helper(projectID, 1, rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"])
    elif rule1["direction"] == "below":
        ends = ignore_helper(projectID, -1, rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"])

    if rule2:
        if rule2["direction"] == "above" and not starts:
            starts = ignore_helper(projectID, 1, rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"])
        elif rule2["direction"] == "below" and not ends:
            ends = ignore_helper(projectID, -1, rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"])
        else:
            print("Rule 2 ignored because it would replace rule 1")

    return starts, ends


def ocr_page(projectID, page_num, start=None, end=None):
    custom_config = r'-c preserve_interword_spaces=1 --oem 1 --psm 1 -l eng+ita'  # TODO: Add language customization?

    # Get the image & run Tesseract
    image_path = f"interface/static/projects/{projectID}/pdf_images/{page_num}.jpg"
    print("Doing OCR...")
    df = pytesseract.image_to_data(Image.open(image_path), output_type='data.frame', config=custom_config).dropna()

    # Remove ignored areas at start & end
    content = df
    if start:
        content = content[content["top"] > start]
    if end:
        content = content[content["top"] < end]

    return content


# FIXME: Rethinking the available rules
# What are the cases that I actually see in the documents?
# 1. After gap of certain size
# 2. Text to the left of a certain line, and (after gap of certain size or at the top of a page)
# could have "simple" and "advanced" versions. Simple has a problem with top-of-page starts. Could get regex involved?

# After gap of a certain size, OR at the top of the page IF the first line of text meets certain conditions
# option to always start a new entry at the top ("strong split"), or never do so ("weak split")
# So the options are: Always, never, or first-line regex

# split = strong | weak
def simple_separate(image_folder, gap_size, blank_thresh, split, regex=None):
    # Validate parameters
    valid_types = ["strong", "weak", "regex"]
    if split not in valid_types:
        raise ValueError(f"Invalid split type: '{split}'. Split type should be one of {valid_types}")
    if split == "regex":
        if not regex:
            raise ValueError("Split type 'regex', but no regular expression provided.")
        try:
            re.compile(regex)
        except re.error:
            raise ValueError(f"Non-valid regex pattern: {regex}")

    # Do gap recognition at the set threshold
    thresh = Thresholds(h_width=gap_size, h_blank=blank_thresh)


# Text to the left of a certain line,  and (after gap of certain size or at the top of a page)
def indent_separate():
    pass


# TEST
if __name__ == '__main__':
    projectID = "sample"
   # 0starts, ends = ignore(projectID,
   #        {"direction": 'above', "n_gaps": 1, "min_size": 10.0, "blank_thresh": 0.02},
   #        {"direction": 'below', "n_gaps": 1, "min_size": 5.0, "blank_thresh": 0.001})

    simple_separate("weak")
    page = 2
    # ocr_page("sample", page, starts[page], ends[page])
