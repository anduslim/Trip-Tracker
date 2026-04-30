import { useMutation, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { holidaysApi } from '@/api/holidays';
import {
  searchApi,
  type LegResult,
  type MultiLegInput,
  type PriceAnalysisDto,
  type SearchInput,
  type SearchOffer,
  type SinglePnrOffer,
} from '@/api/search';
import { PriceAnalysisPanel, PriceRatingBadge } from '@/components/PriceRatingBadge';

type MultiSubMode = 'separate' | 'single-pnr';

type Mode = 'one-way-or-return' | 'multi-city';

export function FlightSearchPage() {
  const { id } = useParams();
  const holidayId = Number(id);
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('one-way-or-return');
  const [singleResults, setSingleResults] = useState<SearchOffer[] | null>(null);
  const [singleProvider, setSingleProvider] = useState<string | null>(null);
  const [singleAnalysis, setSingleAnalysis] = useState<PriceAnalysisDto | null>(null);
  const [multiSubMode, setMultiSubMode] = useState<MultiSubMode>('separate');
  const [multiResults, setMultiResults] = useState<{
    provider: string;
    legs: LegResult[];
    total_min_price: string | null;
    currency: string;
  } | null>(null);
  const [singlePnrResults, setSinglePnrResults] = useState<{
    provider: string;
    offers: SinglePnrOffer[];
  } | null>(null);
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

  const saveMut = useMutation({
    mutationFn: (offer: SearchOffer) =>
      searchApi.saveOffer({ holiday_id: holidayId, offer }),
    onSuccess: () => navigate(`/holidays/${holidayId}`),
  });

  if (!holiday) return <p>Loading...</p>;
  const currencyDefault = holiday.currency ?? 'USD';

  return (
    <div>
      <p>
        <Link to={`/holidays/${holidayId}`}>← {holiday.name}</Link>
      </p>
      <h2>Search flights</h2>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <button
          className={`btn ${mode === 'one-way-or-return' ? '' : 'secondary'}`}
          onClick={() => setMode('one-way-or-return')}
        >
          Single route
        </button>
        <button
          className={`btn ${mode === 'multi-city' ? '' : 'secondary'}`}
          onClick={() => setMode('multi-city')}
        >
          Multi-city
        </button>
      </div>

      {mode === 'one-way-or-return' ? (
        <SingleRouteForm
          currencyDefault={currencyDefault}
          providers={providers?.providers ?? []}
          onResults={(p, offers, analysis) => {
            setSingleProvider(p);
            setSingleResults(offers);
            setSingleAnalysis(analysis);
            setSearchError(null);
          }}
          onError={(msg) => {
            setSearchError(msg);
            setSingleResults([]);
            setSingleAnalysis(null);
          }}
        />
      ) : (
        <>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <button
              className={`btn ${multiSubMode === 'separate' ? '' : 'secondary'}`}
              onClick={() => setMultiSubMode('separate')}
            >
              Separate tickets per leg
            </button>
            <button
              className={`btn ${multiSubMode === 'single-pnr' ? '' : 'secondary'}`}
              onClick={() => setMultiSubMode('single-pnr')}
            >
              Single ticket (one PNR)
            </button>
          </div>
          <p className="muted" style={{ marginTop: '-0.25rem' }}>
            {multiSubMode === 'separate'
              ? 'Each leg searched independently — best for tour-style trips where you book each leg separately.'
              : 'One ticket covering all legs in order — best for connecting itineraries (Amadeus only).'}
          </p>
          <MultiCityForm
            mode={multiSubMode}
            currencyDefault={currencyDefault}
            providers={providers?.providers ?? []}
            onSeparateResults={(r) => {
              setMultiResults(r);
              setSinglePnrResults(null);
              setSearchError(null);
            }}
            onSinglePnrResults={(r) => {
              setSinglePnrResults(r);
              setMultiResults(null);
              setSearchError(null);
            }}
            onError={(msg) => {
              setSearchError(msg);
              setMultiResults(null);
              setSinglePnrResults(null);
            }}
          />
        </>
      )}

      {searchError && <div className="error">{searchError}</div>}

      {mode === 'one-way-or-return' && singleResults !== null && (
        <>
          {singleAnalysis && <PriceAnalysisPanel analysis={singleAnalysis} />}
          <ResultsList
            provider={singleProvider}
            offers={singleResults}
            onSave={(o) => saveMut.mutate(o)}
            saving={saveMut.isPending}
          />
        </>
      )}

      {mode === 'multi-city' && singlePnrResults && (
        <div>
          <p className="muted">
            Provider <strong>{singlePnrResults.provider}</strong> · {singlePnrResults.offers.length} single-ticket option(s)
          </p>
          {singlePnrResults.offers.length === 0 && (
            <p>No single-PNR itineraries found. Try the separate-tickets mode.</p>
          )}
          {singlePnrResults.offers.map((offer, oi) => (
            <div className="card" key={`${offer.provider_offer_id}-${oi}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <strong>Option {oi + 1}</strong>
                <div style={{ fontWeight: 600 }}>
                  {offer.currency} {offer.total_price}
                </div>
              </div>
              {offer.legs.map((leg, li) => (
                <div
                  key={li}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                    padding: '0.4rem 0',
                    borderTop: li === 0 ? undefined : '1px solid #eee',
                  }}
                >
                  <div>
                    <strong>{leg.origin_iata} → {leg.destination_iata}</strong>{' '}
                    <span className="muted">
                      {leg.depart_date}{leg.airline_name ? ` · ${leg.airline_name}` : ''}
                      {leg.cabin ? ` · ${leg.cabin}` : ''}
                    </span>
                  </div>
                  <div className="muted">{leg.currency} {leg.price}</div>
                </div>
              ))}
              <div style={{ marginTop: '0.5rem' }}>
                <button
                  className="btn"
                  disabled={saveMut.isPending}
                  onClick={() => {
                    // Save each leg as a separate flight_entry; the user
                    // can later see them as a group via the comparison view.
                    offer.legs.forEach((leg) => {
                      saveMut.mutate({
                        provider: leg.provider,
                        provider_offer_id: leg.provider_offer_id,
                        origin_iata: leg.origin_iata,
                        destination_iata: leg.destination_iata,
                        depart_date: leg.depart_date,
                        return_date: leg.return_date,
                        airline_code: leg.airline_code,
                        airline_name: leg.airline_name,
                        cabin: leg.cabin,
                        passengers: leg.passengers,
                        price: leg.price,
                        currency: leg.currency,
                        deep_link: leg.deep_link,
                        price_rating: null,
                      });
                    });
                  }}
                >
                  Save all legs to holiday
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {mode === 'multi-city' && multiResults && (
        <div>
          <p className="muted">
            Provider <strong>{multiResults.provider}</strong>
            {multiResults.total_min_price && (
              <>
                {' '}
                · cheapest combined: <strong>{multiResults.currency} {multiResults.total_min_price}</strong>
              </>
            )}
          </p>
          {multiResults.legs.map((leg, i) => (
            <div className="card" key={`${leg.origin}-${leg.destination}-${i}`}>
              <strong>
                Leg {i + 1}: {leg.origin} → {leg.destination}
              </strong>{' '}
              <span className="muted">{leg.depart_date}</span>
              {leg.error && <div className="error">{leg.error}</div>}
              {leg.offers.length === 0 && !leg.error && (
                <p className="muted">No offers found for this leg.</p>
              )}
              {leg.offers.map((o, j) => (
                <div
                  key={`${o.provider_offer_id}-${j}`}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                    padding: '0.5rem 0',
                    borderTop: j === 0 ? undefined : '1px solid #eee',
                  }}
                >
                  <div className="muted">
                    {o.airline_name ?? o.airline_code ?? '—'}
                    {o.cabin ? ` · ${o.cabin}` : ''}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'baseline' }}>
                    <strong>{o.currency} {o.price}</strong>
                    <button
                      className="btn secondary"
                      disabled={saveMut.isPending}
                      onClick={() => saveMut.mutate(o)}
                    >
                      Save leg
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SingleRouteForm({
  currencyDefault,
  providers,
  onResults,
  onError,
}: {
  currencyDefault: string;
  providers: string[];
  onResults: (provider: string, offers: SearchOffer[], analysis: PriceAnalysisDto | null) => void;
  onError: (msg: string) => void;
}) {
  const { register, handleSubmit, formState: { isSubmitting } } = useForm<SearchInput>({
    defaultValues: {
      origin: '',
      destination: '',
      passengers: 1,
      currency: currencyDefault,
      max_results: 10,
    },
  });
  const onSubmit = async (values: SearchInput) => {
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
      onResults(resp.provider, resp.offers, resp.price_analysis);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Search failed');
    }
  };
  return (
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
            {providers.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="form-row">
        <div>
          <label>Min duration (days)</label>
          <input type="number" min={1} max={365} {...register('min_duration_days')} />
        </div>
        <div>
          <label>Max duration (days)</label>
          <input type="number" min={1} max={365} {...register('max_duration_days')} />
        </div>
        <div />
      </div>
      <div style={{ marginTop: '0.75rem' }}>
        <button className="btn" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Searching...' : 'Search'}
        </button>
      </div>
    </form>
  );
}

interface MultiFormValues {
  legs: { origin: string; destination: string; depart_date: string }[];
  passengers: number;
  currency: string;
  cabin: string;
  max_price_per_leg?: string;
  provider?: string;
}

function MultiCityForm({
  mode,
  currencyDefault,
  providers,
  onSeparateResults,
  onSinglePnrResults,
  onError,
}: {
  mode: MultiSubMode;
  currencyDefault: string;
  providers: string[];
  onSeparateResults: (r: {
    provider: string;
    legs: LegResult[];
    total_min_price: string | null;
    currency: string;
  }) => void;
  onSinglePnrResults: (r: { provider: string; offers: SinglePnrOffer[] }) => void;
  onError: (msg: string) => void;
}) {
  const { register, control, handleSubmit, formState: { isSubmitting } } = useForm<MultiFormValues>({
    defaultValues: {
      legs: [
        { origin: '', destination: '', depart_date: '' },
        { origin: '', destination: '', depart_date: '' },
      ],
      passengers: 1,
      currency: currencyDefault,
      cabin: '',
    },
  });
  const { fields, append, remove } = useFieldArray({ control, name: 'legs' });

  const onSubmit = async (values: MultiFormValues) => {
    try {
      const body: MultiLegInput = {
        legs: values.legs.map((l) => ({
          origin: l.origin.toUpperCase(),
          destination: l.destination.toUpperCase(),
          depart_date: l.depart_date,
        })),
        passengers: Number(values.passengers ?? 1),
        currency: values.currency,
        cabin: values.cabin || null,
        max_price_per_leg: values.max_price_per_leg?.toString() || null,
        provider: values.provider || null,
        max_results_per_leg: 5,
      };
      if (mode === 'single-pnr') {
        const resp = await searchApi.multiCitySinglePnr(body);
        onSinglePnrResults(resp);
      } else {
        const resp = await searchApi.multiLeg(body);
        onSeparateResults(resp);
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Search failed');
    }
  };

  return (
    <form className="card" onSubmit={handleSubmit(onSubmit)}>
      {fields.map((f, idx) => (
        <div className="form-row" key={f.id} style={{ alignItems: 'flex-end' }}>
          <div>
            <label>Leg {idx + 1} origin</label>
            <input maxLength={3} {...register(`legs.${idx}.origin` as const, { required: true, minLength: 3 })} />
          </div>
          <div>
            <label>Destination</label>
            <input maxLength={3} {...register(`legs.${idx}.destination` as const, { required: true, minLength: 3 })} />
          </div>
          <div>
            <label>Depart</label>
            <input type="date" {...register(`legs.${idx}.depart_date` as const, { required: true })} />
          </div>
          <div style={{ flex: '0 0 auto' }}>
            <button
              type="button"
              className="btn secondary"
              disabled={fields.length <= 2}
              onClick={() => remove(idx)}
            >
              Remove
            </button>
          </div>
        </div>
      ))}
      <div style={{ marginTop: '0.5rem' }}>
        <button
          type="button"
          className="btn secondary"
          disabled={fields.length >= 8}
          onClick={() => append({ origin: '', destination: '', depart_date: '' })}
        >
          Add leg
        </button>
      </div>
      <div className="form-row" style={{ marginTop: '0.75rem' }}>
        <div>
          <label>Passengers</label>
          <input type="number" min={1} {...register('passengers')} />
        </div>
        <div>
          <label>Currency</label>
          <input maxLength={3} {...register('currency')} />
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
          <label>Max price per leg</label>
          <input type="number" step="0.01" min={0} {...register('max_price_per_leg')} />
        </div>
        <div>
          <label>Provider</label>
          <select {...register('provider')}>
            <option value="">Default</option>
            {providers.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <div />
      </div>
      <div style={{ marginTop: '0.75rem' }}>
        <button className="btn" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Searching...' : 'Search legs'}
        </button>
      </div>
    </form>
  );
}

function ResultsList({
  provider,
  offers,
  onSave,
  saving,
}: {
  provider: string | null;
  offers: SearchOffer[];
  onSave: (o: SearchOffer) => void;
  saving: boolean;
}) {
  return (
    <div>
      <p className="muted">
        {offers.length} result(s) from <strong>{provider}</strong>
      </p>
      {offers.length === 0 && <p>No matching offers found.</p>}
      {offers.map((o, i) => (
        <div className="card" key={`${o.provider}-${o.provider_offer_id}-${i}`}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <div>
              <strong>{o.origin_iata} → {o.destination_iata}</strong>
              <PriceRatingBadge rating={o.price_rating} />{' '}
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
            <button className="btn" disabled={saving} onClick={() => onSave(o)}>
              Save to holiday
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
