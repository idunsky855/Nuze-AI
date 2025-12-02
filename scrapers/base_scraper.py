from abc import ABC, abstractmethod
from typing import List, Dict, Any
import hashlib

class BaseScraper(ABC):
    """
    Abstract base class for all news scrapers.
    """

    def __init__(self):
        pass

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrapes articles and returns a list of dictionaries.
        Each dictionary should contain:
        - url: str
        - title: str
        - summary: str
        - content: str
        - published_at: str (ISO format or similar)
        - source: str (e.g., 'BBC', 'CNN')
        - text_hash: str
        """
        pass

    def compute_hash(self, text: str) -> str:
        """Helper to compute SHA256 hash of text."""
        if not text:
            return ""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
