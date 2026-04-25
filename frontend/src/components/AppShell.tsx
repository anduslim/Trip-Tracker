import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div>
      <header className="navbar">
        <h1>
          <Link to="/holidays">Trip Price Tracker</Link>
        </h1>
        <nav>
          {user ? (
            <>
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
