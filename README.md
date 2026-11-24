# 🚀 Blogger Agent MCP & AI Universal Content Generation Engine

**[English](README.md) | [Русский](README_RU.md)**

---

**Blogger Agent MCP** is an autonomous multi-agent system powered by the **Google Agent Development Kit (ADK)** and the flagship **Gemini 3.8 Flash** model (Vertex AI Global Endpoint). It is designed for deep analytical trend research via **Google BigQuery**, real-time live fact-checking across the web, automated multi-stop route construction in **Google Maps**, authoring comprehensive long-form articles on any specialized or cross-disciplinary topic, publishing documents to **Google Docs**, and dispatching drafts via **Gmail**.

---

## 🌟 Key Features

* 🧠 **Multi-Agent Universal Pipeline (Google ADK & Gemini 3.8 Flash):** Leverages specialized sub-agents: `BlogPlanner` *(Senior Content Strategist & Structural Editor)* and `BlogWriter` *(Master Writer)* orchestrated by the `Root Agent`. Connects to Vertex AI via the global dynamic load balancer (`GOOGLE_CLOUD_LOCATION="global"`).
* 🎯 **Smart Topic Scope Selector:**
  * 📍 **`scope="local"` (Hyperlocal):** For regional traditional products, local crafts, culinary traditions, and travel guides. Fetches trends strictly for the selected country (`geo`), eliminating global noise (`global_trends = []`).
  * 🌍 **`scope="global"` (Worldwide):** For global subjects (AI, quantum computing, cloud architecture).
  * 🌐 **`scope="both"` (Hybrid):** For cross-border topics, export markets, international trade, and transit tourism.
* 📊 **Official BigQuery Engine (Dual-Scope Trend Synthesis):** Replaces brittle unofficial web scrapers with **direct SQL queries against `bigquery-public-data.google_trends.international_top_terms`**. Accurate filtering by ISO country codes without proxies and free from 429/403 rate limits!
* 🛑 **Fail-Fast Quality Gate (Token Burn Protection):** No fake mock fallbacks. If BigQuery is unavailable or fails, the pipeline immediately halts at step 1 with an explicit error, preventing wasteful expenditure of thousands of LLM tokens on degraded articles.
* 🌐 **Native Google Search Grounding:** Built-in Gemini grounding backed by Google's live global index (5,000 free queries/month). The model verifies facts, regulations, pricing, and live statistics in real-time with automatic citations linked to primary sources. No unstable third-party scrapers or CAPTCHAs!
* 🗺 **Grand Tour Scenic Router (`get_scenic_travel_route`):** Generates complex road trips across multiple waypoints (**Point A ➔ B ➔ C ➔ D**) using Google Places & Routes API, with safe URL-encoding of non-ASCII characters (`urllib.parse.urlencode`) and interactive map generation.
* 🔒 **Long-Lived OAuth 2.0 Auth & Fallback Storage:** Configured in **In production** mode with `access_type="offline"` to ensure perpetual token renewal. In case of temporary Google Drive API issues, articles are automatically backed up to **Google Cloud Storage (GCS)** (zero risk of content loss).
* 🐳 **Lightweight Docker Image:** Stripped of unnecessary Node.js/npm dependencies, shrinking the container image by **~350 MB** (pure Python 3.11-slim, fast builds).

---

## 🏗 Pipeline Architecture

