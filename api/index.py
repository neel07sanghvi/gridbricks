from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from math import sqrt

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ELEXON_BASE = "https://data.elexon.co.uk/bmrs/api/v1"


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _floor_hour(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:00:00Z")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _correlation(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sqrt(sum((x - mx) ** 2 for x in xs))
    dy = sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


# ---------------------------------------------------------------------------
# Elexon data fetching
# ---------------------------------------------------------------------------


async def fetch_wind_actuals(client: httpx.AsyncClient, date_from: str, date_to: str) -> list[dict]:
    all_data: list[dict] = []
    current = datetime.fromisoformat(date_from)
    end = datetime.fromisoformat(date_to) + timedelta(days=1)

    while current < end:
        chunk_end = min(current + timedelta(days=7), end)
        params = {
            "publishDateTimeFrom": f"{current.isoformat()}Z",
            "publishDateTimeTo": f"{chunk_end.isoformat()}Z",
        }
        resp = await client.get(f"{ELEXON_BASE}/datasets/FUELHH/stream", params=params)
        resp.raise_for_status()
        records = resp.json()

        wind_records = [
            {
                "startTime": r["startTime"],
                "generation": r["generation"],
                "publishTime": r["publishTime"],
                "settlementPeriod": r["settlementPeriod"],
            }
            for r in records
            if r.get("fuelType") == "WIND"
        ]
        all_data.extend(wind_records)
        current = chunk_end

    seen: set[tuple] = set()
    deduped: list[dict] = []
    for r in all_data:
        key = (r["startTime"], r["generation"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return sorted(deduped, key=lambda x: x["startTime"])


async def fetch_wind_forecasts(client: httpx.AsyncClient, date_from: str, date_to: str) -> list[dict]:
    all_data: list[dict] = []
    current = datetime.fromisoformat(date_from)
    end = datetime.fromisoformat(date_to) + timedelta(days=1)

    publish_start = current - timedelta(days=2)

    while current < end:
        chunk_end = min(current + timedelta(days=7), end)
        params = {
            "from": f"{publish_start.isoformat()}Z",
            "to": f"{chunk_end.isoformat()}Z",
            "publishDateTimeFrom": f"{publish_start.isoformat()}Z",
            "publishDateTimeTo": f"{chunk_end.isoformat()}Z",
        }
        resp = await client.get(f"{ELEXON_BASE}/datasets/WINDFOR/stream", params=params)
        resp.raise_for_status()
        records = resp.json()

        for r in records:
            start_time = r.get("startTime", "")
            if date_from <= start_time[:10] <= date_to:
                all_data.append({
                    "startTime": r["startTime"],
                    "generation": r["generation"],
                    "publishTime": r["publishTime"],
                })

        current = chunk_end
        publish_start = chunk_end - timedelta(days=2)

    seen: set[tuple] = set()
    deduped: list[dict] = []
    for r in all_data:
        key = (r["startTime"], r["publishTime"], r["generation"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return sorted(deduped, key=lambda x: (x["startTime"], x["publishTime"]))


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def _prepare_merged(actuals: list[dict], forecasts: list[dict]) -> list[dict]:
    if not actuals or not forecasts:
        return []

    latest_forecast: dict[str, dict] = {}
    for f in forecasts:
        st = f["startTime"]
        if st not in latest_forecast or f["publishTime"] > latest_forecast[st]["publishTime"]:
            latest_forecast[st] = f

    hourly_actual: dict[str, list[float]] = defaultdict(list)
    for a in actuals:
        hour_key = _floor_hour(_parse_dt(a["startTime"]))
        hourly_actual[hour_key].append(a["generation"])

    actual_hourly: dict[str, float] = {}
    for hour_key, values in hourly_actual.items():
        actual_hourly[hour_key] = sum(values) / len(values)

    merged: list[dict] = []
    for st, forecast in latest_forecast.items():
        hour_key = _floor_hour(_parse_dt(st))
        if hour_key in actual_hourly:
            actual = actual_hourly[hour_key]
            fcast = forecast["generation"]
            error = fcast - actual
            merged.append({
                "startTime": hour_key,
                "actual": actual,
                "forecast": fcast,
                "error": error,
                "abs_error": abs(error),
            })

    merged.sort(key=lambda x: x["startTime"])
    return merged


def compute_accuracy_metrics(actuals: list[dict], forecasts: list[dict]) -> dict:
    merged = _prepare_merged(actuals, forecasts)
    if not merged:
        return {}

    n = len(merged)
    errors = [m["error"] for m in merged]
    abs_errors = [m["abs_error"] for m in merged]
    actuals_v = [m["actual"] for m in merged]
    forecasts_v = [m["forecast"] for m in merged]

    mae = _mean(abs_errors)
    rmse = sqrt(_mean([e ** 2 for e in errors]))
    mape = _mean([ae / max(abs(a), 1) * 100 for ae, a in zip(abs_errors, actuals_v)])
    bias = _mean(errors)
    corr = _correlation(actuals_v, forecasts_v)

    return {
        "mae": round(mae, 1),
        "rmse": round(rmse, 1),
        "mape": round(mape, 2),
        "bias": round(bias, 1),
        "max_over_forecast": round(max(errors), 1),
        "max_under_forecast": round(min(errors), 1),
        "correlation": round(corr, 4),
        "actual_mean_mw": round(_mean(actuals_v), 1),
        "forecast_mean_mw": round(_mean(forecasts_v), 1),
        "data_points": n,
    }


def compute_daily_metrics(actuals: list[dict], forecasts: list[dict]) -> list[dict]:
    merged = _prepare_merged(actuals, forecasts)
    if not merged:
        return []

    daily: dict[str, list[dict]] = defaultdict(list)
    for m in merged:
        date = m["startTime"][:10]
        daily[date].append(m)

    result: list[dict] = []
    for date in sorted(daily):
        rows = daily[date]
        actual_mean = _mean([r["actual"] for r in rows])
        forecast_mean = _mean([r["forecast"] for r in rows])
        mae = _mean([r["abs_error"] for r in rows])
        bias = _mean([r["error"] for r in rows])
        max_error = max(r["abs_error"] for r in rows)
        mape = mae / max(actual_mean, 1) * 100

        result.append({
            "date": date,
            "actual_mean": round(actual_mean, 1),
            "forecast_mean": round(forecast_mean, 1),
            "mae": round(mae, 1),
            "mape": round(mape, 2),
            "bias": round(bias, 1),
            "max_error": round(max_error, 1),
        })

    return result


def compute_hourly_error_profile(actuals: list[dict], forecasts: list[dict]) -> list[dict]:
    merged = _prepare_merged(actuals, forecasts)
    if not merged:
        return []

    hourly: dict[int, list[dict]] = defaultdict(list)
    for m in merged:
        hour = _parse_dt(m["startTime"]).hour
        hourly[hour].append(m)

    result: list[dict] = []
    for hour in sorted(hourly):
        rows = hourly[hour]
        result.append({
            "hour": hour,
            "mae": round(_mean([r["abs_error"] for r in rows]), 1),
            "bias": round(_mean([r["error"] for r in rows]), 1),
            "count": len(rows),
        })

    return result


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


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

    latest_forecast: dict[str, dict] = {}
    for f in forecasts:
        st = f["startTime"]
        if st not in latest_forecast or f["publishTime"] > latest_forecast[st]["publishTime"]:
            latest_forecast[st] = f

    hourly_actual: dict[str, list[float]] = defaultdict(list)
    for a in actuals:
        hour_key = _floor_hour(_parse_dt(a["startTime"]))
        hourly_actual[hour_key].append(a["generation"])

    actual_hourly = {k: sum(v) / len(v) for k, v in hourly_actual.items()}

    records: list[dict] = []
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
