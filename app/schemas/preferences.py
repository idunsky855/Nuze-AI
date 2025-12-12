from pydantic import BaseModel
from typing import List, Optional

class PreferencesUpdate(BaseModel):
    interests_vector: Optional[List[float]] = None
    metadata: Optional[dict] = None

class PreferencesResponse(BaseModel):
    interests_vector: List[float]
    metadata: Optional[dict] = None
