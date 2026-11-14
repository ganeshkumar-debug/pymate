import os, uvicorn
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n  🐍 PyMate v3 — Python AI Chatbot")
    print(f"  → http://localhost:{port}\n")
    uvicorn.run("api.index:app", host="127.0.0.1", port=port, reload=True)
