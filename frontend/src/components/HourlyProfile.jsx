import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";

function HourlyTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;

  const d = payload[0]?.payload;
  if (!d) return null;

  return (
    <div className="tooltip-custom">
      <div className="tooltip-label">{String(d.hour).padStart(2, "0")}:00</div>
      <div className="tooltip-row">
        <span>MAE</span>
        <span className="tooltip-value">{Math.round(d.mae).toLocaleString()} MW</span>
      </div>
      <div className="tooltip-row">
        <span>Bias</span>
        <span className="tooltip-value">{Math.round(d.bias).toLocaleString()} MW</span>
      </div>
      <div className="tooltip-row">
        <span>Samples</span>
        <span className="tooltip-value">{d.count}</span>
      </div>
    </div>
  );
}

export default function HourlyProfile({ data }) {
  if (!data?.length) return null;

  return (
    <div className="chart-container">
      <h2>Hourly Error Profile</h2>
      <p className="chart-desc">
        Average MAE by hour of day. Shows when forecasts are least reliable.
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-grid)" vertical={false} />
          <XAxis
            dataKey="hour"
            tickFormatter={(h) => `${String(h).padStart(2, "0")}:00`}
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            interval={2}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            tickFormatter={(v) => `${Math.round(v)}`}
            width={48}
          />
          <Tooltip content={<HourlyTooltip />} />
          <Bar dataKey="mae" radius={[3, 3, 0, 0]} maxBarSize={24} fill="var(--color-accent)" fillOpacity={0.75} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
