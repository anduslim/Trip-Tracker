import { useQuery } from '@tanstack/react-query';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { notificationsApi } from '@/api/notifications';
import { useAuth } from '@/context/AuthContext';

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { data: unread } = useQuery({
    queryKey: ['unread-count'],
    queryFn: notificationsApi.unreadCount,
    enabled: !!user,
    refetchInterval: 30_000,
  });

  return (
    <div>
      <header className="navbar">
        <h1>
          <Link to="/holidays">Trip Price Tracker</Link>
        </h1>
        <nav>
          {user ? (
            <>
              <Link to="/notifications" style={{ marginRight: '1rem' }}>
                Notifications{unread && unread.unread > 0 ? ` (${unread.unread})` : ''}
              </Link>
              <span className="muted">{user.email}</span>{' '}
              <button
                className="btn secondary"
                onClick={async () => {
                  await logout();
                  navigate('/login');
                }}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </header>
      <main className="app-shell">
        <Outlet />
      </main>
    </div>
  );
}
