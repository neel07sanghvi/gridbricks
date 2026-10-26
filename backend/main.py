from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional

from data_fetcher import fetch_wind_actuals, fetch_wind_forecasts
from analysis import compute_accuracy_metrics, compute_daily_metrics, compute_hourly_error_profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=60.0)
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    title="Wind Power Forecast Dashboard",
    description="UK Wind Power Generation: Actuals vs Forecasts for January 2026",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/actuals")
async def get_actuals(
    date_from: str = Query(default="2026-01-01", description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(default="2026-01-31", description="End date (YYYY-MM-DD)"),
):
    client = app.state.http_client
    data = await fetch_wind_actuals(client, date_from, date_to)
    return {"data": data, "count": len(data)}


@app.get("/api/forecasts")
async def get_forecasts(
    date_from: str = Query(default="2026-01-01", description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(default="2026-01-31", description="End date (YYYY-MM-DD)"),
):
    client = app.state.http_client
    data = await fetch_wind_forecasts(client, date_from, date_to)
    return {"data": data, "count": len(data)}


@app.get("/api/accuracy")
async def get_accuracy(
    date_from: str = Query(default="2026-01-01"),
    date_to: str = Query(default="2026-01-31"),
):
    client = app.state.http_client
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
    client = app.state.http_client
    actuals = await fetch_wind_actuals(client, date_from, date_to)
    forecasts = await fetch_wind_forecasts(client, date_from, date_to)

    df_actual = pd.DataFrame(actuals)
    df_forecast = pd.DataFrame(forecasts)

    if df_actual.empty or df_forecast.empty:
        return {"data": [], "count": 0}

    df_actual["startTime"] = pd.to_datetime(df_actual["startTime"])
    df_forecast["startTime"] = pd.to_datetime(df_forecast["startTime"])

    df_forecast_latest = (
        df_forecast.sort_values("publishTime", ascending=False)
        .groupby("startTime")
        .first()
        .reset_index()
    )

    df_actual["startTime_hour"] = df_actual["startTime"].dt.floor("h")
    actual_hourly = (
        df_actual.groupby("startTime_hour")["generation"]
        .mean()
        .reset_index()
        .rename(columns={"startTime_hour": "startTime", "generation": "actual"})
    )

    merged = pd.merge(
        actual_hourly,
        df_forecast_latest[["startTime", "generation"]].rename(
            columns={"generation": "forecast"}
        ),
        on="startTime",
        how="inner",
    )

    merged["error"] = merged["forecast"] - merged["actual"]
    merged["abs_error"] = merged["error"].abs()
    merged["pct_error"] = (merged["error"] / merged["actual"] * 100).round(2)
    merged["startTime"] = merged["startTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    records = merged.to_dict(orient="records")
    return {"data": records, "count": len(records)}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
