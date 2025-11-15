import asyncio
import aiohttp
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
import dateutil.parser

BASE_URL = "https://www.foxnews.com"
CATEGORIES = ["us", "politics", "world", "opinion", "media", "entertainment", "sports", "lifestyle", "health", "category/tech/artificial-intelligence"]
HEADERS = {'User-Agent': 'Mozilla/5.0'}

async def fetch(session, url):
    async with session.get(url, headers=HEADERS, timeout=10) as response:
        return await response.text()

async def extract_article_links(session, category):
    url = f"{BASE_URL}/{category}"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, 'html.parser')
    links = []

    articles = soup.find_all('article', class_='article')
    for article in articles:
        a_tag = article.find('a', href=True)
        if a_tag:
            href = a_tag['href']
            if any(href.startswith(f"/{cat}") for cat in CATEGORIES):
                full_url = BASE_URL + href
                if full_url not in links:
                    links.append(full_url)
        if len(links) >= 20:
            break

    return links

def normalize_timestamp(text):
    try:
        dt = dateutil.parser.parse(text)
        return dt.isoformat() + 'Z'
    except Exception:
        return None

async def scrape_foxnews_article(session, url):
    try:
        html = await fetch(session, url)
        soup = BeautifulSoup(html, 'html.parser')

        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else None

        summary_tag = soup.find('meta', attrs={'name': 'description'})
        summary = summary_tag['content'].strip() if summary_tag else None

        article_tag = soup.find('article')
        time_element = article_tag.find('time') if article_tag else None
        raw_timestamp = time_element.get_text(strip=True) if time_element else None
        timestamp = normalize_timestamp(raw_timestamp)

        paragraphs = article_tag.find_all('p') if article_tag else []
        text = '\n'.join(p.get_text(strip=True) for p in paragraphs)

        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest() if text else None

        return {
            url: {
                "title": title,
                "summary": summary,
                "timestamp": timestamp,
                "text": text,
                "hash": text_hash
            }
        }
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return {}

def print_articles(article_dict):
    for url, data in article_dict.items():
        print(f"\nURL: {url}")
        print(f"Title: {data.get('title')}")
        print(f"Summary: {data.get('summary')}")
        print(f"Timestamp: {data.get('timestamp')}")
        text_preview = data.get('text', '')[:300].strip().replace('\n', ' ')
        print(f"Text (preview): {text_preview}...")
        print(f"Hash: {data.get('hash')}")
    print(f"\nTotal articles scraped: {len(article_dict)}")

async def scrape_all():
    results = {}
    async with aiohttp.ClientSession() as session:
        # Step 1: Get 20 article links per category
        all_links = []
        link_tasks = [extract_article_links(session, category) for category in CATEGORIES]
        link_results = await asyncio.gather(*link_tasks)
        for link_list in link_results:
            all_links.extend(link_list)

        # Step 2: Scrape all articles concurrently
        article_tasks = [scrape_foxnews_article(session, url) for url in all_links]
        article_results = await asyncio.gather(*article_tasks)

        for article in article_results:
            results.update(article)

    return results

if __name__ == "__main__":
    scraped_data = asyncio.run(scrape_all())

    if scraped_data:
        print_articles(scraped_data)
