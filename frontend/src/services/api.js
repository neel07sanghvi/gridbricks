import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

export async function fetchActuals(dateFrom = "2026-01-01", dateTo = "2026-01-31") {
  const { data } = await api.get("/api/actuals", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}

export async function fetchForecasts(dateFrom = "2026-01-01", dateTo = "2026-01-31") {
  const { data } = await api.get("/api/forecasts", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}

export async function fetchAccuracy(dateFrom = "2026-01-01", dateTo = "2026-01-31") {
  const { data } = await api.get("/api/accuracy", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}

export async function fetchComparison(dateFrom = "2026-01-01", dateTo = "2026-01-31") {
  const { data } = await api.get("/api/comparison", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}
