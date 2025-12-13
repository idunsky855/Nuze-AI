import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import urljoin
import re
import sys
import os
import datetime

# Handle import resolution for both script and module usage
try:
    from .base_scraper import BaseScraper
except ImportError:
    # Add parent directory to path if running as script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scrapers.base_scraper import BaseScraper

class CNNScraper(BaseScraper):
    SECTION_URLS = [
        'https://edition.cnn.com/world',
        'https://edition.cnn.com/politics',
        'https://edition.cnn.com/business',
        'https://edition.cnn.com/technology'
    ]
    BASE_URL = 'https://edition.cnn.com'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    async def scrape(self) -> List[Dict[str, Any]]:
        print("Starting CNN scrape (aiohttp + BS4)...")
        articles_data = []

        async with aiohttp.ClientSession(headers={'User-Agent': self.USER_AGENT}) as session:
            # Step 1: Get all article URLs from sections
            tasks = [self._get_article_urls(session, section_url) for section_url in self.SECTION_URLS]
            results = await asyncio.gather(*tasks)

            all_urls = set()
            for urls in results:
                all_urls.update(urls)

            print(f"Found {len(all_urls)} unique CNN article URLs.")

            # Step 2: Fetch content concurrently
            # Limit concurrency
            semaphore = asyncio.Semaphore(10)

            async def fetch_with_sem(url):
                async with semaphore:
                    return await self._fetch_article_content(session, url)

            article_tasks = [fetch_with_sem(url) for url in all_urls]
            article_results = await asyncio.gather(*article_tasks)

            for res in article_results:
                if res:
                    articles_data.append(res)

        print(f"Successfully scraped {len(articles_data)} CNN articles.")
        return articles_data

    async def _get_article_urls(self, session, section_url):
        print(f"Fetching section: {section_url}")
        urls = set()
        try:
            async with session.get(section_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        full_url = urljoin(self.BASE_URL, href)

                        # Filter for article pattern: /YYYY/MM/DD/
                        # And ensure it's from edition.cnn.com
                        if '/202' in full_url and '/index.html' not in full_url:
                             if re.search(r'/\d{4}/\d{2}/\d{2}/', full_url):
                                 if 'edition.cnn.com' in full_url:
                                     urls.add(full_url)
        except Exception as e:
            print(f"Error fetching section {section_url}: {e}")

        print(f"Found {len(urls)} URLs in {section_url}")
        return list(urls)

    async def _fetch_article_content(self, session, url) -> Dict[str, Any]:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Title
                    title_tag = soup.find('h1')
                    title = title_tag.get_text(strip=True) if title_tag else 'No Title'

                    # Timestamp
                    timestamp = None
                    # Try meta tag first
                    meta_date = soup.find('meta', property='article:published_time')
                    if meta_date:
                        timestamp = meta_date.get('content')
                    else:
                        # Try time tag
                        time_tag = soup.find('time')
                        if time_tag and time_tag.has_attr('datetime'):
                            timestamp = time_tag['datetime']

                    # Summary (meta description)
                    summary_tag = soup.find('meta', attrs={'name': 'description'})
                    summary = summary_tag.get('content', '').strip() if summary_tag else ''

                    # Content
                    # Try generic paragraph extraction
                    # CNN often uses specific classes, but p tags are reliable enough if we filter
                    paragraphs = []

                    # Try to find the main article container first to avoid footer/nav text
                    # Common CNN containers: article, .article__content, .zn-body__paragraph
                    article_body = soup.find('div', class_='article__content') or \
                                   soup.find('div', class_='article-body') or \
                                   soup.find('article')

                    if article_body:
                        for p in article_body.find_all('p'):
                            text = p.get_text(strip=True)
                            if text:
                                paragraphs.append(text)
                    else:
                        # Fallback to all p tags
                        for p in soup.find_all('p'):
                            text = p.get_text(strip=True)
                            if text and len(text) > 20: # Filter short snippets
                                paragraphs.append(text)

                    content = "\n\n".join(paragraphs)

                    if not content or len(content) < 50:
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
                        "source": "CNN",
                        "text_hash": self.compute_hash(content)
                    }
        except Exception as e:
            print(f"Error fetching CNN article {url}: {e}")
        return None

if __name__ == "__main__":
    scraper = CNNScraper()
    articles = asyncio.run(scraper.scrape())
    print(f"Scraped {len(articles)} articles.")
    if articles:
        print(articles[0])
