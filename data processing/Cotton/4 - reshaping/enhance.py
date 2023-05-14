# TODO: Add tiles from BL website? https://hviewer.bl.uk/IamsHViewer/Default.aspx?mdark=ark:/81055/vdc_100000000035.0x0000b4
import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By


def get_shelf_mark(id):
    emperor = id.split(' ')[0]
    letter = id.split(' ')[1][0]
    num = id.split(' ')[1][1:]
    formatted_shelfmark = f"{emperor} {letter} {num}"
    return formatted_shelfmark

driver = webdriver.Firefox()
driver.implicitly_wait(10)
scroll_into_view = "arguments[0].scrollIntoView();"

def get_titles():
    driver.get("https://hviewer.bl.uk/IamsHViewer/Default.aspx?mdark=ark:/81055/vdc_100000000035.0x0000b4")
    assert "Browse Archives" in driver.title

    # Iterate over books
    new_books = []
    with open("../5 - gephi/nodes_books.csv") as f:
        books = [{k: v for k, v in row.items()}
             for row in csv.DictReader(f, skipinitialspace=True)]


    keys = books[0].keys()
    with open("../5 - gephi/nodes_books_with_titles.csv", 'w', encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, keys, lineterminator = '\n')
        dict_writer.writeheader()

        for book in books:
            shelfmark = get_shelf_mark(book["Label"])
            try:
                book_link = driver.find_element(By.PARTIAL_LINK_TEXT, shelfmark).find_element_by_xpath("../..")
                title = book_link.text.split(":")[1].strip()
                driver.execute_script(scroll_into_view, book_link)
                book_link.click()
                info_pane = driver.find_element_by_xpath("/html/body/div[1]/div[2]/div[2]/div")
                more_details = info_pane.find_element_by_partial_link_text("More details").get_attribute('href')
                book['Title'] = title
                book['FindingAid'] = more_details
            except:
                print(f"Not found {shelfmark}")
            dict_writer.writerow(book)

    """
Not found Vitellius F IX
Not found Cleopatra A II
Not found London B ritish
Not found Appendix X LI
Not found Caligula E XII
Not found Caligula A XII
    """

get_titles()
