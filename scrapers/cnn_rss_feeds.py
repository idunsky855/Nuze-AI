import feedparser
import newspaper
import time
from datetime import datetime
from bs4 import BeautifulSoup
import requests # newspaper3k uses requests, good to have for potential future use


#### ! NOT UP TO DATE RSS FEEDS


# --- Configuration ---

# List of CNN RSS Feeds to scrape (Add or remove as needed)
# Found via https://cnn.com/services/rss/ (or similar sources)
CNN_FEED_URLS = [
    'http://rss.cnn.com/rss/cnn_topstories.rss',
    'http://rss.cnn.com/rss/cnn_world.rss',
    'http://rss.cnn.com/rss/cnn_us.rss',
    'http://rss.cnn.com/rss/cnn_allpolitics.rss',
    'http://rss.cnn.com/rss/money_latest.rss', # Business/Finance
    'http://rss.cnn.com/rss/cnn_tech.rss',
    'http://rss.cnn.com/rss/cnn_health.rss',
    'http://rss.cnn.com/rss/cnn_showbiz.rss', # Entertainment
    'http://rss.cnn.com/rss/cnn_travel.rss',
    'http://rss.cnn.com/rss/cnn_living.rss',
    'http://rss.cnn.com/rss/cnn_latest.rss'
]

# Delay between fetching individual article pages (in seconds)
# IMPORTANT: Be respectful. Do not set this too low. 5-10 seconds is a reasonable minimum.
FETCH_DELAY_SECONDS = 7

# Delay between processing different RSS feeds (in seconds)
FEED_DELAY_SECONDS = 2

# User-Agent string to identify your bot
USER_AGENT = 'MyEthicalNewsScraper/1.0 (Contact: your_email@example.com; Purpose: Personal news aggregation)'

# --- Helper Functions ---

