import asyncio
import json
import ollama
import traceback
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.article import Article
from scrapers.new_bbc_scraper import BBCScraper
from scrapers.new_cnn_scraper import CNNScraper
from scrapers.new_foxnews_scraper import FoxNewsScraper
from scrapers.new_nytimes_scraper import NYTimesScraper
from scrapers.new_sky_news_scraper import SkyNewsScraper

class IngestionService:
    OLLAMA_HOST = "http://localhost:11434"
    MODEL_NAME = "news-classifier"
    
    PROMPT_TEMPLATE = """Analyze the following article and return the JSON object:
{article_text}
"""

    def __init__(self):
        self.client = ollama.Client(host=self.OLLAMA_HOST)
        self.scrapers = [
            BBCScraper(),
            CNNScraper(),
            FoxNewsScraper(),
            NYTimesScraper(),
            SkyNewsScraper()
        ]

    async def run_daily_ingestion(self, dry_run=False):
        print(f"Starting daily ingestion (Dry Run: {dry_run})...")
        
        for scraper in self.scrapers:
            try:
                articles = await scraper.scrape()
                print(f"Processing {len(articles)} articles from {scraper.__class__.__name__}")
                
                for article_data in articles:
                    await self.process_article(article_data, dry_run=dry_run)
                    
            except Exception as e:
                print(f"Error running scraper {scraper.__class__.__name__}: {e}")
                traceback.print_exc()

    async def process_article(self, article_data, dry_run=False):
        url = article_data.get('url')
        if not url:
            return

        if dry_run:
            print(f"[Dry Run] Would ingest: {url} - Title: {article_data.get('title')}")
            return

        async with AsyncSessionLocal() as db:
            try:
                # Check for duplicates
                result = await db.execute(select(Article).where(Article.source_url == url))
                existing = result.scalars().first()
                
                if existing:
                    print(f"Skipping duplicate: {url}")
                    return

                print(f"Ingesting: {url}")
                
                # Ollama Processing
                ollama_result = self._call_ollama(article_data.get('content', ''))
                
                if not ollama_result:
                    print(f"Failed to get Ollama result for {url}")
                    return

                # Create Article
                article = Article(
                    title=article_data.get('title'),
                    content=article_data.get('content'),
                    source_url=url,
                    publisher=article_data.get('source'),
                    published_at=article_data.get('published_at'),
                    category_scores=self._extract_category_scores(ollama_result),
                    metadata_=ollama_result 
                )
                
                db.add(article)
                await db.commit()
                print(f"Saved article: {article.title}")
                
            except Exception as e:
                print(f"Error processing article {url}: {e}")
                await db.rollback()

    def _call_ollama(self, text):
        if not text:
            return None
            
        try:
            # Truncate text if too long for context window (simple heuristic)
            truncated_text = text[:4000] 
            prompt = self.PROMPT_TEMPLATE.replace("{article_text}", truncated_text)
            
            response = self.client.chat(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            
            raw_response = response.message.content
            return self._parse_ollama_json(raw_response)
            
        except Exception as e:
            print(f"Ollama error: {e}")
            return None

    def _parse_ollama_json(self, raw_response):
        try:
            cleaned = raw_response.strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]
            
            result = json.loads(cleaned)
            
            # Normalize as per test script
            if "category" in result and isinstance(result["category"], dict):
                for k, v in result["category"].items():
                    result[k] = v
                del result["category"]
                
            if "Named_Entities" in result:
                result["Named Entities"] = result.pop("Named_Entities")
                
            return result
        except Exception as e:
            print(f"JSON parse error: {e}")
            return None

    def _extract_category_scores(self, result):
        categories = [
            "Politics & Law", "Economy & Business", "Science & Technology",
            "Health & Wellness", "Education & Society", "Culture & Entertainment",
            "Religion & Belief", "Sports", "World & International Affairs",
            "Opinion & General News"
        ]
        
        scores = [result.get(k, 0) for k in categories]
        
        # Normalize if needed (simple sum check)
        total = sum(scores)
        if total > 0 and abs(total - 5.0) > 0.01:
             scores = [round(s * 5.0 / total, 2) for s in scores]
             
        return scores

if __name__ == "__main__":
    service = IngestionService()
    asyncio.run(service.run_daily_ingestion(dry_run=True))
