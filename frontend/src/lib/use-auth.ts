'use client';

import { useState, useEffect } from 'react';

export interface CurrentUser {
  id: number | string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export function useAuth() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Try reading cached user from localStorage for instant display
    try {
      const cached = localStorage.getItem('user');
      if (cached) {
        setUser(JSON.parse(cached));
      }
    } catch {
      // Ignore JSON parse errors
    }

    // 2. Fetch fresh user details from /auth/me
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    fetch('http://localhost:8000/api/v1/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (res.ok) {
          return res.json();
        }
        if (res.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          setUser(null);
        }
        throw new Error('Not authenticated');
      })
      .then((data) => {
        setUser(data);
        localStorage.setItem('user', JSON.stringify(data));
      })
      .catch(() => {
        // Token might be invalid or demo token
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const getInitials = (name?: string) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  };

  return {
    user,
    initials: getInitials(user?.full_name),
    loading,
    logout,
  };
}

