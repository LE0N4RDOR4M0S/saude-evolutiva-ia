import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY não encontrada")

    genai.configure(api_key=GOOGLE_API_KEY)