# MenuIQ

AI-powered restaurant menu optimization platform. MenuIQ analyzes transaction and ordering data to surface menu-engineering insights, cross-selling opportunities, and actionable recommendations — with an agentic chat assistant that answers questions grounded in pre-computed analytics.

**Stack:** React · FastAPI · PostgreSQL · Pandas · LangChain · Groq (Llama 3.3 70B)

---

## Features

- **Menu engineering matrix** — Classifies items into Star, Plowhorse, Puzzle, and Dog quadrants based on popularity and margin.
- **Market basket analysis** — Finds item pairings using support, confidence, and lift.
- **AI recommendations** — LLM turns deterministic analytics into prioritized menu actions (promote, bundle, reposition, retire).
- **Agentic chat** — LangChain agent with curated tools; the model fetches real metrics instead of inventing numbers.
- **Transaction upload** — Upload your own CSV/Excel file and analyze it in an isolated session.
- **Demo mode** — Works out of the box with bundled sample data (no upload required).

---

## Architecture

```
React UI  →  FastAPI  →  Pandas analytics (menu engineering, market basket)
                ↓
         LangChain agent + Groq LLM (recommendations & chat)
                ↓
         PostgreSQL (demo dataset)  |  In-memory sessions (uploaded data)
```

All metrics are computed in Python/Pandas first. The LLM only explains and recommends based on tool output — it never calculates sales, margins, or lift on its own.

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL** (for the demo dataset)
- **Groq API key** — [console.groq.com/keys](https://console.groq.com/keys)

---

## Quick start

### 1. Clone and configure environment

```bash
git clone <your-repo-url>
cd MenuIQ
cp .env.example .env
```

Edit `.env` and set your values:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/menuiq
GROQ_API_KEY=gsk-your-key-here
```

### 2. Set up the database (demo data)

```bash
createdb menuiq
psql -d menuiq -f Schema/schema.sql
cd Schema && python load_data.py
```

### 3. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API runs at **http://127.0.0.1:8000**  
Docs at **http://127.0.0.1:8000/docs**

### 4. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** (or the port Vite prints). The dev server proxies API calls to the backend.

---

## Uploading your own data

Upload a CSV or Excel file from the dashboard. The file is parsed into the same canonical shape used by the demo pipeline.

**Required columns** (flexible names accepted):

| Canonical | Accepted synonyms |
|-----------|-------------------|
| `order_id` | order, transaction_id, receipt_id, ticket_id, … |
| `item_name` | item, product, dish, description, … |
| `price` | unit_price, sale_price, amount, … |

**Profitability** — provide one of:

- `food_cost` (or `cost`, `cogs`, …)
- `margin` (or `profit`, …)
- **Or** enter an assumed food-cost % in the upload UI (`cost_pct`)

Optional: `category`, `quantity`

After upload, the app returns a `session_id`. All analytics and chat calls use that session until you reset to demo data.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `POST` | `/upload` | Ingest CSV/Excel → returns `session_id` |
| `GET` | `/menu-matrix` | Menu-engineering quadrant data |
| `GET` | `/menu-analysis` | Matrix + AI recommendations |
| `GET` | `/associations` | Top market-basket pairs |
| `POST` | `/chat` | Agentic Q&A over analytics |

Pass `?session_id=...` on GET routes (or `session_id` in the chat body) to query an uploaded dataset.

---

## Running tests

```bash
cd backend
source .venv/bin/activate
pytest
```

Tests cover ingest parsing, API routes, analytics tools, and formatters. LLM routes are mocked or skipped where a live key is not required.

---

## Project structure

```
MenuIQ/
├── backend/
│   ├── ai/              # LLM agent, tools, recommendations, formatters
│   ├── analytics/       # Menu engineering & market basket (Pandas)
│   ├── tests/
│   ├── main.py          # FastAPI app
│   ├── ingest.py        # Upload parsing & normalization
│   └── session_store.py # Per-upload in-memory sessions
├── frontend/
│   └── src/             # React dashboard, charts, chat, upload UI
├── Schema/
│   ├── schema.sql       # PostgreSQL DDL
│   ├── load_data.py     # Load demo CSVs
│   └── *.csv            # Sample menu & transaction data
├── .env.example
└── README.md
```

---

## Security notes

This repo is intended as a **portfolio / local-dev demo**, not production-ready for real customer data.

- `.env` is gitignored — never commit API keys.
- `API_KEY` auth is optional in dev; set it (and `VITE_API_KEY` on the frontend) for production.
- Uploaded sessions are stored in memory and evicted after a limit — not persisted.
- Rotate your Groq key if it was ever exposed.

See `.env.example` for optional production settings: `CORS_ORIGINS`, `API_KEY`, `CHAT_RATE_LIMIT`.

---

## License

MIT (or specify your license here)
