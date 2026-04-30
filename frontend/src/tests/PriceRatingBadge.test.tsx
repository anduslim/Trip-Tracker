import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PriceRatingBadge } from '@/components/PriceRatingBadge';

describe('PriceRatingBadge', () => {
  it('renders nothing when rating is null', () => {
    const { container } = render(<PriceRatingBadge rating={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders a label for each rating', () => {
    const { rerender } = render(<PriceRatingBadge rating="cheap" />);
    expect(screen.getByText(/bargain/i)).toBeInTheDocument();
    rerender(<PriceRatingBadge rating="good" />);
    expect(screen.getByText(/good price/i)).toBeInTheDocument();
    rerender(<PriceRatingBadge rating="typical" />);
    expect(screen.getByText(/typical/i)).toBeInTheDocument();
    rerender(<PriceRatingBadge rating="expensive" />);
    expect(screen.getByText(/expensive/i)).toBeInTheDocument();
  });
});
