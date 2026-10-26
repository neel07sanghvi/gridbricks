import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { format, parseISO } from "date-fns";

function MapeTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;

  const d = payload[0]?.payload;
  if (!d) return null;

  return (
    <div className="tooltip-custom">
      <div className="tooltip-label">{format(parseISO(d.date), "dd MMM yyyy")}</div>
      <div className="tooltip-row">
        <span>MAPE</span>
        <span className="tooltip-value">{d.mape}%</span>
      </div>
      <div className="tooltip-row">
        <span>Actual Avg</span>
        <span className="tooltip-value">{Math.round(d.actual_mean).toLocaleString()} MW</span>
      </div>
      <div className="tooltip-row">
        <span>Forecast Avg</span>
        <span className="tooltip-value">{Math.round(d.forecast_mean).toLocaleString()} MW</span>
      </div>
    </div>
  );
}

export default function DailyMapeChart({ data }) {
  if (!data?.length) return null;

  return (
    <div className="chart-container">
      <h2>Daily MAPE</h2>
      <p className="chart-desc">
        Mean Absolute Percentage Error per day. Lower is better.
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="mapeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.3} />
              <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-grid)" />
          <XAxis
            dataKey="date"
            tickFormatter={(d) => format(parseISO(d), "dd")}
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
            tickFormatter={(v) => `${v}%`}
            width={48}
          />
          <Tooltip content={<MapeTooltip />} />
          <Area
            type="monotone"
            dataKey="mape"
            stroke="var(--color-accent)"
            strokeWidth={2}
            fill="url(#mapeGrad)"
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0, fill: "var(--color-accent)" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
