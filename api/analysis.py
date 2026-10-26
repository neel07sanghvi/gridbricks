from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import sqrt


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _floor_hour(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:00:00Z")


def _prepare_merged(actuals: list[dict], forecasts: list[dict]) -> list[dict]:
    if not actuals or not forecasts:
        return []

    # Get latest forecast per startTime (by publishTime)
    latest_forecast = {}
    for f in forecasts:
        st = f["startTime"]
        if st not in latest_forecast or f["publishTime"] > latest_forecast[st]["publishTime"]:
            latest_forecast[st] = f

    # Aggregate actuals to hourly (mean of 30-min periods)
    hourly_actual = defaultdict(list)
    for a in actuals:
        hour_key = _floor_hour(_parse_dt(a["startTime"]))
        hourly_actual[hour_key].append(a["generation"])

    actual_hourly = {}
    for hour_key, values in hourly_actual.items():
        actual_hourly[hour_key] = sum(values) / len(values)

    # Merge on startTime
    merged = []
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

    daily = defaultdict(list)
    for m in merged:
        date = m["startTime"][:10]
        daily[date].append(m)

    result = []
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

    hourly = defaultdict(list)
    for m in merged:
        hour = _parse_dt(m["startTime"]).hour
        hourly[hour].append(m)

    result = []
    for hour in sorted(hourly):
        rows = hourly[hour]
        result.append({
            "hour": hour,
            "mae": round(_mean([r["abs_error"] for r in rows]), 1),
            "bias": round(_mean([r["error"] for r in rows]), 1),
            "count": len(rows),
        })

    return result
