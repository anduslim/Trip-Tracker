import type { PriceAnalysisDto, SearchOffer } from '@/api/search';

const STYLES: Record<NonNullable<SearchOffer['price_rating']>, { bg: string; label: string }> = {
  cheap: { bg: '#1e7e34', label: 'Bargain' },
  good: { bg: '#2856e0', label: 'Good price' },
  typical: { bg: '#7f8c8d', label: 'Typical' },
  expensive: { bg: '#c0392b', label: 'Expensive' },
};

export function PriceRatingBadge({ rating }: { rating: SearchOffer['price_rating'] }) {
  if (!rating) return null;
  const s = STYLES[rating];
  return (
    <span
      style={{
        display: 'inline-block',
        marginLeft: '0.5rem',
        padding: '0.1rem 0.5rem',
        background: s.bg,
        color: '#fff',
        borderRadius: 999,
        fontSize: '0.75rem',
        fontWeight: 600,
        letterSpacing: '0.02em',
      }}
    >
      {s.label}
    </span>
  );
}

export function PriceAnalysisPanel({ analysis }: { analysis: PriceAnalysisDto }) {
  return (
    <div className="card">
      <strong>Price context for {analysis.origin_iata} → {analysis.destination_iata}</strong>
      <div className="muted" style={{ marginTop: '0.25rem' }}>
        Historical quartiles ({analysis.currency}) for {analysis.depart_date}:
      </div>
      <table style={{ marginTop: '0.5rem' }}>
        <thead>
          <tr>
            <th>Min</th>
            <th>25%</th>
            <th>Median</th>
            <th>75%</th>
            <th>Max</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{analysis.minimum}</td>
            <td>{analysis.first}</td>
            <td>{analysis.median}</td>
            <td>{analysis.third}</td>
            <td>{analysis.maximum}</td>
          </tr>
        </tbody>
      </table>
      <p className="muted" style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
        Offers ≤ 25th percentile show as <strong>Bargain</strong>; ≤ median as <strong>Good price</strong>;
        ≤ 75th as <strong>Typical</strong>; above as <strong>Expensive</strong>.
      </p>
    </div>
  );
}
