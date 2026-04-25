import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { useAuth } from '@/context/AuthContext';

interface FormValues {
  email: string;
  password: string;
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };
  const [serverError, setServerError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { isSubmitting } } = useForm<FormValues>();

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      await login(values.email, values.password);
      navigate(location.state?.from ?? '/holidays', { replace: true });
    } catch (err) {
      setServerError(err instanceof ApiError ? String(err.detail ?? err.message) : 'Login failed');
    }
  };

  return (
    <div className="card" style={{ maxWidth: 420, margin: '2rem auto' }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit(onSubmit)}>
        <label>Email</label>
        <input type="email" autoComplete="email" {...register('email', { required: true })} />
        <label>Password</label>
        <input type="password" autoComplete="current-password" {...register('password', { required: true })} />
        {serverError && <div className="error">{serverError}</div>}
        <div style={{ marginTop: '1rem' }}>
          <button className="btn" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>
        </div>
      </form>
      <p className="muted" style={{ marginTop: '1rem' }}>
        No account? <Link to="/register">Register</Link>
      </p>
    </div>
  );
}
