import requests, re
from bs4 import BeautifulSoup


def scrape_texts():
    for num in range(1, 6890):
        print(num)
        url = f"https://www.dimev.net/record.php?recID={num}"
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        # Titleout.json
        title_element = soup.find_all("i")[0]
        title = title_element.text.replace("\n", "")

        # Witnesses
        witnesses = []
        links = soup.find_all("a", href=True)
        for l in links:
            if "Records" in l['href']:
                witnesses.append(l['href'].split('=')[1])

        # Details
        details = title_element.find_next("div").find_all("div")
        details_string = '\t'.join([re.sub('\s+', ' ', e.text) for e in details])
        with open('texts-out.tsv', 'a', encoding='utf-8') as f:
            f.write(f"{num}\t{title}\t{details_string}\t{witnesses}\n")


def scrape_mss():
    url = f"https://www.dimev.net/Manuscripts.php?loc=&repos="
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    with open('mss-out.tsv', 'w', encoding='utf-8') as f:
        locations = soup.findAll("select", {"name": "loc"})[0].findChildren("option")
        for loc in locations:
            url = f"https://www.dimev.net/Manuscripts.php?loc={loc['value']}&repos=&search=SUBMIT"
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')

            items = soup.findAll("form")[0].find_next_siblings("div")
            for item in items:
                shelfmark = item.find_next("a")["href"].split("=")[1]
                name = item.text.replace("\n", "")
                print(shelfmark, name)
                f.write(f"{shelfmark}\t{name}\t{loc.text}\n")

scrape_texts()
scrape_mss()
