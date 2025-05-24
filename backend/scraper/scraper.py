import os
import json
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from backend.config import PAGES_JSONL


# Constants
BASE_URL = "https://www.madewithnestle.ca/sitemap"
BASE_URL2 = "https://www.madewithnestle.ca"
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
#JSONL_PATH = os.path.join(DATA_DIR, 'pages.jsonl')
COOKIE_BUTTON_SELECTOR = '#onetrust-accept-btn-handler'

def init_driver(headless: bool) -> webdriver.Chrome:
    """
    Initialize nd setup driver
    """
    options = Options()
    if headless: #Cloudflare blocked on madewithnestle
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
    #options.add_argument("window-size=1400,600")  
    prefs = {
        "profile.default_content_setting_values": {
            "images": 2,
            "stylesheet": 2
        }
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    # size = driver.get_window_size()
    # print(f'Window size: width = {size["width"]}px, height = {size["height"]}px')
    return driver


def get_sitemap_urls(driver: webdriver.Chrome, sitemap_url: str = BASE_URL) -> list:
    """
    Get all urls from the sitemap
    """
    driver.get(sitemap_url)
    time.sleep(2)
    dismiss_cookie_banner(driver) #TODO update condintional to check if exists 

    container = driver.find_element(By.CLASS_NAME, "sitemap")
    link_els = container.find_elements(By.TAG_NAME, "a")
    #elements = driver.find_elements(By.CLASS_NAME, "sitemap-sublist-item")
    urls = []
    for el in link_els:
        try:
            href = el.get_attribute("href")
            if href:
                urls.append(href)
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
    time.sleep(1)
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
#def hasLinks(html):

def expand_all(driver):
    """Click ‘More’ until it disappears."""
    while True:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, 'button[title="Load more items"]')
            btn.click()
            time.sleep(1)
            print("EXPANDED LOADED MORE")
        except NoSuchElementException:
            # no more button → we’re done
            break
        except Exception as e:
            # log and stop if something unexpected happens
            print(f"[expand_all] warning: {e}")
            break
def saveRecord(url, text):
    record = {
                "url": url,
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "text": text
            }
    save_record(record)

def get_main_links(driver, toCrawl):
    """Grab all same-domain links under <main>."""
    elems = driver.find_elements(By.CSS_SELECTOR, 'main a')
    hrefs = {e.get_attribute('href') for e in elems if e.get_attribute('href')}
    print("URLS FOUND BEFORE:::         ", len(hrefs))
    return {h for h in hrefs 
        if h.startswith(BASE_URL2) and h not in toCrawl and "recipe_brand" not in h and "recipe_tags_filter" not in h and "recipe_total_time" not in h}



def main():
    """
    Full scraping run: fetch all sitemap URLs, scrape, parse, and save each page.
    """
    ensure_data_dir()
    driver = init_driver(False)
    try:
        toCrawl = set(get_sitemap_urls(driver))
        print(f"Found {len(toCrawl)} URLs to scrape.") 
        seen = set()

        while toCrawl:
            print(f"{len(toCrawl)} LEFT TO CRAWL")
            url = toCrawl.pop()
            if url in seen:
                continue
            seen.add(url)

            driver.get(url)
            #time.sleep(1)
            dismiss_cookie_banner(driver)

            print(f"Crawling: {url}")

            expand_all(driver)
            
            html = driver.page_source
            text = parse_html(html)
            saveRecord(url, text)

            print(f"Scraped and saved: {url}")

            new_links = get_main_links(driver, toCrawl) - seen - toCrawl
            if new_links:
                print(f"  Found {len(new_links)} new links AFTER")
                toCrawl.update(new_links)

        #urls = get_sitemap_urls(driver)
        # print(f"Found {len(urls)} URLs to scrape.")
        # for url in urls:clear
        #     html = fetch_page(driver, url)
        #     if hasLinks(html):
        #         #Implement here
        #     text = parse_html(html)
            
        #     print(f"Scraped and saved: {url}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
