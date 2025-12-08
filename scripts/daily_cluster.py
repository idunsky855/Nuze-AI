import asyncio
import sys
import os
import json
import math
import ollama
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.future import select
from sqlalchemy import desc
from sklearn.cluster import KMeans

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.article import Article
from app.models.synthesized_article import SynthesizedArticle, SynthesizedSource

class ClusterService:
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    MODEL_NAME = "news-combiner"

    def __init__(self):
        self.client = ollama.Client(host=self.OLLAMA_HOST, timeout=600) # Longer timeout for generation

    async def run_daily_clustering(self):
        print("Starting daily clustering...")
        async with AsyncSessionLocal() as db:
            # 1. Fetch articles from the last 24 hours
            # 1. Fetch articles from the last 24 hours relative to the latest article
            # First, get the latest article date
            latest_article_result = await db.execute(
                select(Article.published_at)
                .where(Article.published_at.is_not(None))
                .order_by(desc(Article.published_at))
                .limit(1)
            )
            latest_date = latest_article_result.scalar_one_or_none()

            if not latest_date:
                print("No articles found in database. Exiting.")
                return

            cutoff = latest_date - timedelta(hours=24)
            print(f"Latest article date: {latest_date}. Fetching articles since {cutoff}...")

            # Ensure we only fetch articles that have category scores
            result = await db.execute(
                select(Article).where(
                    Article.published_at >= cutoff,
                    Article.published_at <= latest_date,
                    Article.category_scores.is_not(None)
                )
            )
            articles = result.scalars().all()
            print(f"Fetched {len(articles)} articles from the 24h window ending at {latest_date}.")

            if not articles:
                print("No articles found. Exiting.")
                return

            # 2. Cluster articles
            # We want groups of roughly 5 articles
            groups = self.group_articles_by_size(articles, num=5)
            print(f"Created {len(groups)} clusters.")

            # 3. Process each group
            for i, group_ids in enumerate(groups):
                print(f"Processing cluster {i+1}/{len(groups)} with {len(group_ids)} articles.")

                # Fetch full article objects for the group and sort by published_at desc
                # We already have them in 'articles' list, but let's filter and sort
                group_articles = [a for a in articles if a.id in group_ids]
                group_articles.sort(key=lambda x: x.published_at or datetime.min, reverse=True)

                # Take top 5 most current (though clustering logic already chunked them,
                # user said "the articles running through the llm should be the most current ones in each cluster")
                # If the cluster is larger than 5 (which shouldn't happen with the chunking logic unless we change it),
                # we take top 5. The chunking logic in test/cluster.py forces chunks of size `num`, so this is redundant but safe.
                target_articles = group_articles[:5]

                if not target_articles:
                    continue

                await self.process_cluster(db, target_articles)

    def group_articles_by_size(self, articles: List[Article], num: int, random_state: int = 42) -> List[List[Any]]:
        """
        Group articles into chunks of size `num`, ensuring that articles
        inside each group are as similar as possible (via clustering).
        """
        if num <= 0:
            raise ValueError("num must be positive")

        total = len(articles)
        if total == 0:
            return []

        # Extract vectors. Note: category_scores is a Vector object or list
        # We need to ensure it's a list of floats for KMeans
        vectors = []
        valid_articles = []
        for a in articles:
            if a.category_scores is not None:
                # Convert to list if it's not already
                vec = list(a.category_scores) if hasattr(a.category_scores, '__iter__') else a.category_scores
                vectors.append(vec)
                valid_articles.append(a)

        if not vectors:
            return []

        ids = [a.id for a in valid_articles]

        # how many clusters do we need?
        k = math.ceil(len(valid_articles) / num)

        if k < 1:
            k = 1

        # If we have fewer samples than clusters, KMeans will fail.
        # But k = ceil(total/num) <= total, so k <= total.
        # Exception: if total < k (impossible by math) or if k=total (each point is a cluster)

        if len(vectors) < k:
             # Should not happen given k calculation, but safety check
             k = len(vectors)

        kmeans = KMeans(
            n_clusters=k,
            random_state=random_state,
            n_init=10
        )

        labels = kmeans.fit_predict(vectors)

        # group by cluster similarity (label -> list of article ids)
        clusters: Dict[int, List[Any]] = {}
        for article_id, label in zip(ids, labels):
            clusters.setdefault(label, []).append(article_id)

        final_groups: List[List[Any]] = []

        # break each cluster into chunks of size `num`
        for label in sorted(clusters.keys()):
            group = clusters[label]
            # Sort group by date desc before chunking?
            # The user said "articles running through the llm should be the most current ones in each cluster"
            # So let's sort the whole cluster by date first
            # We need to find the articles again to sort them
            cluster_articles = [a for a in valid_articles if a.id in group]
            cluster_articles.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
            sorted_group_ids = [a.id for a in cluster_articles]

            for i in range(0, len(sorted_group_ids), num):
                final_groups.append(sorted_group_ids[i:i + num])

        return final_groups

    async def process_cluster(self, db, articles: List[Article]):
        # Prepare prompt
        prompt_articles = ""
        for i, article in enumerate(articles):
            prompt_articles += f"ARTICLE {i+1}:\n"
            prompt_articles += f"Title: {article.title}\n"
            prompt_articles += f"Content: {article.content[:2000]}\n\n" # Truncate content to fit context

        prompt = f"""Analyze the following articles, write one combined news article based only on them, and return the JSON object as specified:

ARTICLE SET:
{prompt_articles}

Return ONLY the JSON object.
"""

        print(f"Sending {len(articles)} articles to Ollama...")
        try:
            response = self.client.chat(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )

            raw_response = response.message.content
            result = self._parse_ollama_json(raw_response)

            if result:
                await self.save_synthesized_article(db, result, articles, prompt)
            else:
                print("Failed to parse Ollama response.")

        except Exception as e:
            print(f"Error calling Ollama: {e}")

    def _parse_ollama_json(self, raw_response):
        try:
            cleaned = raw_response.strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]
            return json.loads(cleaned)
        except Exception as e:
            print(f"JSON parse error: {e}")
            return None

    async def save_synthesized_article(self, db, result, source_articles, prompt):
        try:
            generated_article = result.get("generated_article")
            analysis = result.get("analysis")

            if not generated_article or not analysis:
                print("Missing generated_article or analysis in result.")
                return

            # Create SynthesizedArticle
            synth = SynthesizedArticle(
                title=result.get("title", "Combined News"),
                content=generated_article,
                generation_prompt=prompt,
                analysis=analysis
            )
            db.add(synth)
            await db.flush() # Get ID

            # Link sources
            for article in source_articles:
                source = SynthesizedSource(
                    synthesized_id=synth.id,
                    article_id=article.id
                )
                db.add(source)

            await db.commit()
            print(f"Saved synthesized article {synth.id}")

        except Exception as e:
            print(f"Error saving synthesized article: {e}")
            await db.rollback()

if __name__ == "__main__":
    service = ClusterService()
    asyncio.run(service.run_daily_clustering())
