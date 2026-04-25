import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { shareApi } from '@/api/share';

export function PublicSharePage() {
  const { token } = useParams();
  const { data, error, isLoading } = useQuery({
    queryKey: ['public-share', token],
    queryFn: () => shareApi.publicShare(token!),
    enabled: !!token,
  });

  if (isLoading) return <p>Loading...</p>;
  if (error) {
    if (error instanceof ApiError && error.status === 410) {
      return (
        <div className="card">
          <h2>Link expired</h2>
          <p>This share link has been revoked or is no longer active.</p>
        </div>
      );
    }
    return <p className="error">Failed to load shared holiday.</p>;
  }
  if (!data) return null;

  const insights = data.comparison.insights;
  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>{data.holiday.name}</h2>
        <div className="muted">
          {data.holiday.start_date ?? '?'} → {data.holiday.end_date ?? '?'} · {data.holiday.currency}
        </div>
        {data.holiday.destinations.length > 0 && (
          <p className="muted">Destinations: {data.holiday.destinations.map((d) => d.city).join(', ')}</p>
        )}
      </div>

      <div className="card">
        <strong>Insights</strong>
        <ul>
          {insights.cheapest_route ? (
            <li>
              Cheapest: <strong>{insights.cheapest_route.origin} → {insights.cheapest_route.destination}</strong>{' '}
              at {insights.cheapest_route.currency} {insights.cheapest_route.price}.
            </li>
          ) : (
            <li className="muted">No flights tracked yet.</li>
          )}
          {insights.biggest_drop_30d && (
            <li>
              Biggest 30-day drop: {insights.biggest_drop_30d.origin} → {insights.biggest_drop_30d.destination}{' '}
              ({insights.biggest_drop_30d.delta_pct.toFixed(1)}%).
            </li>
          )}
        </ul>
      </div>

      {data.flight_entries.map((e) => (
        <div className="card" key={e.id}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <div>
              <strong>{e.origin_iata} → {e.destination_iata}</strong>{' '}
              <span className="muted">
                {e.depart_date}{e.return_date ? ` ↔ ${e.return_date}` : ''}
                {e.airline_name ? ` · ${e.airline_name}` : ''}
                {e.cabin ? ` · ${e.cabin}` : ''}
              </span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontWeight: 600 }}>{e.currency} {e.latest_price}</div>
              <div className="muted">{e.snapshots.length} snapshot(s)</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
