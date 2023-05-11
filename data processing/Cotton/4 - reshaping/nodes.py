import pandas as pd

df = pd.read_csv("Tite-overlaps-merged.tsv", sep="\t")


def make_book_nodes():
    books = df["Book"].unique()

    book_nodes = pd.DataFrame(columns=["ID", "Label", "Type"])
    book_nodes["ID"] = books
    book_nodes["Label"] = books
    book_nodes["Type"] = "Book"
    book_nodes.to_csv("nodes_books.csv", index=False)


def make_people_nodes():
    people = df["PERSON"].unique()
    people_nodes = pd.DataFrame(columns=["ID", "Label", "Type"])
    people_nodes["ID"] = people
    people_nodes["Label"] = people
    people_nodes["Type"] = "Person"
    people_nodes.to_csv("nodes_people.csv", index=False)
