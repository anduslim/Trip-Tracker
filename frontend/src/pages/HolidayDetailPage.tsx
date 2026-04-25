import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { flightsApi, type FlightInput } from '@/api/flights';
import { holidaysApi } from '@/api/holidays';
import { FlightEntryForm } from '@/components/FlightEntryForm';
import { PriceHistoryChart } from '@/components/PriceHistoryChart';
import type { FlightEntry } from '@/types/api';

export function HolidayDetailPage() {
  const { id } = useParams();
  const holidayId = Number(id);
  const queryClient = useQueryClient();
  const { data: holiday, isLoading } = useQuery({
    queryKey: ['holiday', holidayId],
    queryFn: () => holidaysApi.get(holidayId),
    enabled: Number.isFinite(holidayId),
  });

  const createFlight = useMutation({
    mutationFn: (input: FlightInput) =>
      flightsApi.create(holidayId, {
        ...input,
        origin_iata: input.origin_iata.toUpperCase(),
        destination_iata: input.destination_iata.toUpperCase(),
        currency: (input.currency ?? holiday?.currency ?? 'USD').toUpperCase(),
        return_date: input.return_date || null,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['holiday', holidayId] }),
  });

  const removeHoliday = useMutation({
    mutationFn: () => holidaysApi.remove(holidayId),
  });

  if (isLoading || !holiday) return <p>Loading...</p>;

  return (
    <div>
      <p>
        <Link to="/holidays">← All holidays</Link>
      </p>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>{holiday.name}</h2>
        <div className="muted">
          {holiday.start_date ?? '?'} → {holiday.end_date ?? '?'} · currency {holiday.currency}
        </div>
        {holiday.notes && <p>{holiday.notes}</p>}
        {holiday.destinations.length > 0 && (
          <p className="muted">
            Destinations: {holiday.destinations.map((d) => d.city).join(', ')}
          </p>
        )}
        <button
          className="btn danger"
          onClick={async () => {
            if (!confirm('Delete this holiday and all its flights?')) return;
            await removeHoliday.mutateAsync();
            window.location.href = '/holidays';
          }}
        >
          Delete holiday
        </button>
      </div>

      <FlightEntryForm
        onSubmit={(v) => createFlight.mutate(v)}
        submitting={createFlight.isPending}
        defaultCurrency={holiday.currency}
      />

      {holiday.flight_entries.length === 0 ? (
        <p className="muted">No flights tracked yet.</p>
      ) : (
        holiday.flight_entries.map((entry) => (
          <FlightEntryCard key={entry.id} entry={entry} holidayId={holidayId} />
        ))
      )}
    </div>
  );
}

function FlightEntryCard({ entry, holidayId }: { entry: FlightEntry; holidayId: number }) {
  const queryClient = useQueryClient();
  const [showRefresh, setShowRefresh] = useState(false);
  const [refreshPrice, setRefreshPrice] = useState('');
  const { data: snapshots } = useQuery({
    queryKey: ['snapshots', holidayId, entry.id],
    queryFn: () => flightsApi.snapshots(holidayId, entry.id),
  });
  const refreshMut = useMutation({
    mutationFn: (price: string) => flightsApi.refresh(holidayId, entry.id, { price }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots', holidayId, entry.id] });
      queryClient.invalidateQueries({ queryKey: ['holiday', holidayId] });
      setShowRefresh(false);
      setRefreshPrice('');
    },
  });
  const removeMut = useMutation({
    mutationFn: () => flightsApi.remove(holidayId, entry.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['holiday', holidayId] }),
  });

  const initial = Number(entry.initial_price);
  const latest = Number(entry.latest_price);
  const delta = latest - initial;
  const deltaPct = initial > 0 ? (delta / initial) * 100 : 0;

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div>
          <strong>
            {entry.origin_iata} → {entry.destination_iata}
          </strong>{' '}
          <span className="muted">
            {entry.depart_date}
            {entry.return_date ? ` ↔ ${entry.return_date}` : ''}
            {entry.airline_name ? ` · ${entry.airline_name}` : ''}
          </span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>
            {entry.currency} {entry.latest_price}
          </div>
          <div className="muted" style={{ color: delta < 0 ? '#1e7e34' : delta > 0 ? '#c0392b' : undefined }}>
            {delta === 0 ? 'no change' : `${delta > 0 ? '+' : ''}${delta.toFixed(2)} (${deltaPct.toFixed(1)}%)`} since first
          </div>
        </div>
      </div>
      {entry.source_url && (
        <p className="muted" style={{ marginTop: '0.5rem' }}>
          Source: <a href={entry.source_url} target="_blank" rel="noreferrer">{entry.source_url}</a>
        </p>
      )}
      <div style={{ marginTop: '0.75rem' }}>
        <PriceHistoryChart snapshots={snapshots ?? []} currency={entry.currency} />
      </div>
      <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
        <button className="btn secondary" onClick={() => setShowRefresh((s) => !s)}>
          {showRefresh ? 'Cancel' : 'Log new price'}
        </button>
        <button
          className="btn danger"
          onClick={() => {
            if (confirm('Delete this flight entry?')) removeMut.mutate();
          }}
        >
          Delete
        </button>
      </div>
      {showRefresh && (
        <div style={{ marginTop: '0.75rem' }} className="form-row">
          <input
            type="number"
            step="0.01"
            min={0}
            placeholder={`New price in ${entry.currency}`}
            value={refreshPrice}
            onChange={(e) => setRefreshPrice(e.target.value)}
          />
          <button
            className="btn"
            disabled={!refreshPrice || refreshMut.isPending}
            onClick={() => refreshMut.mutate(refreshPrice)}
          >
            Save snapshot
          </button>
        </div>
      )}
    </div>
  );
}
