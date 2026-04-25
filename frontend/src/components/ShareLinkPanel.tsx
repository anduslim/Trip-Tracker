import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { shareApi } from '@/api/share';

export function ShareLinkPanel({ holidayId }: { holidayId: number }) {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ['share', holidayId],
    queryFn: () => shareApi.get(holidayId),
  });
  const create = useMutation({
    mutationFn: () => shareApi.create(holidayId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['share', holidayId] }),
  });
  const revoke = useMutation({
    mutationFn: () => shareApi.revoke(holidayId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['share', holidayId] }),
  });

  if (isLoading) return null;
  return (
    <div className="card">
      <strong>Share with family / friends</strong>
      {data ? (
        <div style={{ marginTop: '0.5rem' }}>
          <p className="muted" style={{ marginBottom: '0.25rem' }}>
            Anyone with this link sees a read-only view. Source URLs and notes are hidden.
          </p>
          <div className="form-row">
            <input value={data.url} readOnly />
            <button
              className="btn secondary"
              type="button"
              onClick={async () => {
                await navigator.clipboard.writeText(data.url);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
            <button className="btn secondary" onClick={() => create.mutate()}>
              Rotate
            </button>
            <button className="btn danger" onClick={() => revoke.mutate()}>
              Revoke
            </button>
          </div>
        </div>
      ) : (
        <div style={{ marginTop: '0.5rem' }}>
          <p className="muted">No active share link.</p>
          <button className="btn" onClick={() => create.mutate()}>
            Generate share link
          </button>
        </div>
      )}
    </div>
  );
}
