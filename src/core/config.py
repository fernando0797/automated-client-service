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

DEFAULT_ALREADY_ESCALATED_RESPONSE = (
    "Your ticket has already been escalated to our human support team."

    "A support specialist will review the case and follow up through the usual contact channel. Please keep an eye on your notifications for the next steps."
)

DEFAULT_FORCE_ESCALATION_RESPONSE = (
    "This case requires review by our human support team. "
    "I will escalate your ticket so a specialist can review it."
)

DEFAULT_CLOSED_TICKET_RESPONSE = (
    "This ticket is already closed, so no further actions can be applied to this conversation. "
    "If you still need help or the issue has appeared again, please open a new support ticket with the updated details so our team can assist you properly."
)

DEFAULT_RETRIEVAL_K = 5
