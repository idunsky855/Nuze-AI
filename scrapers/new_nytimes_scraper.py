from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import sys
import os

# Handle import resolution for both script and module usage
try:
    from .base_scraper import BaseScraper
except ImportError:
    # Add parent directory to path if running as script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scrapers.base_scraper import BaseScraper
from typing import List, Dict, Any
import time
from datetime import datetime

from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

class NYTimesScraper(BaseScraper):
    BASE_URL = "https://www.nytimes.com/"
    CATEGORIES = ["section/us", "section/world", "section/business", "section/arts", "spotlight/lifestyle", "section/opinion"]
    MAX_ARTICLES_PER_SECTION = 15

    async def scrape(self) -> List[Dict[str, Any]]:
        print("Starting NYT scrape (Selenium)...")
        # Run Selenium in a thread pool to avoid blocking the async event loop
        loop = asyncio.get_event_loop()
        articles_data = await loop.run_in_executor(None, self._run_selenium_scrape)

        print(f"Successfully scraped {len(articles_data)} NYT articles.")
        return articles_data

    def _run_selenium_scrape(self):
        all_articles = []
        max_workers = min(6, len(self.CATEGORIES))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._scrape_section, self.BASE_URL + cat): cat for cat in self.CATEGORIES}
            for future in as_completed(futures):
                category = futures[future]
                try:
                    result = future.result()
                    all_articles.extend(result)
                    print(f"Finished NYT category: {category} ({len(result)} articles)")
                except Exception as e:
                    print(f"Error in NYT category {category}: {e}")
        return all_articles

    def _scrape_section(self, section_url) -> List[Dict[str, Any]]:
        driver = self._configure_driver()
        articles = []
        try:
            driver.get(section_url)
            time.sleep(1)
            self._scroll_to_load_more(driver, self.MAX_ARTICLES_PER_SECTION)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            containers = soup.select('div.css-14ee9cx')

            for container in containers:
                if len(articles) >= self.MAX_ARTICLES_PER_SECTION:
                    break

                article_data = self._parse_container(container)
                if article_data:
                    articles.append(article_data)

        except Exception as e:
            print(f"Error scraping NYT section {section_url}: {e}")
        finally:
            driver.quit()

        return articles

    def _parse_container(self, container) -> Dict[str, Any]:
        article = container.find('article')
        if not article:
            return None

        a_tag = article.find('a', href=True)
        if not a_tag:
            return None
        href = a_tag['href']
        full_link = href if href.startswith("http") else self.BASE_URL.rstrip('/') + href

        title_tag = a_tag.find(['h2', 'h3'])
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        summary_tag = article.find('p')
        summary = summary_tag.get_text(strip=True) if summary_tag else ""

        paragraphs = article.find_all('p')
        content = "\n\n".join(p.get_text(strip=True) for p in paragraphs) if paragraphs else ""

        date_span = container.find('span', attrs={"data-testid": "todays-date"})
        date_str = date_span.get_text(strip=True) if date_span else None
        timestamp = self._parse_date(date_str)

        # Image (not available from section listing)
        image_url = None

        return {
            "url": full_link,
            "title": title,
            "summary": summary,
            "content": content,
            "published_at": timestamp,
            "image_url": image_url,
            "source": "NYTimes",
            "text_hash": self.compute_hash(content)
        }

    def _configure_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        service = Service(log_path="NUL")
        return webdriver.Chrome(options=options, service=service)

    def _scroll_to_load_more(self, driver, target_count):
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

    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, "%B %d, %Y")
            return dt.isoformat(timespec='milliseconds') + "Z"
        except Exception:
            return None

if __name__ == "__main__":
    scraper = NYTimesScraper()
    articles = asyncio.run(scraper.scrape())
    print(f"Scraped {len(articles)} articles.")
    if articles:
        print(articles[0])
