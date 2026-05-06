import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from 'recharts';
import type { ChartData } from '../types';

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

interface Props {
  chart: ChartData;
}

export default function ChartPanel({ chart }: Props) {
  if (!chart?.labels?.length) return null;

  if (chart.type === 'bar') {
    const ds = chart.datasets[0];
    const data = chart.labels.map((label, i) => ({
      name: label.length > 32 ? label.slice(0, 32) + '…' : label,
      value: ds?.data[i] ?? 0,
    }));

    return (
      <div className="chart-container">
        {chart.question_label && (
          <div className="chart-title">{chart.question_label}</div>
        )}
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 4, right: 12, bottom: 56, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: '#64748b' }}
              angle={-28}
              textAnchor="end"
              interval={0}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
              unit="%"
              domain={[0, 100]}
              width={38}
            />
            <Tooltip
              formatter={(v) => [v != null ? `${v}%` : '', ds?.label ?? '%']}
              contentStyle={{
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                fontSize: 12,
              }}
            />
            <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} maxBarSize={52} />
          </BarChart>
        </ResponsiveContainer>
        {chart.base_label && <div className="chart-base">{chart.base_label}</div>}
      </div>
    );
  }

  if (chart.type === 'line') {
    const data = chart.labels.map((label, i) => {
      const point: Record<string, string | number> = { name: label };
      chart.datasets.forEach(ds => {
        point[ds.label] = ds.data[i] ?? 0;
      });
      return point;
    });

    return (
      <div className="chart-container">
        {chart.question_label && (
          <div className="chart-title">{chart.question_label}</div>
        )}
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 4, right: 12, bottom: 16, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} unit="%" width={38} />
            <Tooltip
              formatter={(v) => v != null ? `${v}%` : ''}
              contentStyle={{
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {chart.datasets.map((ds, i) => (
              <Line
                key={ds.label}
                type="monotone"
                dataKey={ds.label}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2.5}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
        {chart.base_label && <div className="chart-base">{chart.base_label}</div>}
      </div>
    );
  }

  return null;
}
