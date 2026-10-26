from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

from data_fetcher import fetch_wind_actuals, fetch_wind_forecasts
from analysis import compute_accuracy_metrics, compute_daily_metrics, compute_hourly_error_profile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _floor_hour(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:00:00Z")


@app.get("/api/actuals")
async def get_actuals(
    date_from: str = Query(default="2026-01-01"),
    date_to: str = Query(default="2026-01-31"),
):
    async with httpx.AsyncClient(timeout=60.0) as client:
        data = await fetch_wind_actuals(client, date_from, date_to)
    return {"data": data, "count": len(data)}


@app.get("/api/forecasts")
async def get_forecasts(
    date_from: str = Query(default="2026-01-01"),
    date_to: str = Query(default="2026-01-31"),
):
    async with httpx.AsyncClient(timeout=60.0) as client:
        data = await fetch_wind_forecasts(client, date_from, date_to)
    return {"data": data, "count": len(data)}


@app.get("/api/accuracy")
async def get_accuracy(
    date_from: str = Query(default="2026-01-01"),
    date_to: str = Query(default="2026-01-31"),
):
    async with httpx.AsyncClient(timeout=60.0) as client:
        actuals = await fetch_wind_actuals(client, date_from, date_to)
        forecasts = await fetch_wind_forecasts(client, date_from, date_to)

    metrics = compute_accuracy_metrics(actuals, forecasts)
    daily = compute_daily_metrics(actuals, forecasts)
    hourly_profile = compute_hourly_error_profile(actuals, forecasts)

    return {
        "overall_metrics": metrics,
        "daily_metrics": daily,
        "hourly_error_profile": hourly_profile,
    }


@app.get("/api/comparison")
async def get_comparison(
    date_from: str = Query(default="2026-01-01"),
    date_to: str = Query(default="2026-01-31"),
):
    async with httpx.AsyncClient(timeout=60.0) as client:
        actuals = await fetch_wind_actuals(client, date_from, date_to)
        forecasts = await fetch_wind_forecasts(client, date_from, date_to)

    if not actuals or not forecasts:
        return {"data": [], "count": 0}

    # Latest forecast per startTime
    latest_forecast = {}
    for f in forecasts:
        st = f["startTime"]
        if st not in latest_forecast or f["publishTime"] > latest_forecast[st]["publishTime"]:
            latest_forecast[st] = f

    # Aggregate actuals to hourly
    hourly_actual = defaultdict(list)
    for a in actuals:
        hour_key = _floor_hour(_parse_dt(a["startTime"]))
        hourly_actual[hour_key].append(a["generation"])

    actual_hourly = {k: sum(v) / len(v) for k, v in hourly_actual.items()}

    # Merge
    records = []
    for st, forecast in latest_forecast.items():
        hour_key = _floor_hour(_parse_dt(st))
        if hour_key in actual_hourly:
            actual = actual_hourly[hour_key]
            fcast = forecast["generation"]
            error = fcast - actual
            pct_error = round(error / actual * 100, 2) if actual != 0 else 0
            records.append({
                "startTime": hour_key,
                "actual": actual,
                "forecast": fcast,
                "error": error,
                "abs_error": abs(error),
                "pct_error": pct_error,
            })

    records.sort(key=lambda x: x["startTime"])
    return {"data": records, "count": len(records)}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
