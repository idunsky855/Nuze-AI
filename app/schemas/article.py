from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ArticleResponse(BaseModel):
    id: Any
    title: str
    content: str
    source_url: Optional[str] = None
    publisher: Optional[str] = None
    published_at: Optional[datetime] = None
    language: Optional[str] = None
    category_scores: Optional[List[float]] = None

    # Frontend expects 'author', we map publisher to it for now
    @property
    def author(self) -> Optional[str]:
        return self.publisher
    # Map 'metadata_' attribute from SQLAlchemy model to 'metadata' in JSON
    metadata_: Optional[Dict[str, Any]] = Field(default=None, serialization_alias="metadata")

    model_config = ConfigDict(from_attributes=True)
