# Given a gaps file & some rules, break a series of images into TODO

from find_gaps import find_gaps, process_page
from whitespaceHelpers import Thresholds
from tesseract import get_formatted_text
import pytesseract
from PIL import Image
import pandas as pd
import numpy as np
pd.set_option("display.max_rows", 10, "display.max_columns", None)
import re
from tqdm import tqdm

# direction: positive is above, negative is below
def ignore_helper(projectID, direction, n_gaps, min_size, blank_thresh):
    thresh = Thresholds(h_width=min_size, h_blank=blank_thresh)
    binary_im_dir = f"interface/static/projects/{projectID}/binary_images"
    page_data = find_gaps(binary_im_dir, thresholds=thresh, return_data=True, verbose=False)

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
    print("\n***Finding which sections to ignore...***")
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
    print(f"\n***Doing OCR for pg {page_num}...***")
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



# validate inputs for simple_separate TODO: Expand validation
# split = "strong" | "weak" | "regex"
# ignore = [start, end]
def simple_separate_val(projectID, gap_size, blank_thresh, ignore, split, regex=None):
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
    if len(ignore) != 2:
        raise ValueError(f"Invalid shape for 'ignore'. Expected [starts, ends] but received: {ignore}")
    return True


# IN SIMPLE SEPARATE, NEW ENTRIES START:
# After gap of a certain size, OR at the top of the page IF the first line of text meets certain conditions
# option to always start a new entry at the top ("strong split"), or never do so ("weak split")
# So the options are: Always, never, or first-line regex
# FIXME: Can I decompose this method more?
def simple_separate(projectID, gap_size, blank_thresh, ignore, split, regex=None):
    simple_separate_val(projectID, gap_size, blank_thresh, ignore, split, regex)

    starts = ignore[0]
    ends = ignore[1]

    print("\n***Starting simple separate...***")
    # Do gap recognition at the set threshold
    thresh = Thresholds(h_width=gap_size, h_blank=blank_thresh)
    binary_im_dir = f"interface/static/projects/{projectID}/binary_images"
    gaps_data = find_gaps(binary_im_dir, thresholds=thresh, return_data=True, verbose=False)

    # Establish list of entries & var to track the active entry
    separated_entries = []
    active_entry = ""

    # For each page in numerical order NB: this relies on find_gaps returning a SORTED list
    for p in tqdm(gaps_data[:3]):
        n = p["num"]
        print(f"\nPage {n}")
        # OCR the page
        ocr = ocr_page(projectID, n, starts[n], ends[n])

        # Get relevant gaps (ie take the ignore boundaries into account)
        all_page_gaps = next((pg for pg in gaps_data if pg["num"] == n), None)["horizontal_gaps"]  # find this page
        gaps_within_content = [g for g in all_page_gaps if g["start"] > starts[n] and g["end"] < ends[n]]

        n_gaps_considered = 0
        # If there are no gaps, select the whole page
        if len(gaps_within_content) == 0:
            active_selection = ocr
        # If there are gaps, select up to the first gap
        else:
            active_selection = ocr[ocr["top"] < gaps_within_content[0]["start"]]
            n_gaps_considered += 1  # we've looked up to the first gap

        # Decide what to do with the selected text (top of page) based on the split method specified
        # If strong, start a new entry
        if split == "strong":
            if active_entry: separated_entries.append(active_entry)
            active_entry = get_formatted_text(active_selection)  # TODO: save more complicated entry data? Image info, bounding, etc. ALSO save text as text instead of DF slice?
        # If weak, append to previous entry
        elif split == "weak":
            active_entry += f"\n\n{get_formatted_text(active_selection)}"
        # If regex, test regex and then either append or start new
        elif split == "regex":  # TODO: implement regex
            # Get text
            text = get_formatted_text(active_selection)
            needs_split = re.search(regex, text)

            if needs_split:  # Start a new entry
                if active_entry: separated_entries.append(active_entry)
                active_entry = text
            else:  # Do NOT start a new entry, append current selection to previous entry instead
                active_entry += f"\n\n{text}"

        # If there are NO gaps, move to the next page
        if len(gaps_within_content) == 0: continue

        # While there is *another* gap on the page select the text between the "last" gap and the "next" gap
        while n_gaps_considered < len(gaps_within_content):
            upper_bound = gaps_within_content[n_gaps_considered-1]["start"]
            lower_bound = gaps_within_content[n_gaps_considered]["start"]
            active_selection = ocr[ocr["top"] > upper_bound]  # below last gap
            active_selection = active_selection[active_selection["top"] < lower_bound]  # above next gap

            # Start a new entry and add the selected text to it
            separated_entries.append(active_entry)
            active_entry = get_formatted_text(active_selection)

            # Increment gaps considered (entry will get "finished" when the next entry starts)
            n_gaps_considered += 1

        # When there are no gaps left, select the text between the last gap & the bottom of the page
        upper_bound = gaps_within_content[n_gaps_considered-1]["start"]
        active_selection = ocr[ocr["top"] > upper_bound]
        # Start a new entry and add the selected text to it
        separated_entries.append(active_entry)
        active_entry = get_formatted_text(active_selection)

    separated_entries.append(active_entry)
    return separated_entries


# IN INDENT SEPARATE, NEW ENTRIES START:
# When there is text to the left of a certain line, AND after gap of certain size or at the top of a page
# By default, checks for ex-dented text *anywhere* in the block, but can specify first-line only.
# Default anywhere in case ex-dented block gets put somewhere other than first due to a crooked page eg.
def indent_separate():
    pass


# TEST
if __name__ == '__main__':
    projectID = "sample"

    starts, ends = ignore(projectID,
           {"direction": 'above', "n_gaps": 1, "min_size": 10.0, "blank_thresh": 0.02},
           {"direction": 'below', "n_gaps": 1, "min_size": 5.0, "blank_thresh": 0.001})

    entries = simple_separate(projectID, 40.0, 0.01, [starts, ends], "regex", regex="^\d{1,4}\s+[A-Z]+")
    print(entries)