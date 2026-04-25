const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '') as string;

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

type RequestInitJson = Omit<RequestInit, 'body'> & { body?: unknown };

export async function request<T>(path: string, init: RequestInitJson = {}): Promise<T> {
  const headers = new Headers(init.headers);
  let body = init.body as BodyInit | undefined;
  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
    body = JSON.stringify(init.body);
  }
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;
  const resp = await fetch(url, {
    ...init,
    headers,
    body,
    credentials: 'include',
  });
  if (resp.status === 204) {
    return undefined as T;
  }
  const contentType = resp.headers.get('content-type') ?? '';
  const payload = contentType.includes('application/json') ? await resp.json() : await resp.text();
  if (!resp.ok) {
    const detail = (payload && typeof payload === 'object' && 'detail' in payload)
      ? (payload as { detail: unknown }).detail
      : payload;
    throw new ApiError(resp.status, detail);
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
