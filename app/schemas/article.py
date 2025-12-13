from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SourceDetail(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None

class ArticleResponse(BaseModel):
    id: Any
    title: str
    content: str
    source_url: Optional[str] = None
    publisher: Optional[str] = None
    published_at: Optional[datetime] = None
    image_url: Optional[str] = None
    language: Optional[str] = None
    category_scores: Optional[List[float]] = None
    sources: List[SourceDetail] = Field(default=[], validation_alias="sources_detail")
    is_liked: Optional[bool] = None  # Interaction state: True=liked, False=disliked, None=no interaction

    # Frontend expects 'author', we map publisher to it for now
    @property
    def author(self) -> Optional[str]:
        # Handle SynthesizedArticle case
        if self.publisher is None:
             return "Nuze AI"
        return self.publisher

    # validator for backward compatibility if passing dictionary
    @property
    def published_at_field(self) -> Optional[datetime]:
         if self.published_at:
              return self.published_at
         # Fallback for SynthesizedArticle which has generated_at
         if hasattr(self, 'generated_at'):
              return self.generated_at
         return None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
