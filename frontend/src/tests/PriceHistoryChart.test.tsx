import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PriceHistoryChart } from '@/components/PriceHistoryChart';
import type { PriceSnapshot } from '@/types/api';

describe('PriceHistoryChart', () => {
  it('shows empty state when there are no snapshots', () => {
    render(<PriceHistoryChart snapshots={[]} currency="USD" />);
    expect(screen.getByText(/no price history/i)).toBeInTheDocument();
  });

  it('does not show empty state when snapshots are present', () => {
    const snaps: PriceSnapshot[] = [
      {
        id: 1,
        flight_entry_id: 1,
        price: '100.00',
        currency: 'USD',
        source: 'manual',
        captured_at: '2026-04-01T00:00:00Z',
      },
      {
        id: 2,
        flight_entry_id: 1,
        price: '120.00',
        currency: 'USD',
        source: 'manual',
        captured_at: '2026-04-05T00:00:00Z',
      },
    ];
    render(<PriceHistoryChart snapshots={snaps} currency="USD" />);
    expect(screen.queryByText(/no price history/i)).toBeNull();
  });
});
