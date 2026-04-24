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
