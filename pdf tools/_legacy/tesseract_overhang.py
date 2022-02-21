import pytesseract
from PIL import Image
import time
import json
import pandas as pd
pd.set_option("display.max_rows", None, "display.max_columns", None)

THRESHOLD = 50  # number of pixels before identified start to begin looking for entry text
OUTPUT_FILE = "outputs/br_test.json"

def writeOutput():
    global all_entries
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_entries, f, indent=4)


# mostly copied from stackoverflow... Made a few changes to make it actually show mutliple blocks
# https://stackoverflow.com/questions/59582008/preserving-indentation-with-tesseract-ocr-4-x
def getFormattedText(df):
    try:
        sorted_blocks = df.groupby('block_num').first().sort_values('top').sort_values('left').index.tolist()
        text = ''
        for block in sorted_blocks:
            curr = df[df['block_num'] == block]
            sel = curr[curr.text.str.len() > 3]
            char_w = (sel.width / sel.text.str.len()).mean()
            prev_par, prev_line, prev_left = 0, 0, 0
            for ix, ln in curr.iterrows():
                # add new line when necessary
                if prev_par != ln['par_num']:
                    text += '\n'
                    prev_par = ln['par_num']
                    prev_line = ln['line_num']
                    prev_left = 0
                elif prev_line != ln['line_num']:
                    text += '\n'
                    prev_line = ln['line_num']
                    prev_left = 0

                added = 0  # num of spaces that should be added
                if ln['left'] / char_w > prev_left + 1:
                    added = int((ln['left']) / char_w) - prev_left
                    text += ' ' * added
                text += ln['text'] + ' '
                prev_left += len(ln['text']) + added + 1
            text += '\n'
        return text.strip()
    except OverflowError:  # TODO Real solution?
        return ""


def finishEntry():
    global active_entry, all_entries
    if active_entry["text"].strip():
        all_entries.append(active_entry)
    active_entry = {"text": "", "pages": []}


start_time = time.time()

with open("margins_out.json", "r") as f:
    pages = json.load(f)


all_entries = []
active_entry = {"text": "", "pages": []}
for page in pages:
    # incremental save
    if page["p"] % 20 == 0: writeOutput()

    # Get image
    IMAGE_PATH = page["image"]
    print(IMAGE_PATH)

    # OCR
    custom_config = r'-c preserve_interword_spaces=1 --oem 1 --psm 1 -l eng+ita'
    df = pytesseract.image_to_data(Image.open(IMAGE_PATH), output_type='data.frame', config=custom_config).dropna()

    # Find text below running header
    main_text = df[df["top"] > page["top"]]
    if main_text.empty:
        continue

    # Find text to left of margin
    headers = main_text[main_text["left"] < page["left_char"]].index

    # If there aren't any headers, add the whole page to the active entry
    if len(headers) == 0:
        text = getFormattedText(main_text)
        active_entry["text"] += f" {text}"
        active_entry["pages"].append({"num": page["p"],
                                      "top": int(main_text["top"].min()),
                                      "bottom": -1})
        continue

    # If there are headers, add the top bit (before first header) to the active entry
    first_header = main_text[main_text["top"] < main_text["top"][headers[0]] - THRESHOLD]
    top_text = getFormattedText(first_header).strip()
    if top_text:
        active_entry["text"] += f" {top_text}"
        active_entry["pages"].append({"num": page["p"],
                                      "top": int(main_text["top"].min()),
                                      "bottom": int(main_text["top"][headers[0]])})

    # End active entry
    finishEntry()

    # For every header, make a new entry
    for i in range(0, len(headers)):

        # Get all the text after the header
        current_header = headers[i]
        after_text = main_text[main_text["top"] >= main_text["top"][current_header]-THRESHOLD]

        # If there are more headers, filter out the text after the *next* header and add it to full list
        if i < len(headers)-1:
            next_header = headers[i+1]
            after_text = after_text[after_text["top"] < main_text["top"][next_header]-THRESHOLD]
            active_entry["text"] += getFormattedText(after_text)
            active_entry["pages"].append({"num": page["p"],
                                          "top": int(main_text["top"][current_header]),
                                          "bottom": int(main_text["top"][next_header])})

            finishEntry()

        # Otherwise, just add to active and move to next page
        else:
            active_entry["text"] += getFormattedText(after_text)
            active_entry["pages"].append({"num": page["p"],
                                          "top": int(main_text["top"][current_header]),
                                          "bottom": -1})

finishEntry()

print(all_entries)
writeOutput()
print(f"Finished in {time.time()-start_time} seconds")
