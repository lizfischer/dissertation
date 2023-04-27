import pandas as pd
from itertools import combinations

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


def make_adjacency_list(data: pd.DataFrame, node: str, edge: str, outfile: str = None):
    # Get nodes & edges
    subjects_and_texts = data[[edge, node]]

    # Group by edge
    grouped = subjects_and_texts.groupby([edge])[node].apply(list)

    # Make pairs of nodes
    grouped = grouped.apply((lambda x: list(combinations(x, 2)))).explode()
    grouped = pd.DataFrame(grouped)
    grouped[edge] = grouped.index

    # Group pairs of nodes
    grouped = grouped.groupby([node])[edge].apply(list)
    grouped = pd.DataFrame(grouped)
    grouped[node] = grouped.index
    grouped[edge] = grouped[edge].apply(set)
    grouped['Weight'] = grouped[edge].str.len()

    # Concat Edges for Label
    grouped[edge] = grouped[edge].apply(lambda x: ";".join(set(x)))
    grouped[['Source', 'Target']] = pd.DataFrame(grouped[node].tolist(), index=grouped.index)
    grouped = grouped.rename(columns={edge: 'Label'})

    # Save out
    if outfile:
        grouped[['Source', 'Target', 'Label', 'Weight']].to_csv(outfile, index=False)
    return grouped[['Source', 'Target', 'Label', 'Weight']].reset_index()


# ADD BACK MSS
relationships_df = pd.read_csv("../4 - gephi/rel_text-ms.tsv", sep='\t')
merged = pd.merge(exploded, relationships_df, left_on='Id', right_on='Source')
merged = merged.rename(columns={"Target": "MS", "Author(s)": "Author"})
grouped = make_adjacency_list(merged, 'Author', 'MS', "../4 - gephi/rel_author-author_ms.csv")
