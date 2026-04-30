import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { holidaysApi } from '@/api/holidays';
import { shareApi } from '@/api/share';

export function ComparisonPage() {
  const { id } = useParams();
  const holidayId = Number(id);
  const { data: holiday } = useQuery({
    queryKey: ['holiday', holidayId],
    queryFn: () => holidaysApi.get(holidayId),
    enabled: Number.isFinite(holidayId),
  });
  const { data: comparison, isLoading } = useQuery({
    queryKey: ['comparison', holidayId],
    queryFn: () => shareApi.comparison(holidayId),
    enabled: Number.isFinite(holidayId),
  });

  if (isLoading || !comparison) return <p>Loading...</p>;
  const insights = comparison.insights;

  return (
    <div>
      <p>
        <Link to={`/holidays/${holidayId}`}>← {holiday?.name ?? 'Holiday'}</Link>
      </p>
      <h2>Compare flights</h2>

      <div className="card">
        <strong>Insights</strong>
        {comparison.route_groups.length === 0 ? (
          <p className="muted">Add flight entries first to see insights.</p>
        ) : (
          <ul>
            {insights.cheapest_route && (
              <li>
                Cheapest route: <strong>{insights.cheapest_route.origin} → {insights.cheapest_route.destination}</strong>{' '}
                at {insights.cheapest_route.currency} {insights.cheapest_route.price}.
              </li>
            )}
            {insights.biggest_drop_30d && (
              <li>
                Biggest drop in 30d: <strong>{insights.biggest_drop_30d.origin} → {insights.biggest_drop_30d.destination}</strong>{' '}
                ({insights.biggest_drop_30d.delta_pct.toFixed(1)}%, {insights.biggest_drop_30d.currency} {insights.biggest_drop_30d.delta}).
              </li>
            )}
            {!insights.biggest_drop_30d && (
              <li className="muted">No 30-day drops yet — keep tracking.</li>
            )}
            {insights.best_day_of_week.map((b) => (
              <li key={`${b.origin}-${b.destination}`}>
                Best day to depart {b.origin} → {b.destination}: <strong>{b.best_day}</strong>{' '}
                (avg {b.avg_price}, {b.samples} samples)
              </li>
            ))}
          </ul>
        )}
      </div>

      {comparison.route_groups.length > 0 && (
        <div className="card">
          <strong>By route</strong>
          <table style={{ marginTop: '0.5rem' }}>
            <thead>
              <tr>
                <th>Route</th>
                <th>Entries</th>
                <th>Min</th>
                <th>Avg</th>
                <th>Max</th>
              </tr>
            </thead>
            <tbody>
              {comparison.route_groups.map((g) => (
                <tr key={`${g.origin}-${g.destination}`}>
                  <td>{g.origin} → {g.destination}</td>
                  <td>{g.entry_count}</td>
                  <td>{g.min_price}</td>
                  <td>{g.avg_price}</td>
                  <td>{g.max_price}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
