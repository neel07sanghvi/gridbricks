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
├── backend/                # Python FastAPI backend
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
│   ├── nginx.conf          # Production reverse proxy config
│   └── Dockerfile
├── docker-compose.yml      # Multi-container orchestration
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

Link: _[To be added after deployment]_

## AI Tools Used

This application was built with assistance from **Claude Code** (Anthropic's AI coding assistant). Claude was used for code generation, architecture decisions, and iterative development across backend, frontend, and Docker configuration.
