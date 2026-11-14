# 🐍 PyMate — Dedicated Python AI Chatbot

A high-performance, Python-specialized AI chatbot designed for developers. Built with FastAPI, Google Gemini streaming API, and an aggressive cyber-shard black & violet aesthetic.

---

## ✨ Features

- **🐍 Deep Python Specialization**: Syntax, debugging, architectural patterns, FastAPI, Pandas, Asyncio, Django, and deep concepts.
- **⚡ Ultra-Low Latency Streaming**: Millisecond first-token response via direct Server-Sent Events (SSE) with `thinking_budget: 0` optimization on Gemini 2.5 models.
- **💬 Fault-Tolerant Natural Language**: Effortlessly handles broken English, shorthand, typos, and raw error tracebacks without lecturing on grammar.
- **🎨 ROG Cyber-Shard Theme**: Bespoke black (`#09090b`) and neon electric violet / magenta faceted UI with high-contrast Prism syntax highlighting.
- **🔒 Privacy First**: User API keys stay client-side in `localStorage` or environment secrets.
- **☁️ Multi-Cloud Deployment Ready**: Pre-configured for both **Vercel** serverless functions and **Supabase** Edge Functions + Postgres.

---

## 📁 Project Structure

```
pymate/
├── api/
│   └── index.py            # FastAPI serverless backend (Gemini SSE streaming)
├── public/
│   ├── index.html          # Web application UI
│   ├── css/
│   │   └── style.css       # Black & Violet cyber theme
│   ├── js/
│   │   └── app.js          # Client application logic (60fps stream, Prism highlight)
│   └── assets/
│       ├── logo.svg        # Cyber faceted Python emblem
│       └── favicon.svg     # Optimized browser tab icon
├── requirements.txt        # Minimal pinned dependencies
├── vercel.json             # Clean URL rewrites for Vercel
├── main.py                 # Local development launcher
├── .gitignore
└── README.md
```

---

## 🚀 Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run locally**:
   ```bash
   python main.py
   ```
   Open `http://localhost:8000` in your browser.

---

## ☁️ Deployment

### Vercel
Import this repository directly into [vercel.com/new](https://vercel.com/new). Vercel will automatically read `vercel.json` and deploy both the FastAPI backend and frontend.

### Supabase
The repository is also compatible with Supabase Edge Functions (Deno) and Postgres for persistent conversation storage.
