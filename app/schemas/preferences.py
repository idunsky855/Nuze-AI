from pydantic import BaseModel
from typing import List, Optional

class PreferencesUpdate(BaseModel):
    interests_vector: Optional[List[float]] = None

class PreferencesResponse(BaseModel):
    interests_vector: List[float]
