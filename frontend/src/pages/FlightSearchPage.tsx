import { useMutation, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { holidaysApi } from '@/api/holidays';
import { searchApi, type SearchInput, type SearchOffer } from '@/api/search';

interface FormValues extends SearchInput {}

export function FlightSearchPage() {
  const { id } = useParams();
  const holidayId = Number(id);
  const navigate = useNavigate();
  const [results, setResults] = useState<SearchOffer[] | null>(null);
  const [provider, setProvider] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const { data: holiday } = useQuery({
    queryKey: ['holiday', holidayId],
    queryFn: () => holidaysApi.get(holidayId),
    enabled: Number.isFinite(holidayId),
  });
  const { data: providers } = useQuery({
    queryKey: ['providers'],
    queryFn: searchApi.providers,
  });

  const { register, handleSubmit, formState: { isSubmitting } } = useForm<FormValues>({
    defaultValues: {
      origin: '',
      destination: '',
      passengers: 1,
      currency: holiday?.currency ?? 'USD',
      max_results: 10,
    },
  });

  const onSubmit = async (values: FormValues) => {
    setSearchError(null);
    try {
      const resp = await searchApi.flights({
        ...values,
        origin: values.origin.toUpperCase(),
        destination: values.destination.toUpperCase(),
        passengers: Number(values.passengers ?? 1),
        max_results: Number(values.max_results ?? 10),
        max_price: values.max_price?.toString() || null,
        return_date: values.return_date || null,
        min_duration_days: values.min_duration_days ? Number(values.min_duration_days) : null,
        max_duration_days: values.max_duration_days ? Number(values.max_duration_days) : null,
      });
      setProvider(resp.provider);
      setResults(resp.offers);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    }
  };

  const saveMut = useMutation({
    mutationFn: (offer: SearchOffer) =>
      searchApi.saveOffer({ holiday_id: holidayId, offer }),
    onSuccess: () => navigate(`/holidays/${holidayId}`),
  });

  if (!holiday) return <p>Loading...</p>;

  return (
    <div>
      <p>
        <Link to={`/holidays/${holidayId}`}>← {holiday.name}</Link>
      </p>
      <h2>Search flights</h2>

      <form className="card" onSubmit={handleSubmit(onSubmit)}>
        <div className="form-row">
          <div>
            <label>Origin (IATA)</label>
            <input maxLength={3} {...register('origin', { required: true, minLength: 3 })} />
          </div>
          <div>
            <label>Destination (IATA)</label>
            <input maxLength={3} {...register('destination', { required: true, minLength: 3 })} />
          </div>
          <div>
            <label>Passengers</label>
            <input type="number" min={1} {...register('passengers')} />
          </div>
        </div>
        <div className="form-row">
          <div>
            <label>Depart</label>
            <input type="date" {...register('depart_date', { required: true })} />
          </div>
          <div>
            <label>Return (optional)</label>
            <input type="date" {...register('return_date')} />
          </div>
          <div>
            <label>Cabin</label>
            <select {...register('cabin')}>
              <option value="">Any</option>
              <option value="ECONOMY">Economy</option>
              <option value="PREMIUM_ECONOMY">Premium Economy</option>
              <option value="BUSINESS">Business</option>
              <option value="FIRST">First</option>
            </select>
          </div>
        </div>
        <div className="form-row">
          <div>
            <label>Max price (optional)</label>
            <input type="number" step="0.01" min={0} {...register('max_price')} />
          </div>
          <div>
            <label>Currency</label>
            <input maxLength={3} {...register('currency')} />
          </div>
          <div>
            <label>Provider</label>
            <select {...register('provider')}>
              <option value="">Default</option>
              {(providers?.providers ?? []).map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="form-row">
          <div>
            <label>Min trip duration (days)</label>
            <input type="number" min={1} max={365} {...register('min_duration_days')} />
          </div>
          <div>
            <label>Max trip duration (days)</label>
            <input type="number" min={1} max={365} {...register('max_duration_days')} />
          </div>
          <div />
        </div>
        <div style={{ marginTop: '0.75rem' }}>
          <button className="btn" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Searching...' : 'Search'}
          </button>
        </div>
        {searchError && <div className="error">{searchError}</div>}
      </form>

      {results !== null && (
        <div>
          <p className="muted">
            {results.length} result(s) from <strong>{provider}</strong>
          </p>
          {results.length === 0 && <p>No matching offers found.</p>}
          {results.map((o, i) => (
            <div className="card" key={`${o.provider}-${o.provider_offer_id}-${i}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <div>
                  <strong>{o.origin_iata} → {o.destination_iata}</strong>{' '}
                  <span className="muted">
                    {o.depart_date}{o.return_date ? ` ↔ ${o.return_date}` : ''}
                    {o.airline_name ? ` · ${o.airline_name}` : o.airline_code ? ` · ${o.airline_code}` : ''}
                    {o.cabin ? ` · ${o.cabin}` : ''}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: 600 }}>{o.currency} {o.price}</div>
                  {o.deep_link && (
                    <a href={o.deep_link} target="_blank" rel="noreferrer" className="muted">View source</a>
                  )}
                </div>
              </div>
              <div style={{ marginTop: '0.5rem' }}>
                <button
                  className="btn"
                  disabled={saveMut.isPending}
                  onClick={() => saveMut.mutate(o)}
                >
                  Save to holiday
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
