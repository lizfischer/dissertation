import pandas as pd
from adjacency_lists import make_adjacency_list

df = pd.read_csv("Tite-overlaps-merged.tsv", sep="\t")


def person_book_edges():
    edges = pd.DataFrame(columns=["Source", "Target", "Type", "Avg Date", "Start Date", "End Date", "Transcription",
                                              "Book Certainty", "Date Certainty", "Person Certainty"])
    edges["Source"] = df["PERSON"]
    edges["Target"] = df["Book"]
    edges["Type"] = "Undirected"
    edges["Avg Date"] = df["Date (display)"]
    edges["Start Date"] = df["Date (earliest)"] if df["Date (earliest)"].str != "unknown date" else None# + "-01-01"
    edges["End Date"] = df["Date (latest)"] if df["Date (latest)"].str != "unknown date" else None# + "-12-31"
    edges["Transcription"] = df["QUOTE_TRANSCRIPTION"]
    edges["Book Certainty"] = pd.isna(df["Uncertain Book"])
    edges["Date Certainty"] = pd.isna(df["Uncertain date"])
    edges["Person Certainty"] = pd.isna(df["Uncertain Person"])

    edges.to_csv("../5 - gephi/rel_book_person.csv", index=False)


person_book_edges()


def basic_adjacency():
    make_adjacency_list(df, "PERSON", "Book", "../5 - gephi/rel_person_person-book.csv")
    make_adjacency_list(df, "Book", "PERSON", "../5 - gephi/rel_book_book-person.csv")


def loan_adjacency():
    df["Person_Date"] = df["PERSON"] + ", " + df["Date (display)"]
    make_adjacency_list(df, "Book", "Person_Date", "../5 - gephi/rel_book_book-loan.csv")


def loan_adjacency_fuzzy():
    pass
    # TODO: Books borrowed by the same person with 3 years of each other?

