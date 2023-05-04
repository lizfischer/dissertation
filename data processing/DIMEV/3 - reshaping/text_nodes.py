import pandas as pd
import json

"""
Adding back # MS witnesses
"""

text_info_file = "../4 - gephi/nodes_texts.csv"  # Created from Open Refine
with open("../1 - extraction/all_records.json", 'r') as records_json:
    all_records = json.load(records_json)


def lookup_n_witnesses(row):
    id = row['Id'].split(' ')[1]
    record = all_records[id]
    witnesses = record['_witnesses']
    return int(len(witnesses))

df = pd.read_csv(text_info_file)
df["n_witnesses"] = df.apply(lambda row: lookup_n_witnesses(row), axis=1)
df.to_csv(text_info_file, index=False)