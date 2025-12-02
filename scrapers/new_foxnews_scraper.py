import aiohttp
import asyncio
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
import dateutil.parser
import datetime

class FoxNewsScraper(BaseScraper):
    BASE_URL = "https://www.foxnews.com"
    CATEGORIES = ["us", "politics", "world", "opinion", "media", "entertainment", "sports", "lifestyle", "health", "category/tech/artificial-intelligence"]
    HEADERS = {'User-Agent': 'Mozilla/5.0'}

    async def scrape(self) -> List[Dict[str, Any]]:
        print("Starting Fox News scrape...")
        articles_data = []
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Get links
            tasks = [self._extract_article_links(session, cat) for cat in self.CATEGORIES]
            results = await asyncio.gather(*tasks)
            
            all_links = set()
            for links in results:
                all_links.update(links)
            
            print(f"Found {len(all_links)} unique Fox News article URLs.")

            # Step 2: Scrape articles
            semaphore = asyncio.Semaphore(10)
            
            async def fetch_with_sem(url):
                async with semaphore:
                    return await self._scrape_article(session, url)

            article_tasks = [fetch_with_sem(url) for url in all_links]
            article_results = await asyncio.gather(*article_tasks)
            
            for res in article_results:
                if res:
                    articles_data.append(res)

        print(f"Successfully scraped {len(articles_data)} Fox News articles.")
        return articles_data

    async def _extract_article_links(self, session, category):
        url = f"{self.BASE_URL}/{category}"
        links = []
        try:
            async with session.get(url, headers=self.HEADERS, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    articles = soup.find_all('article', class_='article')
                    for article in articles:
                        a_tag = article.find('a', href=True)
                        if a_tag:
                            href = a_tag['href']
                            # Check if it belongs to one of our categories (heuristic)
                            if any(href.startswith(f"/{cat.split('/')[0]}") for cat in self.CATEGORIES):
                                full_url = self._make_absolute(href)
                                links.append(full_url)
                        if len(links) >= 20:
                            break
        except Exception as e:
            print(f"Error fetching Fox News category {category}: {e}")
        return links

    async def _scrape_article(self, session, url) -> Dict[str, Any]:
        try:
            async with session.get(url, headers=self.HEADERS, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    title_tag = soup.find('h1')
                    title = title_tag.get_text(strip=True) if title_tag else 'No Title'

                    summary_tag = soup.find('meta', attrs={'name': 'description'})
                    summary = summary_tag['content'].strip() if summary_tag else ''

                    article_tag = soup.find('article')
                    
                    # Timestamp
                    timestamp = None
                    if article_tag:
                        time_element = article_tag.find('time')
                        if time_element:
                            raw_timestamp = time_element.get_text(strip=True)
                            try:
                                tzinfos = {
                                    "EST": -18000, "EDT": -14400,
                                    "CST": -21600, "CDT": -18000,
                                    "MST": -25200, "MDT": -21600,
                                    "PST": -28800, "PDT": -25200
                                }
                                dt = dateutil.parser.parse(raw_timestamp, tzinfos=tzinfos)
                                # Convert to UTC if possible
                                if dt.tzinfo:
                                    dt = dt.astimezone(datetime.timezone.utc)
                                    timestamp = dt.isoformat().replace('+00:00', 'Z')
                                else:
                                    # Assume UTC if naive, or just format it
                                    timestamp = dt.isoformat() + 'Z'
                            except:
                                pass
                    
                    # Content
                    content = ""
                    if article_tag:
                        paragraphs = article_tag.find_all('p')
                        content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
                    
                    if not content:
                        return None

                    return {
                        "url": url,
                        "title": title,
                        "summary": summary,
                        "content": content,
                        "published_at": timestamp,
                        "source": "Fox News",
                        "text_hash": self.compute_hash(content)
                    }
        except Exception as e:
            print(f"Error fetching Fox News article {url}: {e}")
        return None

    def _make_absolute(self, href):
        if href.startswith('http'):
            return href
        return f"{self.BASE_URL}{href}"

if __name__ == "__main__":
    scraper = FoxNewsScraper()
    articles = asyncio.run(scraper.scrape())
    print(f"Scraped {len(articles)} articles.")
    if articles:
        print(articles[0])
