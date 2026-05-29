import { Navigate, Outlet } from 'react-router-dom';

import { useAuthStore } from '@/domains/auth/store';

/** Gate for the app shell: render child routes only when a token is present. */
export function RequireAuth() {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (accessToken === null) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
