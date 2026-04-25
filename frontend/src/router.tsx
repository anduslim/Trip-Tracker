import { Navigate, createBrowserRouter } from 'react-router-dom';
import { AppShell } from '@/components/AppShell';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { ComparisonPage } from '@/pages/ComparisonPage';
import { FlightSearchPage } from '@/pages/FlightSearchPage';
import { HolidayDetailPage } from '@/pages/HolidayDetailPage';
import { HolidaysListPage } from '@/pages/HolidaysListPage';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { NotificationsPage } from '@/pages/NotificationsPage';
import { PublicSharePage } from '@/pages/PublicSharePage';
import { RegisterPage } from '@/pages/RegisterPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/holidays" replace /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      { path: 'share/:token', element: <PublicSharePage /> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: 'holidays', element: <HolidaysListPage /> },
          { path: 'holidays/:id', element: <HolidayDetailPage /> },
          { path: 'holidays/:id/search', element: <FlightSearchPage /> },
          { path: 'holidays/:id/compare', element: <ComparisonPage /> },
          { path: 'notifications', element: <NotificationsPage /> },
        ],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
