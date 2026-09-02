from google import genai

from app.core.config import settings


client = genai.Client(api_key=settings.gemini_api_key)