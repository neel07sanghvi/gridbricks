import { useState } from "react";
import { useApi } from "./hooks/useApi";
import { fetchAccuracy, fetchComparison } from "./services/api";
import MetricCards from "./components/MetricCards";
import ComparisonChart from "./components/ComparisonChart";
import ErrorChart from "./components/ErrorChart";
import HourlyProfile from "./components/HourlyProfile";
import DailyMapeChart from "./components/DailyMapeChart";

function App() {
  const [dateFrom, setDateFrom] = useState("2026-01-01");
  const [dateTo, setDateTo] = useState("2026-01-31");
  const [activeTab, setActiveTab] = useState("overview");

  const accuracy = useApi(fetchAccuracy, dateFrom, dateTo);
  const comparison = useApi(fetchComparison, dateFrom, dateTo);

  const isLoading = accuracy.loading || comparison.loading;
  const error = accuracy.error || comparison.error;

  return (
    <div className="app">
      <header className="header">
        <h1>UK Wind Power Forecast Dashboard</h1>
        <p>
          National wind generation actuals vs day-ahead forecasts — January 2026
          &nbsp;|&nbsp; Source: Elexon BMRS
        </p>
      </header>

      <div className="date-controls">
        <label>
          From
          <input
            type="date"
            value={dateFrom}
            min="2026-01-01"
            max="2026-01-31"
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={dateTo}
            min="2026-01-01"
            max="2026-01-31"
            onChange={(e) => setDateTo(e.target.value)}
          />
        </label>
      </div>

      <div className="tab-bar">
        <button
          className={activeTab === "overview" ? "active" : ""}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={activeTab === "accuracy" ? "active" : ""}
          onClick={() => setActiveTab("accuracy")}
        >
          Forecast Accuracy
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {isLoading ? (
        <div className="loading">
          <div className="spinner" />
          Loading data from Elexon...
        </div>
      ) : (
        <>
          {activeTab === "overview" && (
            <>
              <MetricCards metrics={accuracy.data?.overall_metrics} />
              <ComparisonChart data={comparison.data?.data} />
            </>
          )}

          {activeTab === "accuracy" && (
            <>
              <MetricCards metrics={accuracy.data?.overall_metrics} />
              <div className="charts-row">
                <ErrorChart data={accuracy.data?.daily_metrics} />
                <DailyMapeChart data={accuracy.data?.daily_metrics} />
              </div>
              <HourlyProfile data={accuracy.data?.hourly_error_profile} />
            </>
          )}
        </>
      )}
    </div>
  );
}

export default App;
