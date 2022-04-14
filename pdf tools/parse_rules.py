# Given a gaps file & some rules, break a series of images into entries

from find_gaps import find_gaps
from whitespaceHelpers import Thresholds
from tesseract import get_formatted_text
import pytesseract
from PIL import Image
import pandas as pd
import re
from tqdm import tqdm

pd.set_option("display.max_rows", 10, "display.max_columns", None)


def ignore_helper(project_id, direction, n_gaps, min_size, blank_thresh):
    binary_im_dir = f"interface/static/projects/{project_id}/binary_images"
    n_gaps = int(n_gaps)
    min_size = int(min_size)
    blank_thresh = float(blank_thresh)

    if direction == "above" or direction == "below":
        thresh = Thresholds(h_width=min_size, h_blank=blank_thresh)
    elif direction == "left" or direction == "right":
        thresh = Thresholds(v_width=min_size, v_blank=blank_thresh)
    else:
        thresh = None
    page_data = find_gaps(binary_im_dir, thresholds=thresh, return_data=True, verbose=False)

    boundaries = {}

    for page in page_data:
        if direction == "above":  # ignore text above
            # The 0-start gap is ALWAYS ignored because it is a margin with no text detected at this threshold
            capture_start = page["horizontal_gaps"][n_gaps]["start"] + page["horizontal_gaps"][n_gaps]["width"] / 2
            boundaries[page["num"]] = capture_start
        elif direction == "below":  # ignore text below
            # The last gap is ALWAYS ignored because it is a margin with no text detected at this threshold
            capture_end = page["horizontal_gaps"][-n_gaps - 1]["start"] + page["horizontal_gaps"][n_gaps - 1][
                "width"] / 2
            boundaries[page["num"]] = capture_end
        elif direction == "left":  # ignore text to the left
            left_edge = page["vertical_gaps"][n_gaps - 1]["end"] - 2  # + page["vertical_gaps"][n_gaps-1]["width"]/2
            boundaries[page["num"]] = left_edge
        elif direction == "right":  # ignore text to the left
            right_edge = page["vertical_gaps"][n_gaps - 1]["start"] + 2  # page["vertical_gaps"][n_gaps-1]["width"]/2
            boundaries[page["num"]] = right_edge
    return boundaries


