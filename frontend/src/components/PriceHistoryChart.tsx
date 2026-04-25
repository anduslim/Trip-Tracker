import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { PriceSnapshot } from '@/types/api';

export function PriceHistoryChart({ snapshots, currency }: { snapshots: PriceSnapshot[]; currency: string }) {
  const data = snapshots.map((s) => ({
    captured_at: new Date(s.captured_at).toLocaleDateString(),
    price: Number(s.price),
  }));
  if (data.length === 0) {
    return <p className="muted">No price history yet.</p>;
  }
  return (
    <div style={{ width: '100%', height: 240 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="captured_at" />
          <YAxis />
          <Tooltip formatter={(v: number) => `${currency} ${v.toFixed(2)}`} />
          <Line type="monotone" dataKey="price" stroke="#2856e0" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
