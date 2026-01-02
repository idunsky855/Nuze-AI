import asyncio
import os
import json
import ollama
import traceback
import logging
from datetime import datetime
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.article import Article
from scrapers.new_bbc_scraper import BBCScraper
from scrapers.new_cnn_scraper import CNNScraper
from scrapers.new_foxnews_scraper import FoxNewsScraper
from scrapers.new_nytimes_scraper import NYTimesScraper
from scrapers.new_sky_news_scraper import SkyNewsScraper
from app.services.llm_validator import validate_output

logger = logging.getLogger(__name__)

class IngestionService:
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    MODEL_NAME = "news-classifier"

    PROMPT_TEMPLATE = """Analyze the following article and return the JSON object:
{article_text}
"""

    def __init__(self):
        self.client = ollama.Client(host=self.OLLAMA_HOST, timeout=300)
        self.scrapers = [
            BBCScraper(),
            CNNScraper(),
            FoxNewsScraper(),
            NYTimesScraper(),
            SkyNewsScraper()
        ]

    async def run_daily_ingestion(self, dry_run=False):
        start_total = datetime.now()
        logger.info(f"Starting daily ingestion (Dry Run: {dry_run})...")

        # Step 1: Collect all articles from all scrapers
        all_articles = []
        for scraper in self.scrapers:
            try:
                start_scrape = datetime.now()
                articles = await scraper.scrape()
                scrape_duration = (datetime.now() - start_scrape).total_seconds()
                logger.info(f"Scraped {len(articles)} articles from {scraper.__class__.__name__} in {scrape_duration:.2f} seconds")
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error running scraper {scraper.__class__.__name__}: {e}")
                logger.debug(traceback.format_exc())

        logger.info(f"Total scraped articles from all sources: {len(all_articles)}")

        # Step 2: Batch check for duplicates (single DB query)
        all_urls = [a.get('url') for a in all_articles if a.get('url')]
        existing_urls = set()
        
        if not dry_run and all_urls:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Article.source_url).where(Article.source_url.in_(all_urls))
                )
                existing_urls = set(result.scalars().all())
            logger.info(f"Found {len(existing_urls)} existing articles in database (skipping duplicates)")

        # Step 3: Filter to only new articles
        new_articles = [a for a in all_articles if a.get('url') not in existing_urls]
        logger.info(f"Processing {len(new_articles)} new articles")

        # Step 4: Process only new articles
        start_process = datetime.now()
        for article_data in new_articles:
            await self.process_article(article_data, dry_run=dry_run, skip_dup_check=True)
        process_duration = (datetime.now() - start_process).total_seconds()
        logger.info(f"Processed {len(new_articles)} articles in {process_duration:.2f} seconds")

        total_duration = (datetime.now() - start_total).total_seconds()
        logger.info(f"Daily ingestion finished in {total_duration:.2f} seconds.")

    async def process_article(self, article_data, dry_run=False, skip_dup_check=False):
        url = article_data.get('url')
        if not url:
            return

        if dry_run:
            logger.info(f"[Dry Run] Would ingest: {url} - Title: {article_data.get('title')}")
            return

        async with AsyncSessionLocal() as db:
            try:
                # Check for duplicates (skip if already batch-checked)
                if not skip_dup_check:
                    result = await db.execute(select(Article).where(Article.source_url == url))
                    existing = result.scalars().first()

                    if existing:
                        logger.info(f"Skipping duplicate: {url}")
                        return

                logger.info(f"Ingesting: {url}")

                # Ollama Processing with Retry and Validation
                ollama_result = None
                for attempt in range(3):
                    logger.debug(f"Ollama attempt {attempt + 1}/3 for {url}")
                    raw_result = self._call_ollama(article_data.get('content', ''))

                    if raw_result:
                        is_valid, error_msg = validate_output(raw_result)
                        if is_valid:
                            ollama_result = raw_result
                            break
                        else:
                            logger.warning(f"Validation failed for {url} (Attempt {attempt + 1}): {error_msg}")
                    else:
                        logger.warning(f"Ollama returned None for {url} (Attempt {attempt + 1})")

                if not ollama_result:
                    logger.error(f"Failed to get valid Ollama result for {url} after 3 attempts. Skipping.")
                    return

                # Parse published_at
                published_at = article_data.get('published_at')
                if isinstance(published_at, str):
                    try:
                        # Handle Z suffix for Python 3.10 compatibility
                        if published_at.endswith('Z'):
                            published_at = published_at[:-1] + '+00:00'
                        published_at = datetime.fromisoformat(published_at)
                    except Exception as e:
                        logger.warning(f"Error parsing date {published_at}: {e}")
                        published_at = None

                # Create Article
                article = Article(
                    title=article_data.get('title'),
                    content=article_data.get('content'),
                    source_url=url,
                    publisher=article_data.get('source'),
                    published_at=published_at,
                    image_url=article_data.get('image_url'),
                    category_scores=self._extract_category_scores(ollama_result),
                    metadata_=ollama_result
                )

                logger.debug(f"category_scores type/value: {type(article.category_scores)} {article.category_scores}")

                db.add(article)
                await db.commit()
                logger.info(f"Saved article: {article.title}")

            except Exception as e:
                logger.error(f"Error processing article {url}: {e}")
                await db.rollback()

    def _call_ollama(self, text):
        if not text:
            return None

        try:
            prompt = self.PROMPT_TEMPLATE.replace("{article_text}", text)

            response = self.client.chat(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )

            raw_response = response.message.content
            return self._parse_ollama_json(raw_response)

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    def _parse_ollama_json(self, raw_response):
        try:
            cleaned = raw_response.strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

            result = json.loads(cleaned)

            # Normalize category structure if nested
            if "category" in result and isinstance(result["category"], dict):
                for k, v in result["category"].items():
                    result[k] = v
                del result["category"]

            if "Named_Entities" in result:
                result["Named Entities"] = result.pop("Named_Entities")

            return result
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            return None

    def _extract_category_scores(self, result):
        categories = [
            "Politics & Law", "Economy & Business", "Science & Technology",
            "Health & Wellness", "Education & Society", "Culture & Entertainment",
            "Religion & Belief", "Sports", "World & International Affairs",
            "Opinion & General News"
        ]

        # Force everything to float
        scores = [float(result.get(k, 0.0)) for k in categories]

        total = sum(scores)
        if total > 0 and abs(total - 5.0) > 0.01:
            scores = [round(s * 5.0 / total, 4) for s in scores]

        return scores

if __name__ == "__main__":
    # Basic logging setup for standalone execution
    logging.basicConfig(level=logging.INFO)
    service = IngestionService()
    asyncio.run(service.run_daily_ingestion(dry_run=True))
