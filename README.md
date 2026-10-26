# UK Wind Power Forecast Dashboard

A web application for visualizing and evaluating UK national wind power generation forecasts against actuals, built for energy utility procurement teams making day-ahead market decisions.

**Data source:** [Elexon BMRS](https://bmrs.elexon.co.uk/) — FUELHH (actuals) and WINDFOR (forecasts) datasets for January 2026.

## Features

- **Actual vs Forecast Comparison** — Hourly time-series chart overlaying real wind generation with the latest available forecast
- **Accuracy Metrics** — MAE, RMSE, MAPE, bias, and correlation computed across the selected date range
- **Daily Forecast Bias** — Bar chart showing over/under-forecasting patterns per day
- **Daily MAPE Trend** — Area chart tracking percentage error over time
- **Hourly Error Profile** — Reveals which hours of the day have the least reliable forecasts
- **Date Range Filtering** — Adjustable date picker scoped to January 2026

## Project Structure

```
├── api/                    # Vercel serverless Python backend
│   └── index.py            # FastAPI app (all endpoints, data fetching, analysis)
├── backend/                # Local/Docker Python backend (pandas/numpy)
│   ├── main.py             # API endpoints and app setup
│   ├── data_fetcher.py     # Elexon API integration
│   ├── analysis.py         # Forecast accuracy computations
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/               # React (Vite) frontend
│   ├── src/
│   │   ├── App.jsx         # Main dashboard with tabs
│   │   ├── components/     # Chart and metric components
│   │   ├── services/       # API client
│   │   └── hooks/          # Custom React hooks
│   ├── nginx.conf          # Docker reverse proxy config
│   └── Dockerfile
├── docker-compose.yml      # Multi-container orchestration (local)
├── vercel.json             # Vercel deployment config
├── requirements.txt        # Serverless Python dependencies
└── README.md
```

## How to Start

### With Docker (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Without Docker (development)

**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173 with API proxy to backend.

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/actuals` | Wind generation actuals (FUELHH, fuelType=WIND) |
| `GET /api/forecasts` | Wind generation forecasts (WINDFOR) |
| `GET /api/accuracy` | Computed accuracy metrics, daily & hourly breakdowns |
| `GET /api/comparison` | Merged actual vs latest forecast per hour |
| `GET /api/health` | Health check |

All endpoints accept `date_from` and `date_to` query parameters (YYYY-MM-DD).

## Deployed Application

**Live:** https://gridbricks-psi.vercel.app

Hosted on Vercel — frontend as static build, backend as Python serverless functions.

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + Vite | Fast dev experience, component-based UI |
| Charts | Recharts | React-native charting, responsive & interactive |
| HTTP Client | Axios | Promise-based, clean API abstraction |
| Backend | Python FastAPI | Async-first, auto-docs, type validation |
| Data Source | Elexon BMRS API | Official UK energy market data |
| Deployment | Vercel | Zero-config frontend + serverless Python |
| Local Dev | Docker Compose | Reproducible multi-service setup |

## Design Decisions

- **Pure Python serverless backend** — The Vercel deployment uses only stdlib + FastAPI + httpx (no pandas/numpy) to stay within serverless size and runtime constraints. The local Docker backend uses pandas for richer analysis.
- **Hourly aggregation** — Actuals arrive at 30-minute resolution (settlement periods), forecasts at hourly. We aggregate actuals to hourly means before comparison.
- **Latest forecast per hour** — When multiple forecasts exist for the same period (published at different times), we use the most recent one, simulating what a procurement team would actually see.
- **January 2026 scope** — Date range is constrained to January 2026 per the assignment brief, ensuring consistent data availability from BMRS.

## AI Tools Used

This application was built with assistance from **Claude Code** (Anthropic's AI coding assistant). Claude was used for code generation, architecture decisions, and iterative development across backend, frontend, and Docker configuration.
