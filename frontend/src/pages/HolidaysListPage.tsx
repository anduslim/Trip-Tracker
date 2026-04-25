import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { holidaysApi, type HolidayInput } from '@/api/holidays';

export function HolidaysListPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const { data, isLoading, error } = useQuery({
    queryKey: ['holidays'],
    queryFn: holidaysApi.list,
  });
  const createMut = useMutation({
    mutationFn: (input: HolidayInput) => holidaysApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['holidays'] });
      setShowForm(false);
    },
  });

  const { register, handleSubmit, reset } = useForm<HolidayInput>({
    defaultValues: { name: '', currency: 'USD' },
  });

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p className="error">Failed to load holidays.</p>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>Your holidays</h2>
        <button className="btn" onClick={() => setShowForm((s) => !s)}>
          {showForm ? 'Cancel' : 'New holiday'}
        </button>
      </div>

      {showForm && (
        <form
          className="card"
          onSubmit={handleSubmit((values) => {
            createMut.mutate(values, {
              onSuccess: () => reset(),
            });
          })}
        >
          <label>Name</label>
          <input {...register('name', { required: true })} placeholder="Japan 2026" />
          <div className="form-row">
            <div>
              <label>Start date</label>
              <input type="date" {...register('start_date')} />
            </div>
            <div>
              <label>End date</label>
              <input type="date" {...register('end_date')} />
            </div>
            <div>
              <label>Currency</label>
              <input {...register('currency')} maxLength={3} />
            </div>
          </div>
          <label>Notes</label>
          <textarea {...register('notes')} rows={2} />
          {createMut.error && <div className="error">Could not create.</div>}
          <div style={{ marginTop: '0.75rem' }}>
            <button className="btn" type="submit" disabled={createMut.isPending}>
              Create
            </button>
          </div>
        </form>
      )}

      {(data ?? []).length === 0 ? (
        <p className="muted">No holidays yet — create one above to get started.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {(data ?? []).map((h) => (
            <li key={h.id} className="card">
              <Link to={`/holidays/${h.id}`}><strong>{h.name}</strong></Link>
              <div className="muted">
                {h.start_date ?? '?'} → {h.end_date ?? '?'} · {h.flight_entry_count} flight(s)
                {h.lowest_current_price !== null && (
                  <> · cheapest {h.currency} {h.lowest_current_price}</>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
