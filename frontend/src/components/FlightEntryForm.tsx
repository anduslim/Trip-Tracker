import { useForm } from 'react-hook-form';
import type { FlightInput } from '@/api/flights';

export function FlightEntryForm({
  onSubmit,
  submitting,
  defaultCurrency,
}: {
  onSubmit: (values: FlightInput) => void;
  submitting: boolean;
  defaultCurrency: string;
}) {
  const { register, handleSubmit, reset } = useForm<FlightInput>({
    defaultValues: {
      passengers: 1,
      currency: defaultCurrency,
      tracking_enabled: true,
    },
  });
  return (
    <form
      className="card"
      onSubmit={handleSubmit((v) => {
        onSubmit(v);
        reset({ passengers: 1, currency: defaultCurrency, tracking_enabled: true });
      })}
    >
      <h3 style={{ marginTop: 0 }}>Add a flight</h3>
      <div className="form-row">
        <div>
          <label>Origin (IATA)</label>
          <input maxLength={3} {...register('origin_iata', { required: true, minLength: 3, maxLength: 3 })} />
        </div>
        <div>
          <label>Destination (IATA)</label>
          <input maxLength={3} {...register('destination_iata', { required: true, minLength: 3, maxLength: 3 })} />
        </div>
        <div>
          <label>Passengers</label>
          <input type="number" min={1} {...register('passengers', { valueAsNumber: true })} />
        </div>
      </div>
      <div className="form-row">
        <div>
          <label>Depart date</label>
          <input type="date" {...register('depart_date', { required: true })} />
        </div>
        <div>
          <label>Return date</label>
          <input type="date" {...register('return_date')} />
        </div>
      </div>
      <div className="form-row">
        <div>
          <label>Airline</label>
          <input placeholder="UA / United" {...register('airline_name')} />
        </div>
        <div>
          <label>Cabin</label>
          <input placeholder="ECONOMY" {...register('cabin')} />
        </div>
      </div>
      <label>Source URL (where you saw this price)</label>
      <input type="url" placeholder="https://..." {...register('source_url')} />
      <div className="form-row">
        <div>
          <label>Initial price</label>
          <input
            type="number"
            step="0.01"
            min={0}
            {...register('initial_price', { required: true })}
          />
        </div>
        <div>
          <label>Currency</label>
          <input maxLength={3} {...register('currency')} />
        </div>
      </div>
      <div style={{ marginTop: '0.75rem' }}>
        <button className="btn" type="submit" disabled={submitting}>
          Add flight
        </button>
      </div>
    </form>
  );
}
