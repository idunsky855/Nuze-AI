import aiohttp
import asyncio
import feedparser
from bs4 import BeautifulSoup
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

class SkyNewsScraper(BaseScraper):
    RSS_URLS = [
        'https://feeds.skynews.com/feeds/rss/home.xml',
        'https://feeds.skynews.com/feeds/rss/uk.xml',
        'https://feeds.skynews.com/feeds/rss/world.xml',
        'https://feeds.skynews.com/feeds/rss/us.xml',
        'https://feeds.skynews.com/feeds/rss/business.xml',
        'https://feeds.skynews.com/feeds/rss/politics.xml',
        'https://feeds.skynews.com/feeds/rss/technology.xml',
        'https://feeds.skynews.com/feeds/rss/entertainment.xml',
        'https://feeds.skynews.com/feeds/rss/strange.xml'
    ]

    async def scrape(self) -> List[Dict[str, Any]]:
        print("Starting Sky News scrape...")
        articles_data = []

        # Step 1: Parse RSS feeds to get URLs
        all_entries = []
        for feed_url in self.RSS_URLS:
            try:
                feed = feedparser.parse(feed_url)
                if feed.entries:
                    all_entries.extend(feed.entries)
            except Exception as e:
                print(f"Error parsing feed {feed_url}: {e}")

        # Deduplicate by link
        unique_entries = {entry.link: entry for entry in all_entries}.values()
        print(f"Found {len(unique_entries)} unique Sky News articles from RSS.")

        # Step 2: Fetch full text for each article
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(10)

            async def fetch_entry(entry):
                async with semaphore:
                    return await self._process_entry(session, entry)

            tasks = [fetch_entry(entry) for entry in unique_entries]
            results = await asyncio.gather(*tasks)

            for res in results:
                if res:
                    articles_data.append(res)

        print(f"Successfully scraped {len(articles_data)} Sky News articles.")
        return articles_data

    async def _process_entry(self, session, entry) -> Dict[str, Any]:
        url = entry.link
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Title (fallback to RSS title if needed, but page title is usually better)
                    title_tag = soup.find('h1')
                    title = title_tag.get_text(strip=True) if title_tag else entry.get('title', 'No Title')

                    # Summary (fallback to RSS summary)
                    summary = entry.get('summary', entry.get('description', ''))

                    # Timestamp
                    timestamp = None
                    if 'published_parsed' in entry:
                        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed)

                    # Content Extraction
                    # Sky News usually puts text in <div class="sdc-article-body-wrapper"> or similar
                    # We'll look for standard paragraph containers
                    article_body = soup.find('div', class_='sdc-article-body-wrapper')
                    if not article_body:
                        # Fallback for other layouts
                        article_body = soup.find('div', class_='sdc-article-body')

                    content = ""
                    if article_body:
                        paragraphs = article_body.find_all('p')
                        content = "\n\n".join([p.get_text(strip=True) for p in paragraphs])

                    if not content:
                        # Fallback: try to find all p tags in main content area if possible, or just skip
                        # For now, let's skip if we can't find the main body to avoid noise
                        return None

                    # Image
                    image_url = None
                    og_image = soup.find('meta', property='og:image')
                    if og_image:
                        image_url = og_image.get('content')

                    return {
                        "url": url,
                        "title": title,
                        "summary": summary,
                        "content": content,
                        "published_at": timestamp,
                        "image_url": image_url,
                        "source": "Sky News",
                        "text_hash": self.compute_hash(content)
                    }
        except Exception as e:
            print(f"Error fetching Sky News article {url}: {e}")
        return None

if __name__ == "__main__":
    scraper = SkyNewsScraper()
    articles = asyncio.run(scraper.scrape())
    print(f"Scraped {len(articles)} articles.")
    if articles:
        print(articles[0])
