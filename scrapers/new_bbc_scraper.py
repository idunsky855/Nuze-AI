import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import datetime
import sys
import os

# Handle import resolution for both script and module usage
try:
    from .base_scraper import BaseScraper
except ImportError:
    # Add parent directory to path if running as script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scrapers.base_scraper import BaseScraper

class BBCScraper(BaseScraper):
    BASE_URL = "https://www.bbc.com"
    CATEGORIES = ["news", "business", "innovation", "culture", "arts", "travel", "future-planet", "sport"]

    async def scrape(self) -> List[Dict[str, Any]]:
        print(f"Starting BBC scrape for categories: {self.CATEGORIES}")
        articles_data = []

        async with aiohttp.ClientSession() as session:
            # Step 1: Collect URLs
            tasks = [self._fetch_category_urls(session, cat) for cat in self.CATEGORIES]
            results = await asyncio.gather(*tasks)

            all_urls = set()
            for urls in results:
                all_urls.update(urls)

            print(f"Found {len(all_urls)} unique BBC article URLs.")

            # Step 2: Fetch Articles
            # Limit concurrency to avoid being blocked
            semaphore = asyncio.Semaphore(10)

            async def fetch_with_sem(url):
                async with semaphore:
                    return await self._fetch_article(session, url)

            article_tasks = [fetch_with_sem(url) for url in all_urls]
            article_results = await asyncio.gather(*article_tasks)

            for res in article_results:
                if res:
                    articles_data.append(res)

        print(f"Successfully scraped {len(articles_data)} BBC articles.")
        return articles_data

    async def _fetch_category_urls(self, session, category):
        url = f"{self.BASE_URL}/{category}"
        urls = []
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    if category == "sport":
                        # Sport pages have different promo structure
                        promo_blocks = soup.find_all('div', attrs={'data-testid': 'promo', 'type': 'article'})
                        for promo in promo_blocks:
                            a_tag = promo.find('a', href=True)
                            if a_tag and '/articles/' in a_tag['href']:
                                full_url = self._make_absolute(a_tag['href'])
                                urls.append(full_url)

                    # Standard article links
                    a_tags = soup.find_all('a', attrs={'data-testid': 'internal-link'})
                    for a in a_tags:
                        href = a.get('href')
                        if href and '/articles/' in href:
                            full_url = self._make_absolute(href)
                            urls.append(full_url)

        except Exception as e:
            print(f"Error fetching BBC category {category}: {e}")
        return urls

    async def _fetch_article(self, session, url) -> Dict[str, Any]:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Title
                    title_tag = soup.find('h1') or soup.find('title')
                    title = title_tag.get_text(strip=True) if title_tag else 'No Title'

                    # Summary
                    summary_tag = soup.find('p') # Heuristic: first paragraph
                    summary = summary_tag.get_text(strip=True) if summary_tag else ''

                    # Timestamp
                    timestamp = None
                    time_tag = soup.find('time')
                    if time_tag and time_tag.has_attr('datetime'):
                        timestamp = time_tag['datetime']

                    # Image
                    image_url = None
                    og_image = soup.find('meta', property='og:image')
                    if og_image:
                        image_url = og_image.get('content')

                    # Content
                    text_blocks = soup.find_all('div', attrs={'data-component': 'text-block'})
                    paragraphs = [p.get_text(strip=True) for block in text_blocks for p in block.find_all('p')]
                    content = "\n\n".join(paragraphs)

                    if not content:
                        return None

                    return {
                        "url": url,
                        "title": title,
                        "summary": summary,
                        "content": content,
                        "published_at": timestamp,
                        "image_url": image_url,
                        "source": "BBC",
                        "text_hash": self.compute_hash(content)
                    }
        except Exception as e:
            print(f"Error fetching BBC article {url}: {e}")
        return None

    def _make_absolute(self, href):
        if href.startswith('http'):
            return href
        return f"{self.BASE_URL}{href}"

if __name__ == "__main__":
    scraper = BBCScraper()
    articles = asyncio.run(scraper.scrape())
    print(f"Scraped {len(articles)} articles.")
    if articles:
        print(articles[0])
