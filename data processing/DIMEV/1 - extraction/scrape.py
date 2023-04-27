from bs4 import BeautifulSoup
import requests
import re
import csv
import json
import urllib.parse
import logging
import pprint
import time
import os

logging.basicConfig(filename='scrape.log', level=logging.WARNING,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)


def _collapse_whitespace(string):
    """ Remove conescutive, leading, and trailing whitespace from a string """
    return re.sub(r'\s{2,}', ' ', string).strip()


# MSS
def _get_repositories():
    list_url = "https://www.dimev.net/Manuscripts.php"
    page = requests.get(list_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    repos = soup.findAll("select", {"name": "repos"})[0].findChildren("option")
    repos = repos[2:]  # skip the "Select: Repository" and blank options
    return [r['value'] for r in repos]


def get_repo_mss(repo):
    mss = {}
    repo_url = f"https://www.dimev.net/Manuscripts.php?repos={urllib.parse.quote_plus(repo)}"
    page = requests.get(repo_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    first_ms = soup.find_all('form')[0].find_next_sibling('div')
    if not first_ms:
        return None
    location = re.search(r'\d\.\s*(.+?),', first_ms.text)
    location = location.group(1) if location else None

    current_ms = first_ms
    while current_ms:
        ms_link = current_ms.find_next('a')
        ms_id = ms_link['href'].split('=')[1]
        ms_name = ms_link.text
        current_ms = current_ms.find_next_sibling('div')
        mss[ms_id] = {'name': ms_name, 'location': location, 'repository': repo}
    return mss


def get_all_mss(log=False):
    repositories = _get_repositories()
    # repositories = ["Edinburgh University Library"]
    with open('mss_info.csv', 'w', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, delimiter='|', lineterminator='\n')
        writer.writerow(['ID', 'Name', 'Location', 'Repository'])
        for repo in repositories:
            if log:
                print(repo)
            mss = get_repo_mss(repo)
            if not mss: continue
            for ms in mss:
                writer.writerow([ms, mss[ms]['name'], mss[ms]['location'], mss[ms]['repository']])


# RECORDS
def _fetch_record_html(number):
    """ Get the HTML for a record in the DIMEV

    Args:
        number: the DIMEV number of the record to get

    Returns:
        BeautifulSoup object for the page
    """
    URL = f"https://www.dimev.net/record.php?recID={number}"
    page = requests.get(URL)
    return BeautifulSoup(page.content, "html.parser")


def _bold_headers_to_key_value_pairs(elems, collapse_whitespace=False):
    d = {}
    for div in elems:
        field = div.find('b').text
        value = div.text.replace(field, '')  # get just the value w/o the field name
        if collapse_whitespace:
            value = _collapse_whitespace(value)
        field = re.sub(r':\s*', '',
                       field)  # do this after the field is removed from value so colon is removed from both
        d[field] = value
    return d


def get_record(dimev_num):
    soup = _fetch_record_html(dimev_num)

    # Header (Title/First Line)
    header_element = soup.find_all("i")[0]
    header = _collapse_whitespace(header_element.text)

    # Content wrapper
    content_wrapper = header_element.parent.parent

    # Details
    details_wrapper = header_element.find_next("div")
    details_elements = details_wrapper.find_all("div", recursive=False)

    record = {'_id': dimev_num,
              '_header': header,
              **_bold_headers_to_key_value_pairs(details_elements[1:], collapse_whitespace=True),
              '_description': _collapse_whitespace(details_elements[0].text),
              '_witnesses': {}}

    # Get all witnesses under the "Manuscript Witnesses" header
    witness_header = content_wrapper.find_next('span', string='Manuscript Witnesses:')
    witness_elem = witness_header.find_next_sibling('div') if witness_header else None
    while witness_elem:
        if witness_elem.name in ['br', 'hr']:  # To end the loop before Print Witnesses, where present
            break

        source_link_elem = witness_elem.find_all('a')[1]
        source_id = source_link_elem['href'].split('=')[1]

        witness_notes = witness_elem.find_all("div", recursive=False)
        witness_notes = _bold_headers_to_key_value_pairs(witness_notes)

        record['_witnesses'][source_id] = witness_notes

        folio = ''.join([s.text for s in source_link_elem.next_siblings if s.name != 'div']).strip()
        folio = re.sub(r'^, ', '', folio)
        record['_witnesses'][source_id]['folio'] = folio

        witness_elem = witness_elem.find_next_sibling()

    return record


def get_all_records(log=False):
    # DIMEV has 6889 entries as of 2/9/2023

    for i in range(881, 885):
        if log: print(i)
        with open(f'records/{i}.json', 'w') as f:
            try:
                json.dump(get_record(i), f, indent=4)
            except Exception as e:
                logger.error(f'Error at DIMEV no. {i}', exc_info=e)


def combine_records():
    files = os.listdir('records')
    files.sort(key=lambda f: int(re.sub('\D', '', f)))
    all_records = {}
    for file in files:
        print(file)
        with open(f'records/{file}', 'r') as infile:
            item = json.load(infile)
        all_records[item['_id']] = item
    with open('all_records.json', 'w') as outfile:
        json.dump(all_records, outfile)


start = time.time()

# get_all_records(log=True)
# combine_records()
runtime = time.time() - start
print(f"Finished in {time.strftime('%H:%M:%S', time.gmtime(runtime))}")
