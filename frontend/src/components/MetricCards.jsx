export default function MetricCards({ metrics }) {
  if (!metrics) return null;

  const cards = [
    { label: "MAE", value: metrics.mae, unit: "MW", desc: "Mean Absolute Error" },
    { label: "RMSE", value: metrics.rmse, unit: "MW", desc: "Root Mean Square Error" },
    { label: "MAPE", value: metrics.mape, unit: "%", desc: "Mean Abs % Error" },
    { label: "Bias", value: metrics.bias, unit: "MW", desc: "Avg over/under forecast" },
    { label: "Correlation", value: metrics.correlation, unit: "", desc: "Actual vs Forecast" },
    { label: "Data Points", value: metrics.data_points, unit: "hrs", desc: "Matched observations" },
  ];

  return (
    <div className="metrics-grid">
      {cards.map((c) => (
        <div key={c.label} className="metric-card">
          <div className="label">{c.label}</div>
          <div className="value">
            {typeof c.value === "number" ? c.value.toLocaleString() : "—"}
            {c.unit && <span className="unit">{c.unit}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}
