import ollama
from typing import List, Dict
import json
import logging

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self, model_name="news-classifier", host="http://localhost:11434"):
        self.client = ollama.Client(host=host)
        self.model_name = model_name

    def classify_article(self, text: str) -> List[float]:
        """
        Classifies the article and returns a vector of scores for the categories.
        """
        prompt = f"""Analyze the following article and return the JSON object with category scores:
        {text[:2000]}
        """

        try:
            response = self.client.chat(
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
    def summarize_articles(self, articles_text: List[str]) -> str:
        """
        Summarizes a list of articles.
        """
        combined_text = "\n\n".join(articles_text)
        prompt = f"""Summarize the following news articles into a cohesive daily summary:
        {combined_text[:4000]}
        """

        try:
            response = self.client.chat(
                model=self.model_name, # Or use a summarization model
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            return response.message.content
        except Exception as e:
            logger.error(f"Error summarizing articles: {e}")
            return "Failed to generate summary."
