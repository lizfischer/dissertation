import pandas as pd
from itertools import combinations
from adjacency_lists import make_adjacency_list


# CREATE Authors NODES

text_info_file = "../4 - gephi/nodes_texts.csv"
text_df = pd.read_csv(text_info_file)

text_df['Author(s)'] = text_df['Author(s)'].str.split(';')
exploded = text_df.explode(['Author(s)'])
exploded['Author(s)'] = exploded['Author(s)'].fillna("Unknown")


def authors_nodes():
    unique_authors = list(exploded['Author(s)'].unique())
    authors_df = pd.DataFrame()
    authors_df['Id'] = unique_authors
    authors_df['Label'] = unique_authors
    authors_df['Type'] = 'Author'
    authors_df.to_csv("../4 - gephi/nodes_authors.csv", index=False)
    return authors_df


# ADD BACK MSS
relationships_df = pd.read_csv("../4 - gephi/rel_text-ms.tsv", sep='\t')
merged = pd.merge(exploded, relationships_df, left_on='Id', right_on='Source')
merged = merged.rename(columns={"Target": "MS", "Author(s)": "Author"})
grouped = make_adjacency_list(merged, 'Author', 'MS', "../4 - gephi/rel_author-author_ms.csv")
