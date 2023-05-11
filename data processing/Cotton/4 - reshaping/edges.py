import pandas as pd
from adjacency_lists import make_adjacency_list

df = pd.read_csv("Tite-overlaps-merged.tsv", sep="\t")


def person_book_edges():
    edges = pd.DataFrame(columns=["Source", "Target", "Date", "Transcription",
                                              "Book Certainty", "Date Certainty", "Person Certainty"])
    edges["Source"] = df["PERSON"]
    edges["Target"] = df["Book"]
    edges["Date"] = df["Date (display)"]
    edges["Transcription"] = df["QUOTE_TRANSCRIPTION"]
    edges["Book Certainty"] = pd.isna(df["Uncertain Book"])
    edges["Date Certainty"] = pd.isna(df["Uncertain date"])
    edges["Person Certainty"] = pd.isna(df["Uncertain Person"])

    edges.to_csv("rel_book_person.csv", index=False)


make_adjacency_list(df, "PERSON", "Book", "../5 - gephi/rel_person_person-book.csv")
make_adjacency_list(df, "Book", "PERSON", "../5 - gephi/rel_book_book-person.csv")