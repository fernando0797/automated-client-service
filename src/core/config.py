from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_PATH = BASE_DIR / "knowledge"
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY is not set. "
        "Create a .env file in the project root and add GOOGLE_API_KEY=your_api_key"
    )

MAX_TURNS_PER_TICKET = 8
MAX_RAG_CALLS_PER_TICKET = 4

DEFAULT_ESCALATION_RESPONSE = (
    "Thank you for the information provided. "
    "This case requires review by our human support team to ensure it is handled correctly. "
    "We have escalated your ticket to a support specialist, who will review the details and follow up with the next steps. "
    "Please keep an eye on your usual contact channel for updates."
)

DEFAULT_CLOSED_TICKET_RESPONSE = (
    "This ticket is already closed, so no further actions can be applied to this conversation. "
    "If you still need help or the issue has appeared again, please open a new support ticket with the updated details so our team can assist you properly."
)

DEFAULT_RETRIEVAL_K = 5
