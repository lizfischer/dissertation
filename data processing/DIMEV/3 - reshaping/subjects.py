import json
import pandas as pd
from itertools import combinations


## CREATE SUBJECTS NODES

text_info_file = "../2 - cleaning/text_info_edited_authors_and_subjects.csv"
text_df = pd.read_csv(text_info_file)

subjects = text_df['Subjects']
text_df['Subjects_Primary'] = text_df['Subjects_Primary'].str.split(';')
exploded = text_df.explode(['Subjects_Primary'])
unique_subjects = list(exploded['Subjects_Primary'].unique())

with open("nodes_subjects.csv", 'w', encoding="utf-8") as subjects_out:
    subjects_out.write("Id, Label, Type\n")
    for subject in unique_subjects:
        subjects_out.write(f"{subject}, {subject}, Subject\n")

## ADD BACK MSS
relationships_df =pd.read_csv("../2 - cleaning/relationships.tsv", sep='\t')

merged = pd.merge(exploded, relationships_df, left_on='Id', right_on='Source')
subjects_and_mss = merged[['Subjects_Primary', 'Target']]
subjects_and_mss = subjects_and_mss.rename(columns={"Subjects_Primary": "Source"})
subjects_and_mss.to_csv("rel_subject-ms.csv", index=False)


## SUBJECT-SUBJECT ADJACENCY
grouped = subjects_and_mss.groupby(['Target'])['Source']
grouped = grouped.apply(list)
with open("rel_subject-subject.csv", "w") as outfile:
    outfile.write("Source, Target\n")
    for group in grouped.values:
        group_pairs = list(combinations(group, 2))
        for pair in group_pairs:
            outfile.write(f"{pair[0]}, {pair[1]}\n")
print("Done")