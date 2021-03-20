import requests
from bs4 import BeautifulSoup

for num in range(1157, 1483):
#num = 1098
    url = f"https://www.dimev.net/record.php?recID={num}"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Titleout.json
    title = soup.find_all("i")[0].text.replace("\n", "")
    print(title)

    # Witnesses
    witnesses = []
    links = soup.find_all("a", href=True)
    for l in links:
        if "Records" in l['href']:
            witnesses.append(l['href'].split('=')[1])

    with open('out.json', 'a') as f:
        f.write(f"{num}; {title}; {witnesses}\n")