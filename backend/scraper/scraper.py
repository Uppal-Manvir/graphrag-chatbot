import os
import json
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from backend.config import PAGES_JSONL


# Constants
BASE_URL = "https://www.madewithnestle.ca/sitemap"
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
#JSONL_PATH = os.path.join(DATA_DIR, 'pages.jsonl')
COOKIE_BUTTON_SELECTOR = '#onetrust-accept-btn-handler'

def init_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Initialize nd setup driver
    """
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def get_sitemap_urls(driver: webdriver.Chrome, sitemap_url: str = BASE_URL) -> list:
    """
    Get all urls from the sitemap
    """
    driver.get(sitemap_url)
    time.sleep(2)
    dismiss_cookie_banner(driver) #TODO update condintional to check if exists 

    elements = driver.find_elements(By.CLASS_NAME, "sitemap-sublist-item")
    urls = []
    for el in elements:
        try:
            link = el.find_element(By.TAG_NAME, "a").get_attribute("href")
            if link:
                urls.append(link)
        except Exception:
            continue
    return urls

def dismiss_cookie_banner(driver: webdriver.Chrome):
    """
    Accept cookies if there is a popup
    """
    try:
        btn = driver.find_element(By.CSS_SELECTOR, COOKIE_BUTTON_SELECTOR)
        btn.click()
        time.sleep(1)
    except Exception:
        # If accept button not found or click fails, proceed without blocking
        pass



def fetch_page(driver: webdriver.Chrome, url: str) -> str:
    """
    Fetch page and get its HTML
    """
    driver.get(url)
    time.sleep(2)
    return driver.page_source


def parse_html(html: str) -> str:
    """
    Strip HTML tags and return clean text.
    """
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def ensure_data_dir():
    """
    Create the data directory if it doesn't exist.
    """
    os.makedirs(DATA_DIR, exist_ok=True)


def save_record(record: dict):
    """
    Append a JSON record to the JSONL output file.
    """
    with open(PAGES_JSONL, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    """
    Full scraping run: fetch all sitemap URLs, scrape, parse, and save each page.
    """
    ensure_data_dir()
    driver = init_driver(headless=False)
    try:
        urls = get_sitemap_urls(driver)
        print(f"Found {len(urls)} URLs to scrape.")
        for url in urls:
            html = fetch_page(driver, url)
            text = parse_html(html)
            record = {
                "url": url,
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "text": text
            }
            save_record(record)
            print(f"Scraped and saved: {url}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
