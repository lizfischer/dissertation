import json
import csv
from itertools import combinations
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd


def text_text():
    with open('all_records.json', 'r') as infile:
        texts = json.load(infile)

    with open('DIMEV/4 - gephi/rel_text-text.csv', 'w') as outfile:
        writer = csv.writer(outfile, lineterminator='\n')
        writer.writerow(['Source', 'Target', 'Label', 'Type'])
        mss = {}
        for t in texts:
            text_label = f"DIMEV {t}"
            for w in texts[t]['_witnesses']:
                if w in mss:
                    mss[w].append(text_label)
                else:
                    mss[w] = [text_label]
        for ms in mss:
            pairs = list(combinations(mss[ms], 2))
            for p in pairs:
                writer.writerow([p[0], p[1], ms, 'Undirected'])


def ms_ms():
    with open('all_records.json', 'r') as infile:
        texts = json.load(infile)

    with open('rel_ms-ms.csv', 'w') as outfile:
        writer = csv.writer(outfile, lineterminator='\n')
        writer.writerow(['Source', 'Target', 'Label', 'Type'])
        for t in texts:
            text_label = f"DIMEV {t}"
            witnesses = [w for w in texts[t]['_witnesses']]
            pairs = list(combinations(witnesses, 2))
            for p in pairs:
                writer.writerow([p[0], p[1], text_label, 'Undirected'])


def make_adjacency_list(data: pd.DataFrame, node: str, edge: str, outfile: str = None):
    # Get nodes & edges
    subjects_and_texts = data[[edge, node]]

    # Group by edge
    grouped = subjects_and_texts.groupby([edge])[node].apply(list)

    # Make pairs of nodes
    grouped = grouped.apply((lambda x: list(combinations(x, 2)))).explode()
    grouped = grouped.dropna()
    grouped = grouped.apply(lambda x: tuple(sorted(str(y) for y in x)))  # sort so they get deduplicated later
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
    print(f"Wrote to {outfile}")
    return grouped[['Source', 'Target', 'Label', 'Weight']].reset_index()
