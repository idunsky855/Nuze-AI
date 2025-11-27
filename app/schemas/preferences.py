from pydantic import BaseModel
from typing import List, Optional

class PreferencesUpdate(BaseModel):
    # We expect a list of floats representing the interest vector
    # In a real app, this might be a list of topics that we convert to a vector
    # For now, let's assume the client sends the vector or a list of topics
    # The diagram says "interests_vector", so let's support raw vector or topics
    interests_vector: Optional[List[float]] = None
    # topics: Optional[List[str]] = None # Future extension

class PreferencesResponse(BaseModel):
    interests_vector: List[float]
