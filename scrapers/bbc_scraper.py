import aiohttp
import asyncio
import hashlib
from bs4 import BeautifulSoup

# Base URL and list of categories to scrape
base_URL = "https://www.bbc.com"
categories = ["news", "business", "innovation", "culture", "arts", "travel", "future-planet", "sport"]

# Async function to fetch a single article
async def fetch_article(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # 1. URL
                full_url = url

                # 2. Title
                title_tag = soup.find('h1') or soup.find('title')
                title = title_tag.get_text(strip=True) if title_tag else 'No Title'

                # 3. Summary (first <p>)
                summary_tag = soup.find('p')
                summary = summary_tag.get_text(strip=True) if summary_tag else ''

                # 4. Timestamp
                timestamp = ''
                time_tag = soup.find('time')
                if time_tag and time_tag.has_attr('datetime'):
                    timestamp = time_tag['datetime']
                elif time_tag:
                    timestamp = time_tag.get_text(strip=True)

                # 5. Text from all <div data-component="text-block">
                text_blocks = soup.find_all('div', attrs={'data-component': 'text-block'})
                paragraphs = [p.get_text(strip=True) for block in text_blocks for p in block.find_all('p')]
                full_text = "\n".join(paragraphs)

                # 6. Hash of text
                text_hash = hashlib.sha256(full_text.encode('utf-8')).hexdigest()

                return {
                    url: [full_url, title, summary, timestamp, full_text, text_hash]
                }

    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

# Fetch articles from a single category
async def fetch_articles_from_category(session, category):
    category_url = f"{base_URL}/{category}"
    try:
        async with session.get(category_url) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                article_urls = []

                # For "sport" category: use <div data-testid="promo" type="article">
                if category == "sport":
                    promo_blocks = soup.find_all('div', attrs={'data-testid': 'promo', 'type': 'article'})
                    for promo in promo_blocks:
                        a_tag = promo.find('a', href=True)
                        if a_tag and '/articles/' in a_tag['href']:
                            full_url = base_URL + a_tag['href']
                            article_urls.append(full_url)
                else:
                    # Default method for other categories
                    a_tags = soup.find_all('a', attrs={'data-testid': 'internal-link'})
                    for a in a_tags:
                        href = a.get('href')
                        if href and '/articles/' in href:
                            full_url = base_URL + href
                            article_urls.append(full_url)

                return list(set(article_urls))  # remove duplicates

    except Exception as e:
        print(f"Error loading category '{category}': {e}")
    return []


# Main async function to scrape all categories
async def fetch_all_categories(categories):
    articles_data = {}

    async with aiohttp.ClientSession() as session:
        all_article_urls = []

        # Step 1: collect URLs from all categories
        category_tasks = [fetch_articles_from_category(session, cat) for cat in categories]
        category_results = await asyncio.gather(*category_tasks)

        for urls in category_results:
            all_article_urls.extend(urls)

        all_article_urls = list(set(all_article_urls))  # deduplicate again globally

        # Step 2: fetch all articles in parallel
        article_tasks = [fetch_article(session, url) for url in all_article_urls]
        article_results = await asyncio.gather(*article_tasks)

        for result in article_results:
            if result:
                articles_data.update(result)

    return articles_data

# Run it
if __name__ == "__main__":
    articles = asyncio.run(fetch_all_categories(categories))

    for url, data in articles.items():
        print(f"URL: {data[0]}")
        print(f"Title: {data[1]}")
        print(f"Summary: {data[2]}")
        print(f"Timestamp: {data[3]}")
        print(f"Hash: {data[5]}")
        print(f"Text (preview): {data[4][:300]}...\n")

print(len(articles))