# PyMate API
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai

load_dotenv()  # reads .env on your computer; on Vercel the dashboard variables are used

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

app = FastAPI()

def get_client():
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set on the server")
    return genai.Client(api_key=GEMINI_API_KEY)