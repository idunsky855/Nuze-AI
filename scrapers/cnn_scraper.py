import requests
# BeautifulSoup is no longer needed for finding links, but keep for potential future use or cleaning
# from bs4 import BeautifulSoup
import newspaper # Main library for build() and Article()
import time
from datetime import datetime
from urllib.parse import urljoin # To make relative URLs absolute
import re # For potential pattern matching

# --- Configuration ---

# List of CNN Section Pages to scrape for article links
CNN_SECTION_URLS = [
    'https://cnn.com/world',
    # 'https://cnn.com/politics',
    # 'https://cnn.com/business',
    # 'https://cnn.com/technology'
]

# Base URL for resolving relative links (still needed for newspaper.build context)
CNN_BASE_URL = 'https://cnn.com'

# Delay between processing different section pages (in seconds)
SECTION_PAGE_DELAY_SECONDS = 10 # Be very respectful

# Delay between fetching individual article details (in seconds)
FETCH_DELAY_SECONDS = 7 # Be very respectful

# User-Agent string to identify your bot
USER_AGENT = 'MyEthicalNewsScraper/1.2 (Contact: your_email@example.com; Purpose: Personal news aggregation)'

# --- Helper Functions ---

def get_article_full_text(article_url):
    """
    Attempts to fetch and parse the full text of an article using newspaper3k.Article.
    Includes necessary delays and error handling.
    WARNING: Use this function cautiously and respect website terms.
    """
    print(f"      Attempting newspaper3k.Article fetch for: {article_url}...")
    try:
        config = newspaper.Config()
        config.browser_user_agent = USER_AGENT
        config.request_timeout = 20 # Increased timeout

        article = newspaper.Article(article_url, config=config)
        article.download()

        # --- CRUCIAL DELAY ---
        print(f"        Waiting {FETCH_DELAY_SECONDS}s before parsing...")
        time.sleep(FETCH_DELAY_SECONDS)
        # --- END CRUCIAL DELAY ---

        article.parse()
        print("        Parsed successfully.")
        # Basic check if text extraction was meaningful
        if article.text and len(article.text) > 100: # Arbitrary length check
             return article.text
        else:
             return "N/A - newspaper3k parsed but extracted little/no text."

    except newspaper.article.ArticleException as e:
        print(f"        Newspaper3k.Article failed for {article_url}: {e}")
        return f"N/A - newspaper3k.Article failed: {e}"
    except requests.exceptions.RequestException as e:
        print(f"        Network error fetching {article_url}: {e}")
        return f"N/A - Network error: {e}"
    except Exception as e:
        print(f"        Unexpected error processing {article_url}: {e}")
        return f"N/A - Unexpected error: {e}"

def scrape_cnn_section_with_newspaper(section_url):
    """
    Uses newspaper.build() to find potential article links on a CNN section page.
    Returns a list of potential article URLs found and filtered.
    NOTE: Reliability may vary on complex sites like CNN.
    """
    print(f"  Attempting newspaper.build() for section: {section_url}")
    article_urls = set() # Use a set to avoid duplicate links

    try:
        # Configure newspaper build
        config = newspaper.Config()
        config.browser_user_agent = USER_AGENT
        config.request_timeout = 30 # Timeout for building the source
        # config.memoize_articles = False # Set to False to disable caching (more load, ensures freshness)
                                        # Default is True (caches based on URL)

        # Build the source object - this downloads and processes the section page
        source = newspaper.build(section_url, config=config)

        print(f"    newspaper.build() found {len(source.articles)} potential articles.")

        for article in source.articles:
            url = article.url
            if not url:
                continue

            # Make URL absolute (newspaper often does this, but double-check)
            absolute_url = urljoin(section_url, url) # Use section_url as base if needed

            # Apply the same filtering logic as before:
            # - Must contain a year (e.g., /2024/, /2025/) - common for CNN articles
            # - Must likely end with .html
            # - Avoid common non-article paths like /videos/, /gallery/, /profiles/
            if re.search(r'/\d{4}/\d{2}/\d{2}/', absolute_url) and absolute_url.endswith('.html') and \
               not any(sub in absolute_url for sub in ['/videos/', '/gallery/', '/profiles/', '/live-news/']):
                article_urls.add(absolute_url)

        print(f"    Extracted {len(article_urls)} unique, filtered article URLs.")
        return list(article_urls)

    except Exception as e:
        print(f"  Error during newspaper.build() for {section_url}: {e}")
        return [] # Return empty list on error

# --- Main Scraping Logic ---

