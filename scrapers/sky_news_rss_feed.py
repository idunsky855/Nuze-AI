import feedparser
import time
from datetime import datetime


# All of Sky News RSS feeds
urls = [
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

# List to store dictionaries of scraped data
scraped_articles = []
for feed_url in urls:
    try:
        print(f"Fetching feed: {feed_url}")
        news_feed = feedparser.parse(feed_url)

        # Check for errors during parsing
        if news_feed.bozo:
            print(f"Warning/Error parsing feed: {news_feed.bozo_exception}")
            # Decide if you want to proceed despite potential issues
            # For this example, we'll proceed if entries exist

        if not news_feed.entries:
             print("No entries found in the feed.")

        else:
            print(f"Feed Title: {news_feed.feed.get('title', 'N/A')}")
            print(f"Number of entries found: {len(news_feed.entries)}")
            print("-" * 30)

            for entry in news_feed.entries:
                article_data = {}

                # 1. URL
                article_data['URL'] = entry.get('link', 'N/A')

                # 2. Title
                article_data['title'] = entry.get('title', 'N/A')

                # 3. Summary
                # Feeds might use 'summary' or 'description'
                article_data['summary'] = entry.get('summary', entry.get('description', 'N/A'))

                # 4. Timestamp
                # feedparser provides parsed tuples (preferred) or strings
                timestamp_parsed = entry.get('published_parsed', entry.get('updated_parsed', None))
                if timestamp_parsed:
                    # Convert the time tuple to a standard datetime object or ISO format string
                    # article_data['timestamp'] = datetime.fromtimestamp(time.mktime(timestamp_parsed))
                    article_data['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', timestamp_parsed)
                else:
                    # Fallback to string version if parsed version isn't available
                    article_data['timestamp'] = entry.get('published', entry.get('updated', 'N/A'))

                # 5. Text (Attempt extraction from 'content', often needs separate fetch)
                article_text = "N/A - Full text likely requires fetching URL"
                if 'content' in entry:
                    # content is usually a list of possible content types
                    for content_item in entry.content:
                        # Prioritize plain text if available
                        if content_item.get('type') == 'text/plain':
                            article_text = content_item.get('value', article_text)
                            break # Found plain text, stop looking
                        # Otherwise, take HTML (might need cleaning)
                        elif content_item.get('type') == 'text/html':
                             article_text = content_item.get('value', article_text)
                             # Note: This HTML might need cleaning with BeautifulSoup later
                        # Add more content types if needed
                    # If loop finished without finding text/plain, article_text might hold HTML or the default message

                # If 'content' doesn't exist or didn't yield text, keep the default message
                article_data['text'] = article_text

                # Add the extracted data dictionary to our list
                scraped_articles.append(article_data)

                # Optional: Add a small delay between processing entries
                # time.sleep(0.1)

    except Exception as e:
        print(f"An error occurred during feed processing: {e}")

    # Now print the extracted data from the list of dictionaries
    print("\n--- Extracted Article Data ---")
    if not scraped_articles:
        print("No articles were successfully processed.")
    else:
        for i, article in enumerate(scraped_articles):
            print(f"\n--- Article {i+1} ---")
            print(f"URL: {article['URL']}")
            print(f"Title: {article['title']}")
            print(f"Timestamp: {article['timestamp']}")
            print(f"Summary: {article['summary'][:200]}...") # Print partial summary
            if article['text'].startswith("N/A - Full text likely requires"):
                 print(f"Text: {article['text']}")
            else:
                 # If text was found in content, print a snippet (it might be long HTML)
                 print(f"Text (from feed content): {article['text'][:300]}...")
            print("-" * 20)

    # TODO:
    # --- Reminder ---
    # To get the GUARANTEED full text for 'text':
    # 1. Iterate through scraped_articles.
    # 2. For each article where 'text' indicates it needs fetching:
    # 3. Take the article['URL'].
    # 4. Use requests + BeautifulSoup or newspaper3k to fetch and parse the actual article page.
    # 5. Extract the full text content from the page's HTML structure.
    # 6. Update the 'text' field in your article_data dictionary.
    # Remember to add delays (time.sleep) when fetching individual article URLs!