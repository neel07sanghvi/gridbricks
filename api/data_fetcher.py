from __future__ import annotations

import httpx
from datetime import datetime, timedelta

ELEXON_BASE = "https://data.elexon.co.uk/bmrs/api/v1"


async def fetch_wind_actuals(client: httpx.AsyncClient, date_from: str, date_to: str) -> list[dict]:
    all_data = []
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

    seen = set()
    deduped = []
    for r in all_data:
        key = (r["startTime"], r["generation"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return sorted(deduped, key=lambda x: x["startTime"])


async def fetch_wind_forecasts(client: httpx.AsyncClient, date_from: str, date_to: str) -> list[dict]:
    all_data = []
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

    seen = set()
    deduped = []
    for r in all_data:
        key = (r["startTime"], r["publishTime"], r["generation"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return sorted(deduped, key=lambda x: (x["startTime"], x["publishTime"]))
