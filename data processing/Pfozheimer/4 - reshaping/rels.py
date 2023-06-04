import pandas as pd


def correct_ids():
    rel_data = pd.read_csv("rel_raw.tsv", delimiter="\t")
    node_data = pd.read_csv("nodes_raw.tsv", delimiter="\t")

    valid_ids = set(list(node_data['ID']))

    # Make ID map
    id_map = {}
    for index, row in node_data.iterrows():
        if row['AlternateID']:
            alt_ids = str(row['AlternateID']).split('|')
            for x in alt_ids:
                id_map[x] = row['ID']

    def lookup_id(some_id):
        if some_id in valid_ids:
            return some_id
        elif some_id in id_map.keys():
            return id_map[some_id]
        else:
            print(f"Id not found: {some_id}")
            return None

    # Map ids
    rel_data['source_id'] = rel_data['source_id'].apply(lookup_id)
    rel_data['target_id'] = rel_data['target_id'].apply(lookup_id)

    rel_data.to_csv("rel_ids_fixed.csv", index=False)


def add_pforz():
    rel_data = pd.read_csv("rel_ids_fixed.csv")
    node_data = pd.read_csv("nodes_raw.tsv", delimiter="\t")

    sources = list(rel_data['source_id'])
    ends = [node_id for node_id in node_data['ID'] if node_id not in sources]

    pforz_edges = pd.DataFrame()
    pforz_edges['Source'] = ends
    pforz_edges['Target'] = 0

    pforz_edges.to_csv("../5 - gephi/rel_pforz_only.csv", index=False)


def seller_seller():
    rel_data = pd.read_csv("rel_ids_fixed_with_pforz.csv")
    node_data = pd.read_csv("nodes_raw.tsv", delimiter="\t")

    sellers = pd.DataFrame()
    # sellers['Source_id'] = rel_data['source_id']
    # sellers['Target_id'] = rel_data['target_id']

    sellers['Source'] = rel_data.source_id.map(node_data.set_index('ID')['Person'])
    sellers['Target'] = rel_data.target_id.map(node_data.set_index('ID')['Person']).fillna("Pforzheimer")

    sellers['Year'] = rel_data.source_id.map(node_data.set_index('ID')['AuctionYear']).fillna("")
    sellers['Book'] = rel_data.source_id.map(node_data.set_index('ID')['CatalogNum']).fillna("")
    sellers['Lot'] = rel_data.source_id.map(node_data.set_index('ID')['Lot']).fillna("")

    sellers['Edge Label'] = sellers.apply(lambda x: f"Book {x['Book']}: {x['Year'] or 'Undated'}, Lot {x['Lot'] or 'n/a'} ", axis=1)

    # Weight and create edge labels
    grouped = sellers.groupby(['Source', 'Target'])['Book'].apply(list)
    grouped = pd.DataFrame(grouped)
    grouped['Years'] = sellers.groupby(['Source', 'Target'])['Year'].apply(list)
    grouped['Edge Label'] = sellers.groupby(['Source', 'Target'])['Edge Label'].apply(list)
    grouped['Weight'] = grouped['Book'].str.len()
    grouped.rename(columns={'Book': 'Books'}, inplace=True)
    grouped = grouped.reset_index()

    grouped.to_csv("../5 - gephi/rel_seller_seller_with_pforz_grouptest.csv", index=False)


def auction_auction():
    rel_data = pd.read_csv("rel_ids_fixed_with_pforz.csv")
    node_data = pd.read_csv("nodes_raw.tsv", delimiter="\t")

    auctions = pd.DataFrame()
    auctions['Source_id'] = rel_data['source_id']
    auctions['Target_id'] = rel_data['target_id']

    auctions['Source'] = rel_data.source_id.map(node_data.set_index('ID')['Person'])
    auctions['Target'] = rel_data.target_id.map(node_data.set_index('ID')['Person']).fillna("Pforzheimer")
    auctions['SourceYear'] = rel_data.source_id.map(node_data.set_index('ID')['AuctionYear']).fillna("")
    auctions['TargetYear'] = rel_data.target_id.map(node_data.set_index('ID')['AuctionYear']).fillna("")

    auctions['Source'] = auctions[['Source', 'SourceYear']].apply(lambda row: f"{row['Source']} ({row['SourceYear'] or 'Undated'})", axis=1)
    auctions['Target'] = auctions[['Target', 'TargetYear']].apply(lambda row: f"{row['Target']} ({row['TargetYear'] or 'Undated'})", axis=1)
    auctions['Target'] = auctions['Target'].replace('Pforzheimer (Undated)', 'Pforzheimer')

    auctions['Book'] = rel_data.source_id.map(node_data.set_index('ID')['CatalogNum'])
    auctions['Lot'] = rel_data.source_id.map(node_data.set_index('ID')['Lot'])

    auctions.to_csv("../5 - gephi/rel_auction_auction_with_pforz.csv", index=False)




if __name__ == '__main__':
    # correct_ids()
    # add_pforz()
    seller_seller()
    # auction_auction()
