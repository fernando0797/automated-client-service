from pydantic import BaseModel
from typing import List

from src.core.models import RetrievalResult


class BuiltContext(BaseModel):
    context_text: str
    results_used: List[RetrievalResult]
    total_chars: int
