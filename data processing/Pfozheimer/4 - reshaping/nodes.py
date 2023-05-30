import pandas as pd
from pymarc import MARCReader

import json
# Book #s

# Collection/sale names

# Collection + year nodes for the same sale

# Book node:
# Catalog #
#
# Auction node:
# Collection
# Year
#
# Seller node:
# Name


def parse_marc():
    metadata = {}
    with open("D:\Desktop\dissertation\data processing\Pfozheimer\\1 - extraction\marc\pforz_utcatalog.mrc", 'rb') as fh:
        reader = MARCReader(fh)
        for record in reader:
            # TITLE
            try:
                num = record.get_fields('510')[0].get_subfields('c')[0]

            except Exception as e:
                continue

            if num not in metadata.keys():
                metadata[num] = {}
            metadata[num]['title'] = record.title()
            metadata[num]['author'] = record.author()
            metadata[num]['year'] = record.pubyear()

    return metadata


def make_book_nodes(book_data):
    marc = parse_marc()

    books = pd.DataFrame()
    books['Id'] = list(set(book_data['CatalogNum']))
    books['Label'] = books['Id']
    books['Title'] = [marc[book_id]['title'] if book_id in marc.keys() else None for book_id in list(books['Id'])]
    books['Author'] = [marc[book_id]['author'] if book_id in marc.keys() else None for book_id in list(books['Id'])]
    books['PubYear'] = [marc[book_id]['year'] if book_id in marc.keys() else None for book_id in list(books['Id'])]

    books.to_csv("../5 - gephi/nodes_books.csv", index=False)
    return books


def make_seller_nodes(seller_data):
    sellers = pd.DataFrame()
    sellers['Id'] = list(set(seller_data['Person']))
    sellers['Label'] = sellers['Id']
    sellers.to_csv("../5 - gephi/nodes_sellers.csv", index=False)

    return sellers


def make_auction_nodes(auction_data):
    auctions = pd.DataFrame()
    auctions['Id'] = list(auction_data['UUID'])
    auctions['Seller'] = list(auction_data['Person'])
    auctions['Year'] = list(auction_data['AuctionYear'])
    auctions['Year'] = auctions['Year'].fillna("")

    auctions['Label'] = auctions[['Seller', 'Year']].apply(lambda row: f"{row['Seller']} ({row['Year'] or 'Undated'})", axis=1)
    auctions.to_csv("../5 - gephi/nodes_auctions.csv", index=False)

    return auctions


if __name__ == '__main__':
    data = pd.read_csv("nodes_raw.tsv", delimiter="\t")

    # make_book_nodes(data)
    # make_seller_nodes(data)
    make_auction_nodes(data)
    print("Done")