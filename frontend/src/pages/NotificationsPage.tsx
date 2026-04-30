import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '@/api/notifications';

export function NotificationsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list(false),
  });
  const markRead = useMutation({
    mutationFn: (id: number) => notificationsApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });
  const markAll = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });

  if (isLoading) return <p>Loading...</p>;
  const items = data ?? [];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Notifications</h2>
        {items.some((n) => !n.read_at) && (
          <button className="btn secondary" onClick={() => markAll.mutate()}>
            Mark all read
          </button>
        )}
      </div>
      {items.length === 0 ? (
        <p className="muted">No notifications yet.</p>
      ) : (
        items.map((n) => (
          <div
            className="card"
            key={n.id}
            style={{ borderLeft: n.read_at ? undefined : '4px solid #2856e0' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>{n.title}</strong>
              <span className="muted">{new Date(n.created_at).toLocaleString()}</span>
            </div>
            <p style={{ margin: '0.5rem 0' }}>{n.body}</p>
            {!n.read_at && (
              <button className="btn secondary" onClick={() => markRead.mutate(n.id)}>
                Mark read
              </button>
            )}
          </div>
        ))
      )}
    </div>
  );
}
