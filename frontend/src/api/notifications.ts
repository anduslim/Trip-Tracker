import { api } from './client';

export interface Notification {
  id: number;
  user_id: number;
  holiday_id: number | null;
  flight_entry_id: number | null;
  type: string;
  title: string;
  body: string;
  extra: Record<string, unknown> | null;
  read_at: string | null;
  email_status: string;
  created_at: string;
}

export const notificationsApi = {
  list: (unreadOnly = false) =>
    api.get<Notification[]>(`/api/notifications?unread_only=${unreadOnly}`),
  unreadCount: () => api.get<{ unread: number }>('/api/notifications/unread-count'),
  markRead: (id: number) => api.post<void>(`/api/notifications/${id}/read`),
  markAllRead: () => api.post<void>('/api/notifications/read-all'),
};