```
[User Request (Any specialized or multidisciplinary topic)]
        │
        ▼
[Root Agent (Blogger Orchestrator)]
        │
        ├──> 1. Smart Topic Scope Selector (prompts.py)
        │        ├──> scope="local"  -> Regional trends for selected country only
        │        ├──> scope="global" -> Worldwide global trends only
        │        └──> scope="both"   -> Synthesis of local and global trends
        │
        ├──> 2. Official BigQuery Trends Engine (get_google_trends)
        │        └──> `bigquery-public-data.google_trends.international_top_terms`
        │
        ├──> 3. Native Google Search Grounding (google_search)
        │        └──> 5,000 free queries/month across Google's global index
        │
        ├──> 4. Scenic Route Planner (get_scenic_travel_route / Places & Routes API)
        │
        ├──> 5. Outline Generation (Sub-Agent: BlogPlanner - Senior Content Strategist)
        │
        ├──> 6. Full Article Generation (Sub-Agent: BlogWriter - Master Writer)
        │
        └──> 7. Export & Delivery
                 ├── Google Drive / Docs API (save_to_google_drive)
                 ├── 🛡 Fallback: Google Cloud Storage (save_to_cloud_storage)
                 └── Gmail API Dispatch (send_article_email)
```

---

## ⚙️ Environment Variables (`.env`)

Create a `.env` file in the root directory of the project:

```env
# Google Cloud Vertex AI Model & Region
MODEL=gemini-3.8-flash
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Google Maps Platform API Key
GOOGLE_MAPS_API_KEY=AIzaSyYourGoogleMapsApiKeyHere12345

# Google Cloud Storage Bucket
GCS_BUCKET_NAME=your-gcs-bucket-name

# OAuth 2.0 Desktop Credentials (for Google Drive & Gmail)
OAUTH_CLIENT_ID=123456789012-yourclientid.apps.googleusercontent.com
OAUTH_CLIENT_SECRET=GOCSPX-yourClientSecretHere123456
OAUTH_REFRESH_TOKEN=1//04yourRefreshTokenHere_abcdefghijklmnopqrstuvwxyz

# Email recipient for notifications and drafts
NOTIFICATION_EMAIL=your_email@gmail.com
```

---

## 📦 Quickstart & Local Setup

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone -b bigquery https://github.com/googyaipro/blogger_agent.git
cd blogger_agent

python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. OAuth 2.0 Authorization (One-time Setup)
To obtain your long-lived `OAUTH_REFRESH_TOKEN`, run the token generation script:
```bash
python generate_oauth_token.py
```
Sign in with your Google Account in the browser window that opens, and copy the resulting `refresh_token` into your `.env` file and Google Cloud Secret Manager.

### 4. Run the Agent Locally
```bash
python agent.py
```

---

## 🐳 Deployment (Docker / Cloud Run / Dokploy)

### 1. Deploy to Google Cloud Run (Recommended)
```bash
gcloud run deploy bloggeragentmcpv03 \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --service-account="blogger-sa@your-gcp-project.iam.gserviceaccount.com" \
  --set-secrets="OAUTH_REFRESH_TOKEN=oauth-refresh-token:latest" \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE,MODEL="gemini-3.8-flash",GOOGLE_CLOUD_LOCATION="global",GCS_BUCKET_NAME="your-gcs-bucket-name",NOTIFICATION_EMAIL="your_email@gmail.com",GOOGLE_MAPS_API_KEY="AIzaSyYourGoogleMapsApiKeyHere12345"
```

---

### 2. Run with Docker Compose
```bash
docker compose up -d
```

---

### 3. Deploy to Dokploy (VPS)
1. Create a new **Application** in Dokploy dashboard.
2. Under **Build Type**, select `Dockerfile`.
3. Fill in the variables under the **Environment** tab.
4. Mount your Service Account JSON key `/app/gcp-key.json` under **File Mounts** for Vertex AI & BigQuery authentication.
5. Click **Deploy**.

---

## 📚 Additional Documentation

* 📑 [**Project Retrospective**](PROJECT_RETROSPECTIVE.md) — in-depth breakdown of architectural challenges, solutions, and benchmarks.
* 🛠 [**gcloud Cheatsheet**](gcloud_cheatsheet.md) — reference guide for infrastructure commands, Secret Manager, and Cloud Run.
* 📊 [**Interactive Pitch Deck**](blogger_agent_pitch_deck.html) — presentation mockup ready for PDF export.

---

## 📝 License
MIT License © 2026 Blogger Agent MCP Team.
