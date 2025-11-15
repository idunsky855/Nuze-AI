from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://www.nytimes.com/"
CATEGORIES = ["section/us", "section/world", "section/business", "section/arts", "spotlight/lifestyle", "section/opinion"]
MAX_ARTICLES_PER_SECTION = 15

def hash_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def parse_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%B %d, %Y")
        return dt.isoformat(timespec='milliseconds') + "Z"
    except Exception:
        return "Invalid Timestamp"

def configure_driver():
    options = Options()
    options.add_argument("--headless=new")  # modern headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    service = Service(log_path="NUL")  # suppress chromedriver logs (Windows)
    return webdriver.Chrome(options=options, service=service)

def scroll_to_load_more(driver, target_count):
    SCROLL_PAUSE = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight")
    attempts = 0

    while attempts < 10:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        attempts += 1

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = soup.select('div.css-14ee9cx')
        if len(articles) >= target_count:
            break

def scrape_nyt_section(section_url):
    driver = configure_driver()
    driver.get(section_url)
    time.sleep(1)
    scroll_to_load_more(driver, MAX_ARTICLES_PER_SECTION)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    result_dict = {}
    containers = soup.select('div.css-14ee9cx')

    for container in containers:
        if len(result_dict) >= MAX_ARTICLES_PER_SECTION:
            break

        article = container.find('article')
        if not article:
            continue

        a_tag = article.find('a', href=True)
        if not a_tag:
            continue
        href = a_tag['href']
        full_link = href if href.startswith("http") else BASE_URL.rstrip('/') + href

        title_tag = a_tag.find(['h2', 'h3'])
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        summary_tag = article.find('p')
        summary = summary_tag.get_text(strip=True) if summary_tag else "No Summary"

        paragraphs = article.find_all('p')
        full_text = " ".join(p.get_text(strip=True) for p in paragraphs) if paragraphs else "No Content"

        date_span = container.find('span', attrs={"data-testid": "todays-date"})
        date_str = date_span.get_text(strip=True) if date_span else None
        timestamp = parse_date(date_str) if date_str else "No Timestamp"

        content_hash = hash_text(full_text)

        result_dict[full_link] = [title, summary, timestamp, full_text, content_hash]

    return result_dict

def parallel_scrape_categories(categories):
    all_articles = {}
    max_workers = min(6, len(categories))  # faster threading

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_nyt_section, BASE_URL + cat): cat for cat in categories}
        for future in as_completed(futures):
            category = futures[future]
            try:
                result = future.result()
                all_articles.update(result)
                print(f"Finished: {category} ({len(result)} articles)")
            except Exception as e:
                print(f"Error in {category}: {e}")
    return all_articles

# Main
if __name__ == "__main__":
    print("Starting parallel scraping...")
    all_articles = parallel_scrape_categories(CATEGORIES)

    for url, values in all_articles.items():
        print(f"\nURL: {url}")
        print(f"Title: {values[0]}")
        print(f"Summary: {values[1]}")
        print(f"Timestamp: {values[2]}")
        print(f"Text: {values[3][:100]}...")
        print(f"Hash: {values[4]}")

    print(f"\nTotal articles scraped: {len(all_articles)}")
