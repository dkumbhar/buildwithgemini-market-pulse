# MarketPulse — Real-Time Finance & Portfolio Copilot

MarketPulse is an agentic financial strategist built on the **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Agent Platform**. It enables investors to analyze live market quotes, manage portfolio positions in Firestore, simulate compound growth, locate financial services via Google Maps, and generate AI visual media.

![MarketPulse Demo](demo.gif)

---

## 🌟 Wired Capabilities & Google Cloud Services

Based on the codebase in `app/` and `agents-cli-manifest.yaml`, MarketPulse implements the following tools and integrations:

- **Vertex AI Memory Bank (Long-Term Memory)**: Persists user investment goals, risk tolerance, and asset preferences across sessions using `PreloadMemoryTool` and `generate_memories_callback`.
- **Google Cloud Firestore**: Manages real-time portfolio positions, asset balances, and cost basis in Firestore database mode (`get_portfolio`, `add_or_update_portfolio_item`).
- **Google Cloud Storage (GCS)**: Stores generated asset graphics and video artifacts in a public GCS bucket (`gs://market-pulse-assets-...`) and serves public HTTPS media URLs.
- **AI Image Generation (Gemini 3.1)**: Generates investment milestone cards and asset graphics using `gemini-3.1-flash-lite-image` (`generate_asset_image`).
- **AI Video Generation (Gemini Omni)**: Generates animated market chart videos using `gemini-omni-flash-preview` in the `global` region (`generate_asset_video`).
- **Agent Engine Sandbox Code Executor**: Runs isolated Python code execution (`AgentEngineSandboxCodeExecutor`) for financial simulations, compound growth, and ROI calculations (`simulate_investment_growth`).
- **Google Maps APIs**: Geocodes locations and searches nearby banks, credit unions, and financial offices (`geocode_address`, `find_nearby_places`).
- **Real-Time Market & FX Data**: Fetches stock quotes via Yahoo Finance (`fetch_market_quote`) and currency exchange rates (`fetch_exchange_rates`).
- **A2UI v0.8 Rich Card UI**: Renders structured display cards (Basic Catalog v0.8) formatted via `a2ui_callback` for display in ADK Web and custom frontends.

---

## 🏗 Project Architecture

```
market-pulse/
├── app/
│   ├── __init__.py
│   ├── agent.py               # Main ADK Agent & App definition with tools & callbacks
│   ├── a2ui_utils.py          # A2UI v0.8 callback formatter
│   ├── portfolio_tools.py     # Firestore CRUD, Yahoo Finance & compound growth simulator
│   ├── image_tools.py         # Gemini 3.1 image generation & GCS uploader
│   ├── video_tools.py         # Gemini Omni video generation & GCS uploader
│   └── maps_tools.py          # Google Maps geocoding & places search
├── frontend/
│   ├── main.py                # FastAPI proxy server (Browser -> Agent Engine via A2A)
│   ├── Dockerfile             # Container configuration for Cloud Run
│   └── static/
│       └── index.html         # Custom chat frontend with built-in A2UI card renderer
├── agents-cli-manifest.yaml    # Agents CLI manifest & deployment configuration
├── deployment_metadata.json   # Deployed Agent Engine resource details
├── demo.gif                   # Looping video recording of the agent in action
├── pyproject.toml             # Project dependencies and virtual environment spec
└── README.md                  # Project documentation
```

---

## 🛠 Setup & Local Execution Instructions

### Prerequisites
- Python 3.11+
- `uv` package manager (`pip install uv`)
- Google Cloud SDK (`gcloud`) authenticated to your GCP project

### 1. Installation
Install project dependencies using `uv`:
```bash
uv sync
```

### 2. Environment Variables
Set the Google Maps API key in your environment or `.env` file:
```bash
export GOOGLE_MAPS_API_KEY="YOUR_KEY_HERE"
```

### 3. Running the Agent Locally (ADK Web Playground)
To launch the agent locally with Vertex AI Memory Bank support:
```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://YOUR_MEMORY_BANK_ID
```

### 4. Running the Custom Frontend Proxy Locally
To run the custom FastAPI proxy server:
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT/locations/us-east1/reasoningEngines/YOUR_ID"
export AGENT_DIRECTORY="app"
uvicorn main:app --host 0.0.0.0 --port 8080
```

---

## 🚀 Deployment Instructions

### Deploying the Agent to Agent Platform
Deploy the reasoning engine to Google Cloud Agent Platform:
```bash
agents-cli deploy --no-confirm-project --update-env-vars GOOGLE_MAPS_API_KEY=YOUR_KEY_HERE
```

### Deploying the Frontend to Cloud Run
Deploy the FastAPI container to Google Cloud Run:
```bash
cd frontend
gcloud run deploy market-pulse-frontend \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT/locations/us-east1/reasoningEngines/YOUR_ID",AGENT_DIRECTORY="app"
```
