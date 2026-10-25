
import os

from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check the project's root .env file."
    )

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.5-flash-lite"


def ask_ai(question: str) -> str:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=question.strip(),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text
