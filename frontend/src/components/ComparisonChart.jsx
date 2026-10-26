import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { format, parseISO } from "date-fns";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  const time = format(parseISO(label), "dd MMM HH:mm");
  return (
    <div className="tooltip-custom">
      <div className="tooltip-label">{time}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tooltip-row">
          <span>{p.name}</span>
          <span className="tooltip-value" style={{ color: p.color }}>
            {Math.round(p.value).toLocaleString()} MW
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ComparisonChart({ data }) {
  if (!data?.length) return null;

  const formatted = data.map((d) => ({
    ...d,
    time: d.startTime,
    displayDate: format(parseISO(d.startTime), "dd MMM"),
  }));

  return (
    <div className="chart-container">
      <h2>Wind Generation: Actual vs Forecast</h2>
      <p className="chart-desc">
        Hourly comparison for the selected period. Forecast uses the latest available publish time per hour.
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart data={formatted} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-grid)" />
          <XAxis
            dataKey="time"
            tickFormatter={(t) => format(parseISO(t), "dd MMM")}
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            interval="preserveStartEnd"
            minTickGap={60}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            width={48}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            align="right"
            iconType="plainline"
            wrapperStyle={{ fontSize: 13, paddingBottom: 8 }}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual"
            stroke="var(--color-actual)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast"
            stroke="var(--color-forecast)"
            strokeWidth={2}
            dot={false}
            strokeDasharray="6 3"
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