# rule1 and rule 2 should each take the form {direction: 'above'|'below', n_gaps: #, min_size: #, blank_thresh: #}
# Returns none for starts, ends, lefts, and rights if no rules specified
def ignore(project_id, rule1=None, rule2=None):
    print("\n***Finding which sections to ignore...***")
    starts, ends, lefts, rights = None, None, None, None

    if rule1:
        if rule1["direction"] == "above":
            starts = ignore_helper(project_id, "above", rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"])
        elif rule1["direction"] == "below":
            ends = ignore_helper(project_id, "below", rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"])
        elif rule1["direction"] == "left":
            lefts = ignore_helper(project_id, "left", rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"])
        elif rule1["direction"] == "right":
            lefts = ignore_helper(project_id, "right", rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"])

    if rule2:
        if rule2["direction"] == "above" and not starts:
            starts = ignore_helper(project_id, 1, rule2["n_gaps"], rule2["min_size"], rule2["blank_thresh"])
        elif rule2["direction"] == "below" and not ends:
            ends = ignore_helper(project_id, -1, rule2["n_gaps"], rule2["min_size"], rule2["blank_thresh"])
        elif rule2["direction"] == "left" and not lefts:
            lefts = ignore_helper(project_id, "left", rule2["n_gaps"], rule2["min_size"], rule2["blank_thresh"])
        elif rule2["direction"] == "right" and not rights:
            lefts = ignore_helper(project_id, "right", rule2["n_gaps"], rule2["min_size"], rule2["blank_thresh"])
        else:
            print("Rule 2 ignored because it would replace rule 1")

    return starts, ends, lefts, rights


def ocr_page(project_id, page_num, start=None, end=None, left=None, right=None):
    custom_config = r'-c preserve_interword_spaces=1 --oem 1 --psm 1 -l eng+ita'  # TODO: Add language customization?

    # Get the image & run Tesseract
    image_path = f"interface/static/projects/{project_id}/pdf_images/{page_num}.jpg"
    print(f"\n***Doing OCR for pg {page_num}...***")
    df = pytesseract.image_to_data(Image.open(image_path), output_type='data.frame', config=custom_config).dropna()

    # Remove ignored areas at start & end
    content = df
    if start:
        content = content[content["top"] > start]
    if end:
        content = content[content["top"] < end]
    if left:
        content = content[content["left"] > left]
    if right:
        content = content[content["left"] < right]
    return content


# TODO: Rethinking the available rules
# What are the cases that I actually see in the documents?
# 1. After gap of certain size
# 2. Text to the left of a certain line, and (after gap of certain size or at the top of a page)
# could have "simple" and "advanced" versions. Simple has a problem with top-of-page starts. Could get regex involved?


# validate inputs for simple_separate TODO: Expand validation
# split = "strong" | "weak" | "regex"
# ignore = [start, end]
def simple_separate_val(project_id, gap_size, blank_thresh, ignore, split, regex=None):
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
    if len(ignore) != 4:
        raise ValueError(f"Invalid shape for 'ignore'. Expected [starts, ends, lefts, rights] but received: {ignore}")
    return True


# IN SIMPLE SEPARATE, NEW ENTRIES START:
# After gap of a certain size, OR at the top of the page IF the first line of text meets certain conditions
# option to always start a new entry at the top ("strong split"), or never do so ("weak split")
# So the options are: Always, never, or first-line regex
# FIXME: Can I decompose this method more?
def simple_separate(project_id, gap_size, blank_thresh, ignore, split, regex=None):
    simple_separate_val(project_id, gap_size, blank_thresh, ignore, split, regex)

    starts = ignore[0]
    ends = ignore[1]
    lefts = ignore[2]
    rights = ignore[3]

    print("\n***Starting simple separate...***")
    # Do gap recognition at the set threshold
    thresh = Thresholds(h_width=gap_size, h_blank=blank_thresh)
    binary_im_dir = f"interface/static/projects/{project_id}/binary_images"
    gaps_data = find_gaps(binary_im_dir, thresholds=thresh, return_data=True, verbose=False)

    # Establish list of entries & var to track the active entry
    separated_entries = []
    active_entry = ""

    # For each page in numerical order NB: this relies on find_gaps returning a SORTED list
    for p in tqdm(gaps_data):  # NOTE: This is the place to limit pages if desired for testing
        n = p["num"]
        print(f"\nPage {n}")

        # OCR the page
        start = starts[n] if starts else 0
        end = ends[n] if ends else p["height"]
        left = lefts[n] if lefts else 0
        right = rights[n] if rights else p["width"]

        ocr = ocr_page(project_id, n, start, end, left, right)

        # Get relevant gaps (ie take the ignore boundaries into account)
        all_page_gaps = next((pg for pg in gaps_data if pg["num"] == n), None)["horizontal_gaps"]  # find this page
        gaps_within_content = [g for g in all_page_gaps if g["start"] > start and g["end"] < end]

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
            active_entry = get_formatted_text(
                active_selection)  # TODO: save more complicated entry data? Image info, bounding, etc. ALSO save text as text instead of DF slice?
        # If weak, append to previous entry
        elif split == "weak":
            active_entry += f"\n\n{get_formatted_text(active_selection)}"
        # If regex, test regex and then either append or start new
        elif split == "regex" and regex:
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
            upper_bound = gaps_within_content[n_gaps_considered - 1]["start"]
            lower_bound = gaps_within_content[n_gaps_considered]["start"]
            active_selection = ocr[ocr["top"] > upper_bound]  # below last gap
            active_selection = active_selection[active_selection["top"] < lower_bound]  # above next gap

            # Start a new entry and add the selected text to it
            separated_entries.append(active_entry)
            active_entry = get_formatted_text(active_selection)

            # Increment gaps considered (entry will get "finished" when the next entry starts)
            n_gaps_considered += 1

        # When there are no gaps left, select the text between the last gap & the bottom of the page
        upper_bound = gaps_within_content[n_gaps_considered - 1]["start"]
        active_selection = ocr[ocr["top"] > upper_bound]
        # Start a new entry and add the selected text to it
        separated_entries.append(active_entry)
        active_entry = get_formatted_text(active_selection)

    separated_entries.append(active_entry)
    return separated_entries


# TODO: Indent separate parser
# Indent separate
# type - hanging or regular

def indent_separate_val(project_id, indent_type, margin_thresh, indent_width, ignore):
    valid_types = ["hanging", "regular"]
    if indent_type not in valid_types:
        raise ValueError(f"Invalid indent type: '{indent_type}'. Split type should be one of {valid_types}")

    if not isinstance(margin_thresh, float):
        raise TypeError(f"Invalid margin threshold: '{margin_thresh}'. Expecting float, received {type(margin_thresh)}")

    if not isinstance(indent_width, float):
        raise TypeError(f"Invalid margin threshold: '{indent_width}'. Expecting float, received {type(indent_width)}")

    if len(ignore) != 4:
        raise ValueError(f"Invalid shape for 'ignore'. Expected [starts, ends, lefts, rights] but received: {ignore}")

    return True


def indent_separate(project_id, indent_type, margin_thresh, indent_width, ignore):
    indent_separate_val(project_id, indent_type, margin_thresh, indent_width, ignore)

    starts = ignore[0]
    ends = ignore[1]
    lefts = ignore[2]
    rights = ignore[3]

    print("\n***Starting simple separate...***")
    # Do gap recognition at the set threshold
    thresh = Thresholds(v_blank=margin_thresh)
    binary_im_dir = f"interface/static/projects/{project_id}/binary_images"
    gaps_data = find_gaps(binary_im_dir, thresholds=thresh, return_data=True, verbose=False)

    # Establish list of entries & var to track the active entry
    separated_entries = []
    active_entry = ""

    # For each page in numerical order NB: this relies on find_gaps returning a SORTED list
    for p in tqdm(gaps_data):  # NOTE: This is the place to limit pages if desired for testing
        n = p["num"]
        print(f"\nPage {n}")

        # OCR the page
        start = starts[n] if starts else 0
        end = ends[n] if ends else p["height"]
        left = lefts[n] if lefts else 0
        right = rights[n] if rights else p["width"]

        ocr = ocr_page(project_id, n, start, end, left, right)

        # Find left margin
        all_vertical_gaps = next((pg for pg in gaps_data if pg["num"] == n), None)["vertical_gaps"]  # find this page
        left_margin_line = all_vertical_gaps[0]["end"]

        # Group by line
        lines = ocr.groupby(["block_num", "par_num", "line_num"])
        line_starts = lines.first()

        # Go through line by line
        for line in lines:
            first_word = line[1].iloc[0]
            if indent_type is "hanging":
                is_start = first_word["left"] < left_margin_line - 5  # NOTE: 5 fudge pixels-- this could be a variable?
            else:  # indent_type is "regular"
                is_start = first_word["left"] > left_margin_line + indent_width-5

            # TODO: Get text between, etc.


def test():
    project_id = "swinfield sample"

    starts, ends, lefts, rights = ignore(project_id,
                                         {"direction": 'above', "n_gaps": 2, "min_size": 10.0, "blank_thresh": 0.02},
                                         {"direction": 'left', "n_gaps": 1, "min_size": 10.0, "blank_thresh": 0.05})

    entries = simple_separate(project_id, 50.0, 0.02, [starts, ends, lefts, rights], "regex",
                              regex="^[a-zA-Z]{3,5}[.]? *[0-9]{1,2}[.]? *[—,-]")
    for entry in entries:
        print(entry[0:60].replace('\n', ' '), entry[-60:].replace('\n', ' '))


# TEST
if __name__ == '__main__':
    test()