def scrape_cnn_using_build(section_urls, fetch_full_text=False):
    """
    Scrapes CNN section pages using newspaper.build() for links,
    and optionally fetches full text using newspaper.Article().
    """
    # Use a set to store URLs processed in this run to avoid duplicates
    processed_urls_this_run = set()
    # Add persistent tracking load/save logic here if needed

    all_new_articles_data = []
    start_time = time.time()

    print("Starting CNN Scraping using newspaper.build()...")
    print(f"Processing {len(section_urls)} section pages.")
    print(f"Fetching full text: {'Yes' if fetch_full_text else 'No'}")
    print(f"User Agent: {USER_AGENT}")
    print("-" * 40)

    for i, section_url in enumerate(section_urls):
        print(f"\n[{i+1}/{len(section_urls)}] Processing Section: {section_url}")

        # Get potential article URLs using newspaper.build()
        found_urls = scrape_cnn_section_with_newspaper(section_url)

        new_urls_found_count = 0
        for url in found_urls:
            if url not in processed_urls_this_run:
                new_urls_found_count += 1
                print(f"    New URL found: {url}")
                processed_urls_this_run.add(url) # Mark as seen for this run

                article_data = {'URL': url, 'source_section': section_url} # Basic info

                # --- Optional: Fetch Full Details ---
                if fetch_full_text:
                    # Attempt to get details using newspaper3k.Article
                    article_text = get_article_full_text(url)
                    article_data['text'] = article_text
                    # Placeholders for other fields - newspaper.Article doesn't easily give these
                    # back to the main loop after fetching text in the helper function.
                    # If you need title/summary/timestamp reliably, you'd modify
                    # get_article_full_text to return a dictionary with these fields.
                    article_data['title'] = "N/A - Fetch details if needed"
                    article_data['summary'] = "N/A - Fetch details if needed"
                    article_data['timestamp'] = "N/A - Fetch details if needed"
                else:
                    # If not fetching full text now, add placeholders
                    article_data['text'] = "N/A - Full text fetching disabled"
                    article_data['title'] = "N/A - Requires fetching URL"
                    article_data['summary'] = "N/A - Requires fetching URL"
                    article_data['timestamp'] = "N/A - Requires fetching URL"

                all_new_articles_data.append(article_data)
                # Delay is inside get_article_full_text if fetching text

        print(f"  Found {new_urls_found_count} new article URLs in this section.")

        # Delay before processing the next section page
        if i < len(section_urls) - 1:
            print(f"\n  Waiting {SECTION_PAGE_DELAY_SECONDS}s before next section...")
            time.sleep(SECTION_PAGE_DELAY_SECONDS)

    print("\n" + "=" * 40)
    print(f"Finished scraping sections. Found {len(all_new_articles_data)} new articles in total.")
    print(f"Total unique URLs processed this run: {len(processed_urls_this_run)}")
    print(f"Scraping took: {time.time() - start_time:.2f} seconds")
    print("=" * 40)

    # Add persistent tracking save logic here if needed

    return all_new_articles_data

# --- Execution ---
if __name__ == "__main__":
    # Set fetch_full_text to True to attempt fetching full text (USE WITH CAUTION!)
    FETCH_TEXT = True # Set to True as user wants text

    new_data = scrape_cnn_using_build(CNN_SECTION_URLS, fetch_full_text=FETCH_TEXT)

    # --- Print Results ---
    print("\n--- New Articles Found ---")
    if not new_data:
        print("No new articles were found in the specified sections.")
    else:
        print(f"Total new articles collected: {len(new_data)}")
        # Print details for the first few articles as an example
        for i, article in enumerate(new_data[:5]): # Print first 5
             print(f"\n--- New Article {i+1} ---")
             print(f"URL: {article['URL']}")
             print(f"Source Section: {article['source_section']}")
             # Print other fields if they were fetched
             if FETCH_TEXT:
                 # Note: Title/Timestamp/Summary are placeholders here unless get_article_full_text is modified
                 print(f"Title: {article.get('title', 'N/A')}")
                 print(f"Timestamp: {article.get('timestamp', 'N/A')}")
                 print(f"Summary: {article.get('summary', 'N/A')[:250]}...")
                 text_snippet = article.get('text', 'N/A')
                 if not text_snippet.startswith("N/A -"):
                      print(f"Text (snippet): {text_snippet[:300]}...")
                 else:
                      print(f"Text: {text_snippet}") # Shows N/A or error
             else:
                  print("(Set FETCH_TEXT=True to attempt fetching details like title, text)")
             print("-" * 20)
        if len(new_data) > 5:
            print(f"\n... and {len(new_data) - 5} more new articles found (details not printed).")

    print("\nScript finished.")
    print(f"Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}. Location context: Kefar Sava, Center District, Israel.")

