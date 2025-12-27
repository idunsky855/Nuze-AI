import ollama
from typing import List, Dict
import json
import logging

import os

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self, model_name="news-classifier", host=None):
        if host is None:
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = ollama.AsyncClient(host=host)
        self.model_name = model_name

    async def classify_article(self, text: str) -> List[float]:
        """
        Classifies the article and returns a vector of scores for the categories.
        """
        prompt = f"""Analyze the following article and return the JSON object with category scores:
        {text[:3000]}
        """

        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            raw_response = response.message.content

            # Simple cleanup
            cleaned = raw_response.strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                cleaned = cleaned[start:end+1]

            result = json.loads(cleaned)

            # Flatten if needed
            if "category" in result and isinstance(result["category"], dict):
                for k, v in result["category"].items():
                    result[k] = v

            categories = [
                "Politics & Law", "Economy & Business", "Science & Technology",
                "Health & Wellness", "Education & Society", "Culture & Entertainment",
                "Religion & Belief", "Sports", "World & International Affairs",
                "Opinion & General News"
            ]

            scores = [float(result.get(k, 0)) for k in categories]
            return scores

        except Exception as e:
            logger.error(f"Error classifying article: {e}")
            # Return zero vector on error
            return [0.0] * 10

    # TODO: remove if not used
    async def summarize_articles(self, articles_text: List[str], user_preferences: dict = None) -> str:
        """
        Summarizes a list of articles using the news-summarizer model.
        """
        logger.info(f"Summarizing {len(articles_text)} articles with preferences: {user_preferences}")
        model = "news-summarizer"

        # Build the input for the model
        input_data = {
            "preferences": user_preferences if user_preferences else {},
            "articles": articles_text
        }

        # Serialize to string for the prompt
        import json
        data_json = json.dumps(input_data, indent=2)

        explicit_prompt = f"""
Here is the data (User Preferences + Articles):
{data_json}

INSTRUCTIONS:
Generate a Daily Briefing JSON object based on the above articles and preferences.
Structure:
{{
  "greeting": "...",
  "summary": "...",
  "key_points": ["..."]
}}
Output ONLY valid JSON.
"""

        try:
            response = await self.client.chat(
                model=model,
                messages=[{"role": "user", "content": explicit_prompt}],
                stream=False
            )
            raw_content = response.message.content
            # Clean up potential markdown code blocks
            cleaned = raw_content.strip()
            if cleaned.startswith("```"):
                # Find the first opening brace
                start = cleaned.find("{")
                # Find the last closing brace
                end = cleaned.rfind("}")
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end+1]
            return cleaned
        except Exception as e:
            logger.error(f"Error summarizing articles: {e}")
            return "Failed to generate summary."
