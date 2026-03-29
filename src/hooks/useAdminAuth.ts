import { useState, useCallback } from 'react';
import { adminFetch } from '../api/client';

export function useAdminAuth() {
  const [adminKey, setAdminKeyState] = useState<string | null>(
    () => sessionStorage.getItem('mccaa_admin_key')
  );

  const login = useCallback(async (key: string) => {
    await adminFetch('/admin/articles?status=draft', key);
    sessionStorage.setItem('mccaa_admin_key', key);
    setAdminKeyState(key);
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem('mccaa_admin_key');
    setAdminKeyState(null);
  }, []);

  return { adminKey, isAuthenticated: adminKey !== null, login, logout };
}