def clean_summary(html_summary):
    """Removes HTML tags and common feed clutter from summary."""
    if not html_summary or not isinstance(html_summary, str):
        return "N/A"
    try:
        # Basic cleaning for known CNN feed clutter
        cleaned = html_summary.replace('<div class="feedflare"></div>', '')
        # Use BeautifulSoup to remove remaining HTML tags
        soup = BeautifulSoup(cleaned, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception:
        # Fallback if parsing fails
        return html_summary # Return original if cleaning fails

def get_article_full_text(article_url):
    """
    Attempts to fetch and parse the full text of an article using newspaper3k.
    Includes necessary delays and error handling.
    WARNING: Use this function cautiously and respect website terms.
    """
    print(f"  Attempting to fetch full text for: {article_url}...")
    try:
        # Configure newspaper article with user-agent
        config = newspaper.Config()
        config.browser_user_agent = USER_AGENT
        config.request_timeout = 15 # Set a timeout for requests

        article = newspaper.Article(article_url, config=config)
        article.download()

        # --- CRUCIAL DELAY ---
        print(f"    Waiting {FETCH_DELAY_SECONDS} seconds before parsing...")
        time.sleep(FETCH_DELAY_SECONDS)
        # --- END CRUCIAL DELAY ---

        article.parse()
        print("    Successfully parsed.")
        return article.text

    except newspaper.article.ArticleException as e:
        print(f"    Newspaper3k failed for {article_url}: {e}")
        return f"N/A - newspaper3k failed: {e}"
    except requests.exceptions.RequestException as e:
        print(f"    Network error fetching {article_url}: {e}")
        return f"N/A - Network error: {e}"
    except Exception as e:
        print(f"    Unexpected error processing {article_url}: {e}")
        return f"N/A - Unexpected error: {e}"

# --- Main Scraping Logic ---

def scrape_cnn_feeds(feed_urls, fetch_full_text=False):
    """
    Scrapes multiple CNN RSS feeds and optionally fetches full article text.
    """
    all_articles_data = []
    start_time = time.time()

    print("Starting CNN RSS Feed Scraping...")
    print(f"Processing {len(feed_urls)} feeds.")
    print(f"Fetching full text: {'Yes' if fetch_full_text else 'No'}")
    print(f"User Agent: {USER_AGENT}")
    print("-" * 40)

    for i, feed_url in enumerate(feed_urls):
        print(f"\n[{i+1}/{len(feed_urls)}] Processing Feed: {feed_url}")

        try:
            # Use the custom user-agent with feedparser if possible (depends on version/backend)
            # feedparser might handle this automatically with requests backend
            news_feed = feedparser.parse(feed_url, agent=USER_AGENT)

            # Check for parsing errors
            if news_feed.bozo:
                print(f"  Warning/Error parsing feed: {news_feed.bozo_exception}")

            if not news_feed.entries:
                print("  No entries found in this feed.")
                # Add delay even if feed is empty or fails, before next feed
                if i < len(feed_urls) - 1:
                     print(f"  Waiting {FEED_DELAY_SECONDS}s before next feed...")
                     time.sleep(FEED_DELAY_SECONDS)
                continue # Skip to the next feed

            print(f"  Feed Title: {news_feed.feed.get('title', 'N/A')}")
            print(f"  Found {len(news_feed.entries)} entries.")

            for entry in news_feed.entries:
                article_data = {}

                # 1. URL (Handle potential Feedburner links)
                article_data['URL'] = entry.get('feedburner_origlink', entry.get('link', 'N/A'))

                # 2. Title
                article_data['title'] = entry.get('title', 'N/A')

                # 3. Summary (Cleaned)
                raw_summary = entry.get('description', entry.get('summary', 'N/A'))
                article_data['summary'] = clean_summary(raw_summary)

                # 4. Timestamp (ISO Format)
                timestamp_parsed = entry.get('published_parsed', entry.get('updated_parsed', None))
                if timestamp_parsed:
                    try:
                        # Use UTC offset if available, otherwise assume local/feed time
                        article_data['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', timestamp_parsed)
                    except Exception:
                         article_data['timestamp'] = entry.get('published', entry.get('updated', 'N/A')) # Fallback
                else:
                    article_data['timestamp'] = entry.get('published', entry.get('updated', 'N/A'))

                # 5. Text (Placeholder - will be fetched if fetch_full_text is True)
                article_data['text'] = "N/A - Full text not fetched (requires separate step)"

                # Basic check for valid URL before adding
                if article_data['URL'] and article_data['URL'] != 'N/A':
                     all_articles_data.append(article_data)
                else:
                    print(f"  Skipping entry with missing URL: {article_data.get('title', 'No Title')}")


            print(f"  Finished processing entries for this feed.")

        except Exception as e:
            print(f"  ERROR processing feed {feed_url}: {e}")

        # Delay before processing the next feed
        if i < len(feed_urls) - 1:
            print(f"  Waiting {FEED_DELAY_SECONDS}s before next feed...")
            time.sleep(FEED_DELAY_SECONDS)

    print("\n" + "=" * 40)
    print(f"Finished scraping RSS feeds. Found {len(all_articles_data)} articles.")
    print(f"RSS scraping took: {time.time() - start_time:.2f} seconds")
    print("=" * 40)


    # --- Optional: Fetch Full Text ---
    if fetch_full_text:
        print("\nStarting Full Text Fetching (using newspaper3k)...")
        print(f"WARNING: This will access each article page individually.")
        print(f"         Respect CNN's Terms of Service and robots.txt.")
        print(f"         A delay of {FETCH_DELAY_SECONDS} seconds is applied between requests.")
        print("-" * 40)

        full_text_start_time = time.time()
        articles_processed = 0

        for article_data in all_articles_data:
            if article_data.get('URL') and article_data['URL'] != 'N/A':
                article_data['text'] = get_article_full_text(article_data['URL'])
                articles_processed += 1
                # Note: The delay is inside get_article_full_text()
            else:
                 article_data['text'] = "N/A - Invalid or missing URL"

        print("\n" + "=" * 40)
        print(f"Finished fetching full text for {articles_processed} articles.")
        print(f"Full text fetching took: {time.time() - full_text_start_time:.2f} seconds")
        print("=" * 40)

    return all_articles_data

# --- Execution ---
if __name__ == "__main__":
    # Set fetch_full_text to True to attempt fetching full text (USE WITH CAUTION!)
    # Set fetch_full_text to False to only get data from RSS feeds (Safer)
    FETCH_TEXT = False

    all_data = scrape_cnn_feeds(CNN_FEED_URLS, fetch_full_text=FETCH_TEXT)

    # --- Print Results ---
    print("\n--- Final Scraped Data ---")
    if not all_data:
        print("No articles were successfully scraped.")
    else:
        print(f"Total articles collected: {len(all_data)}")
        # Print details for the first few articles as an example
        for i, article in enumerate(all_data[:5]): # Print first 5
             print(f"\n--- Article {i+1} ---")
             print(f"URL: {article['URL']}")
             print(f"Title: {article['title']}")
             print(f"Timestamp: {article['timestamp']}")
             print(f"Summary: {article['summary'][:250]}...") # Print partial summary
             # Print text snippet differently based on whether it was fetched
             if FETCH_TEXT and not article['text'].startswith("N/A -"):
                  print(f"Text (snippet): {article['text'][:300]}...")
             else:
                  print(f"Text: {article['text']}") # Will show N/A or error message
             print("-" * 20)
        if len(all_data) > 5:
            print(f"\n... and {len(all_data) - 5} more articles collected (details not printed).")

    print("\nScript finished.")
    print(f"Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}. Location context: Kefar Sava, Center District, Israel.")

