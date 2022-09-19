import os
import time
import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options


def init_browser(headless):
    firefox_driver = os.path.join(os.getcwd(), "Drivers",
                                  'geckodriver.exe')  # See PyCharm help at https://www.jetbrains.com/help/pycharm/
    firefox_service = Service(firefox_driver)
    firefox_options = Options()
    firefox_options.headless = headless
    return webdriver.Firefox(service=firefox_service, options=firefox_options)


def get_tag_sample(vocab_file):
    with open(vocab_file) as f:
        return f.readline().strip()


def login(browser, wait, username, password, redirect=None):
    browser.get("https://recogito.pelagios.org/login")
    wait.until(lambda browser: browser.find_element(By.ID, "username"))

    username_field = browser.find_element(By.ID, "username")
    username_field.send_keys(username)
    password_field = browser.find_element(By.ID, "password")
    password_field.send_keys(password)
    password_field.submit()
    wait.until(lambda browser: browser.find_element(By.CLASS_NAME, 'user'))
    if redirect:
        browser.get(redirect)


def find_doc_links(browser, wait):
    wait.until(lambda browser: browser.find_elements(By.CLASS_NAME, 'row'))
    documents = browser.find_elements(By.CLASS_NAME, 'row')
    doc_links = [d.find_element(By.CLASS_NAME, 'title').get_attribute('href') for d in documents]

    new_doc_links = doc_links
    while len(new_doc_links) > 0:
        documents[-1].click()
        documents = browser.find_elements(By.CLASS_NAME, 'row')
        new_doc_links = [d.find_element(By.CLASS_NAME, 'title').get_attribute('href') for d in documents]
        doc_links += [n for n in new_doc_links if n not in doc_links]
    return doc_links


def rename_batches(browser):
    doc_links = find_doc_links(browser, wait)
    for d in doc_links:

        pass


def upload_tags_helper(browser, wait, vocab_file, tag_sample, doc_link):
    settings_url = doc_link.replace("part/1/edit", "settings?tab=preferences")
    browser.get(settings_url)
    wait.until(lambda browser: browser.find_element(By.ID, "upload-vocabulary"))
    time.sleep(1)
    browser.find_element(By.ID, "upload-vocabulary").send_keys(os.path.abspath(vocab_file))
    wait.until(lambda browser: browser.find_element(By.XPATH, f"//td[contains(text(),'{tag_sample}')]"))


def upload_tags(browser, wait, vocab_file, tag_sample):
    for d in doc_links:
        upload_tags_helper(browser, wait, vocab_file, tag_sample, doc_link=d)


if __name__ == "__main__":
    USERNAME = "lizfischer0"
    PASSWORD = "yFsdIcq6MLTG*!6a!o#"
    RECOGITO_FOLDER_URL = "https://recogito.pelagios.org/lizfischer0#b939d0fc-0da1-4801-9760-adfec2bdc36c"  # "https://recogito.pelagios.org/lizfischer0#95d2d801-4cd7-45a4-9d88-0bbf9605997f"
    VOCAB_FILE = "D:\Desktop\dissertation\data processing\\pforz tagging vocab.txt"
    HEADLESS = False

    tag_sample = get_tag_sample(VOCAB_FILE)

    browser = init_browser(HEADLESS)
    wait = ui.WebDriverWait(browser, 30)

    login(browser, wait, USERNAME, PASSWORD, RECOGITO_FOLDER_URL)
    doc_links = find_doc_links(browser, wait)
    rename_batches(browser, doc_links)
    #upload_tags(browser, wait, VOCAB_FILE, tag_sample)
