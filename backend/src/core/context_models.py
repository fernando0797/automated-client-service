
from pydantic import BaseModel

from src.core.models import RetrievalResult


class BuiltContext(BaseModel):
    context_text: str
    results_used: list[RetrievalResult]
    total_chars: int
