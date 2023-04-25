import os
import sys
import glob
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import numpy as np
import pandas
import pandas as pd
pd.set_option('display.max_columns', None)

# Calculate end of entity span
def calculate_end(row):
    start = row["start"]
    length = len(row["QUOTE_TRANSCRIPTION"])
    return start + length - 1


# Import file
df = pandas.read_csv("RECOGITO OUTPUT/Tite/!merged.csv")

# Rename anchor column to "start" & convert to int
df.rename(columns={"ANCHOR": "start"}, inplace=True)
df['start'] = df['start'].map(lambda x: int(x.replace("char-offset:", "")))

# Add "end" column
df['end'] = df.apply(lambda row:calculate_end(row), axis=1)

# Remove unused columns & move 'end' next to 'start
columns = ['UUID', 'FILE', 'QUOTE_TRANSCRIPTION', 'start', 'end', 'TYPE', 'TAGS', 'COMMENTS']
df = df[columns]

#NOTE: Pforz
# df["Person"] = np.NAN
# df["AuctionYear"] = np.NAN
# df["Lot"] = np.NAN
# df["PersonUUID"] = np.NAN

# NOTE: TITE
df["GROUP_ID"] = np.NAN

# Loop through documents
gb_file = df.groupby("FILE")
files = gb_file.groups.keys()
for f, tags_in_file in gb_file:
    # Get all the "wrapper" entities
    #wrappers = tags_in_file.loc[tags_in_file["TYPE"] == "EVENT"]  # NOTE: PFORZ

    # NOTE: TITE
    tags_in_file["TAGS"] = tags_in_file["TAGS"].str.lower()
    cond = tags_in_file["TAGS"].str.split('|', expand=True).eq("loan").any(axis=1)
    wrappers = tags_in_file.loc[cond]


    # In each wrapper...
    for index, wrapper in wrappers.iterrows():
        # Get the start and end of the character offset ragne
        start = wrapper["start"]
        end = wrapper["end"]

        # Filter the set of tags in the file for things that are nested within this wrapper (by character offset)
        inner = tags_in_file.loc[(tags_in_file["start"] >= start) & (tags_in_file["end"] <= end)]

        # Search the "inner" tags for the info we want to save
        # NOTE: PFORZ
        # person = inner.loc[inner["TYPE"] == "PERSON"]["QUOTE_TRANSCRIPTION"]
        # personUUID = inner.loc[inner["TYPE"] == "PERSON"]["UUID"]
        # year = inner.loc[inner["TAGS"] == "AuctionYear"]["QUOTE_TRANSCRIPTION"]
        # lot = inner.loc[inner["TAGS"] == "Lot"]["QUOTE_TRANSCRIPTION"]

        # NOTE: TITE
        df.loc[inner.index, "GROUP_ID"] = wrapper["UUID"]

        # Set year, lot, person name, and PersonID on the row for the Event entity.
        ## need to save person ID because relationships *should* key on person ID, not event ID
        # NOTE: PFORZ
        # df.loc[df['UUID'] == wrapper['UUID'], "AuctionYear"] = year.str.cat(sep='|') if not year.empty else np.NAN
        # df.loc[df['UUID'] == wrapper['UUID'], "Lot"] = lot.str.cat(sep='|') if not lot.empty else np.NAN
        # df.loc[df['UUID'] == wrapper['UUID'], "Person"] = person.str.cat(sep='|') if not person.empty else np.NAN
        # df.loc[df['UUID'] == wrapper['UUID'], "PersonUUID"] = personUUID.str.cat(sep='|') if not personUUID.empty else np.NAN

        # Merge the comments on all the "inner" labels and save them to the wrapper's row
        # df.loc[df['UUID'] == wrapper['UUID'], "COMMENTS"] = inner["COMMENTS"].str.cat(sep="|")


        # Drop all inner rows
        # df.drop(inner.index, inplace=True)

# Save new DF
df.to_csv("Tite-overlaps-merged.csv")




