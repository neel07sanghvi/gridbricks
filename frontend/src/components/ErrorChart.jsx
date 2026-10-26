import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";
import { format, parseISO } from "date-fns";

function ErrorTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  const d = payload[0]?.payload;
  if (!d) return null;

  return (
    <div className="tooltip-custom">
      <div className="tooltip-label">{format(parseISO(d.date), "dd MMM yyyy")}</div>
      <div className="tooltip-row">
        <span>MAE</span>
        <span className="tooltip-value">{Math.round(d.mae).toLocaleString()} MW</span>
      </div>
      <div className="tooltip-row">
        <span>MAPE</span>
        <span className="tooltip-value">{d.mape}%</span>
      </div>
      <div className="tooltip-row">
        <span>Bias</span>
        <span className="tooltip-value">{Math.round(d.bias).toLocaleString()} MW</span>
      </div>
      <div className="tooltip-row">
        <span>Max Error</span>
        <span className="tooltip-value">{Math.round(d.max_error).toLocaleString()} MW</span>
      </div>
    </div>
  );
}

export default function ErrorChart({ data }) {
  if (!data?.length) return null;

  return (
    <div className="chart-container">
      <h2>Daily Forecast Bias</h2>
      <p className="chart-desc">
        Positive = over-forecast, Negative = under-forecast. Bars show average daily bias in MW.
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-grid)" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={(d) => format(parseISO(d), "dd")}
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            tickFormatter={(v) => `${Math.round(v)}`}
            width={52}
          />
          <Tooltip content={<ErrorTooltip />} />
          <ReferenceLine y={0} stroke="var(--color-text-muted)" strokeWidth={1} />
          <Bar dataKey="bias" radius={[3, 3, 0, 0]} maxBarSize={20}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.bias >= 0 ? "var(--color-error-positive)" : "var(--color-error-negative)"}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
