import asyncio
import sys
import os
import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.article import Article
from app.models.synthesized_article import SynthesizedArticle, SynthesizedSource

async def backfill_articles(session: AsyncSession):
    print("Fetching articles without images...")
    result = await session.execute(select(Article).where(Article.image_url.is_(None)))
    articles = result.scalars().all()
    print(f"Found {len(articles)} articles to process.")

    async with aiohttp.ClientSession() as http_session:
        for i, article in enumerate(articles):
            if not article.source_url:
                continue

            try:
                print(f"[{i+1}/{len(articles)}] Fetching {article.source_url}...")
                async with http_session.get(article.source_url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        og_image = soup.find('meta', property='og:image')
                        if og_image:
                            image_url = og_image.get('content')
                            if image_url:
                                article.image_url = image_url
                                session.add(article)
                                print(f"  -> Found image: {image_url}")
                    else:
                        print(f"  -> Failed with status {response.status}")
            except Exception as e:
                print(f"  -> Error: {e}")

            # Commit periodically
            if (i + 1) % 10 == 0:
                await session.commit()

    await session.commit()
    print("Article backfill complete.")

async def backfill_synthesized_articles(session: AsyncSession):
    print("Fetching synthesized articles without images...")
    result = await session.execute(select(SynthesizedArticle).where(SynthesizedArticle.image_url.is_(None)))
    synth_articles = result.scalars().all()
    print(f"Found {len(synth_articles)} synthesized articles to process.")

    for i, synth in enumerate(synth_articles):
        # Get source articles
        # Manual join because lazy loading might be async issue here if not careful,
        # but let's try direct relationship access if loaded, else manual query.

        stmt = select(Article).join(SynthesizedSource).where(SynthesizedSource.synthesized_id == synth.id)
        res = await session.execute(stmt)
        sources = res.scalars().all()

        # Sort by processed/scraped/published at? Usually latest is best.
        # Let's filter for those with image_url
        valid_sources = [s for s in sources if s.image_url]

        if valid_sources:
             # Take the first one (or sort by date desc if needed)
             # Usually latest article is most relevant?
             valid_sources.sort(key=lambda x: x.published_at or x.scraped_at, reverse=True)
             synth.image_url = valid_sources[0].image_url
             session.add(synth)
             print(f"[{i+1}/{len(synth_articles)}] Updated synth {synth.id} with image from {valid_sources[0].source_url}")
        else:
             print(f"[{i+1}/{len(synth_articles)}] No source images found for synth {synth.id}")

    await session.commit()
    print("Synthesized article backfill complete.")

async def main():
    async with AsyncSessionLocal() as session:
        await backfill_articles(session)
        await backfill_synthesized_articles(session)

if __name__ == "__main__":
    asyncio.run(main())
