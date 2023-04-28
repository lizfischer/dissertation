import pandas as pd
from itertools import combinations
from adjacency_lists import make_adjacency_list

# CREATE SUBJECTS NODES

text_info_file = "../4 - gephi/nodes_texts.csv"
text_df = pd.read_csv(text_info_file)

subjects = text_df['Subjects']
text_df['Subjects_Primary'] = text_df['Subjects_Primary'].str.split(';')
exploded = text_df.explode(['Subjects_Primary'])
unique_subjects = list(exploded['Subjects_Primary'].unique())


def save_subject_nodes():
    with open("../4 - gephi/nodes_subjects.csv", 'w', encoding="utf-8") as subjects_out:
        subjects_out.write("Id, Label, Type\n")
        for subject in unique_subjects:
            subjects_out.write(f"{subject}, {subject}, Subject\n")


def subject_subject_ms():
    # ADD BACK MSS
    relationships_df = pd.read_csv("../4 - gephi/rel_text-ms.tsv", sep='\t')

    merged = pd.merge(exploded, relationships_df, left_on='Id', right_on='Source')
    subjects_and_mss = merged[['Subjects_Primary', 'Target']]
    subjects_and_mss = subjects_and_mss.rename(columns={"Subjects_Primary": "Source"})
    subjects_and_mss.to_csv("rel_subject-ms.csv", index=False)

    # SUBJECT-SUBJECT ADJACENCY
    grouped = subjects_and_mss.groupby(['Target'])['Source'].apply(list)
    grouped = grouped.apply((lambda x: list(combinations(x, 2)))).explode()
    grouped = pd.DataFrame(grouped)
    grouped['MS'] = grouped.index

    grouped = grouped.groupby(['Source'])['MS'].apply(list)
    grouped = pd.DataFrame(grouped)
    grouped['Subjects'] = grouped.index
    grouped['Weight'] = grouped['MS'].str.len()

    # Concat MSS for Label
    grouped['MS'] = grouped['MS'].apply(lambda x: ";".join(set(x)))
    grouped[['Source', 'Target']] = pd.DataFrame(grouped['Subjects'].tolist(), index=grouped.index)
    grouped = grouped.rename(columns={'MS': 'Label'})

    # Save out
    grouped[['Source', 'Target', 'Label', 'Weight']].to_csv("../4 - gephi/rel_subject-subject_ms.csv", index=False)

    return grouped


def rel_subject_author(save: bool = True):
    exploded['Author(s)'] = exploded['Author(s)'].str.split(';')
    explode_authors = exploded.explode(['Author(s)'])
    subjects_and_authors = explode_authors[['Subjects_Primary', "Author(s)", "Id"]]
    subjects_and_authors = subjects_and_authors[subjects_and_authors['Author(s)'].notna()]
    subjects_and_authors_renamed = subjects_and_authors.rename(columns={"Subjects_Primary": "Source", "Author(s)": "Target",
                                                                "Id": "Label"})
    if save:
        subjects_and_authors_renamed.to_csv("../4 - gephi/rel_subject-author.csv", index=False)
    return subjects_and_authors


subject_author = rel_subject_author()
subject_subject_author = make_adjacency_list(subject_author, "Subjects_Primary", "Author(s)",
                                             "../4 - gephi/rel_subject-subject_author.csv")
#
# def subject_subject_author():
#     subjects_and_authors = subject_author(save=False)
#     grouped = subjects_and_authors.groupby(['Target'])['Source'].apply(list)
#     grouped = grouped.apply((lambda x: list(combinations(x, 2)))).explode()
#
#     grouped = pd.DataFrame(grouped)
#     grouped['Author'] = grouped.index
#
#     grouped = grouped.groupby(['Source'])['Author'].apply(list)
#     grouped = pd.DataFrame(grouped)
#     grouped['Subjects'] = grouped.index
#     grouped['Weight'] = grouped['Author'].str.len()
#
#     # Concat MSS for Label
#     grouped['Author'] = grouped['Author'].apply(lambda x: ";".join(set(x)))
#     grouped[['Source', 'Target']] = pd.DataFrame(grouped['Subjects'].tolist(), index=grouped.index)
#     grouped = grouped.rename(columns={'Author': 'Label'})
#
#     # Save out
#     grouped[['Source', 'Target', 'Label', 'Weight']].to_csv("../4 - gephi/rel_subject-subject_author.csv", index=False)


def subject_subject_text():
    # Get subjects & texts
    subjects_and_texts = exploded[['Id', 'Subjects_Primary']]\

    # Group by subjects
    grouped = subjects_and_texts.groupby(['Id'])['Subjects_Primary'].apply(list)

    # Make pairs of subjects
    grouped = grouped.apply((lambda x: list(combinations(x, 2)))).explode()
    grouped = pd.DataFrame(grouped)
    grouped['Text'] = grouped.index

    # Group pairs by text
    grouped = grouped.groupby(['Subjects_Primary'])['Text'].apply(list)
    grouped = pd.DataFrame(grouped)
    grouped['Subjects'] = grouped.index
    grouped['Weight'] = grouped['Text'].str.len()

    # Concat Texts for Label
    grouped['Text'] = grouped['Text'].apply(lambda x: ";".join(set(x)))
    grouped[['Source', 'Target']] = pd.DataFrame(grouped['Subjects'].tolist(), index=grouped.index)
    grouped = grouped.rename(columns={'Text': 'Label'})

    # Save out
    grouped[['Source', 'Target', 'Label', 'Weight']].to_csv("../4 - gephi/rel_subject-subject_text.csv", index=False)



# save_subject_nodes()

# subject_subject_text()
# subject_subject_ms()
# subject_subject_author()
