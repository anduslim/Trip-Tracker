import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="card">
      <h2>Not found</h2>
      <p>That page doesn't exist.</p>
      <Link to="/holidays">Go to holidays</Link>
    </div>
  );
}
