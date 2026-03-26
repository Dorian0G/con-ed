# Deploying as a Public Web App (Free)

## Option A — Streamlit Community Cloud (recommended, easiest)

**No server, no cost, live URL in ~3 minutes.**

### Steps

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create utility-benchmark --public --push
   ```

2. **Go to [share.streamlit.io](https://share.streamlit.io)**
   - Sign in with GitHub
   - Click **"New app"**
   - Select your repo → branch `main` → Main file: `app.py`
   - Click **Deploy**

3. **Share the URL**
   You get a public URL like:
   `https://yourname-utility-benchmark-app-xyz.streamlit.app`
   Anyone can visit it — no login, no install.

### Notes
- Free tier: 1 GB RAM, sleeps after inactivity (wakes in ~10 seconds)
- No API keys needed — the app runs fully on simulated + scraped public data
- Streamlit handles HTTPS automatically

---

## Option B — Hugging Face Spaces (also free)

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) → New Space
2. Choose **Streamlit** as the SDK
3. Upload your files (or link a GitHub repo)
4. Hugging Face builds and hosts it automatically

---

## Option C — Railway / Render (more control)

Use if you want persistent storage or a custom domain.

**Dockerfile (add to project root):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

Deploy to [railway.app](https://railway.app) or [render.com](https://render.com) — both have free tiers.

---

## Microsoft Copilot integration (zero API cost)

The app generates a ready-to-paste prompt in the **Copilot** tab and in the Excel download. Users:

1. Click **"Open Copilot →"** (opens copilot.microsoft.com in a new tab)
2. Paste the prompt (one click from the app)
3. Get an executive summary, slide talking points, or strategic recommendations

**Requirements:** A free Microsoft account at outlook.com or any Microsoft 365 subscription. No API key, no billing, no backend changes.

---

## What requires NO setup
- ✅ Web scraping (public pages, no auth)
- ✅ Simulated fallback data (built in)
- ✅ Benchmark calculations (pure Python)
- ✅ Excel export (openpyxl, no cloud)
- ✅ Microsoft Copilot (user's own free account)
- ✅ Streamlit hosting (free tier)

## What is intentionally excluded
- ❌ OpenAI / Azure OpenAI API (would require billing + key management)
- ❌ Any paid data provider
- ❌ User accounts or authentication on the app itself
