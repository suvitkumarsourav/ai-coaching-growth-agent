
import os

from dotenv import load_dotenv
from google import genai

# Load the project's root .env file.
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY missing. Check the project's root .env file."
    )

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Explain what an AI Engineer does in three simple sentences.",
)

print("\nGemini AI Response:")
print(response.text)
