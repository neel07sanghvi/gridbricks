import pandas as pd
import numpy as np


def _prepare_merged(actuals: list[dict], forecasts: list[dict]) -> pd.DataFrame:
    df_actual = pd.DataFrame(actuals)
    df_forecast = pd.DataFrame(forecasts)

    if df_actual.empty or df_forecast.empty:
        return pd.DataFrame()

    df_actual["startTime"] = pd.to_datetime(df_actual["startTime"])
    df_forecast["startTime"] = pd.to_datetime(df_forecast["startTime"])
    df_forecast["publishTime"] = pd.to_datetime(df_forecast["publishTime"])

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
    return merged


def compute_accuracy_metrics(actuals: list[dict], forecasts: list[dict]) -> dict:
    merged = _prepare_merged(actuals, forecasts)
    if merged.empty:
        return {}

    n = len(merged)
    mae = merged["abs_error"].mean()
    rmse = np.sqrt((merged["error"] ** 2).mean())
    mape = (merged["abs_error"] / merged["actual"].abs().clip(lower=1) * 100).mean()
    bias = merged["error"].mean()
    max_over = merged["error"].max()
    max_under = merged["error"].min()
    correlation = merged["actual"].corr(merged["forecast"])

    actual_mean = merged["actual"].mean()
    forecast_mean = merged["forecast"].mean()

    return {
        "mae": round(float(mae), 1),
        "rmse": round(float(rmse), 1),
        "mape": round(float(mape), 2),
        "bias": round(float(bias), 1),
        "max_over_forecast": round(float(max_over), 1),
        "max_under_forecast": round(float(max_under), 1),
        "correlation": round(float(correlation), 4),
        "actual_mean_mw": round(float(actual_mean), 1),
        "forecast_mean_mw": round(float(forecast_mean), 1),
        "data_points": n,
    }


def compute_daily_metrics(actuals: list[dict], forecasts: list[dict]) -> list[dict]:
    merged = _prepare_merged(actuals, forecasts)
    if merged.empty:
        return []

    merged["date"] = merged["startTime"].dt.date

    daily = merged.groupby("date").agg(
        actual_mean=("actual", "mean"),
        forecast_mean=("forecast", "mean"),
        mae=("abs_error", "mean"),
        bias=("error", "mean"),
        max_error=("abs_error", "max"),
    ).reset_index()

    daily["mape"] = (daily["mae"] / daily["actual_mean"].clip(lower=1) * 100).round(2)

    result = []
    for _, row in daily.iterrows():
        result.append({
            "date": str(row["date"]),
            "actual_mean": round(float(row["actual_mean"]), 1),
            "forecast_mean": round(float(row["forecast_mean"]), 1),
            "mae": round(float(row["mae"]), 1),
            "mape": round(float(row["mape"]), 2),
            "bias": round(float(row["bias"]), 1),
            "max_error": round(float(row["max_error"]), 1),
        })

    return result


def compute_hourly_error_profile(actuals: list[dict], forecasts: list[dict]) -> list[dict]:
    merged = _prepare_merged(actuals, forecasts)
    if merged.empty:
        return []

    merged["hour"] = merged["startTime"].dt.hour

    hourly = merged.groupby("hour").agg(
        mae=("abs_error", "mean"),
        bias=("error", "mean"),
        count=("error", "count"),
    ).reset_index()

    result = []
    for _, row in hourly.iterrows():
        result.append({
            "hour": int(row["hour"]),
            "mae": round(float(row["mae"]), 1),
            "bias": round(float(row["bias"]), 1),
            "count": int(row["count"]),
        })

    return result
