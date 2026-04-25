import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { useAuth } from '@/context/AuthContext';

interface FormValues {
  email: string;
  password: string;
  display_name?: string;
}

export function RegisterPage() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { isSubmitting } } = useForm<FormValues>();

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      await registerUser(values.email, values.password, values.display_name);
      navigate('/holidays', { replace: true });
    } catch (err) {
      setServerError(err instanceof ApiError ? String(err.detail ?? err.message) : 'Registration failed');
    }
  };

  return (
    <div className="card" style={{ maxWidth: 420, margin: '2rem auto' }}>
      <h2>Create account</h2>
      <form onSubmit={handleSubmit(onSubmit)}>
        <label>Display name</label>
        <input {...register('display_name')} />
        <label>Email</label>
        <input type="email" autoComplete="email" {...register('email', { required: true })} />
        <label>Password (min 8 chars)</label>
        <input type="password" autoComplete="new-password" {...register('password', { required: true, minLength: 8 })} />
        {serverError && <div className="error">{serverError}</div>}
        <div style={{ marginTop: '1rem' }}>
          <button className="btn" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create account'}
          </button>
        </div>
      </form>
      <p className="muted" style={{ marginTop: '1rem' }}>
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </div>
  );
}
