'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { Menu, Bell, Play, CheckCircle2, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/use-auth';
import { API_BASE_URL } from '@/lib/api';

export interface HeaderProps {
  onMenuToggle: () => void;
  title?: string;
}

export const Header: React.FC<HeaderProps> = ({ onMenuToggle, title = 'Dashboard' }) => {
  const router = useRouter();
  const pathname = usePathname();
  const { user, initials } = useAuth();
  const [isRunning, setIsRunning] = useState(false);
  const [isVerified, setIsVerified] = useState<boolean | null>(null);
  const [platformStatus, setPlatformStatus] = useState<{
    naukri: { logged_in: boolean; email?: string | null };
    indeed: { logged_in: boolean; email?: string | null };
  }>({
    naukri: { logged_in: false, email: null },
    indeed: { logged_in: false, email: null },
  });

  const checkStatus = useCallback(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) {
      setIsVerified(false);
      return;
    }

    Promise.all([
      fetch(`${API_BASE_URL}/profile/`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : null)),
      fetch(`${API_BASE_URL}/browser/session-status`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : null)),
    ])
      .then(([profData, sessionData]) => {
        if (profData && profData.is_verified && profData.skills && profData.skills.length > 0) {
          setIsVerified(true);
        } else {
          setIsVerified(false);
        }

        if (sessionData) {
          setPlatformStatus({
            naukri: {
              logged_in: Boolean(sessionData.naukri?.logged_in),
              email: sessionData.naukri?.email || null,
            },
            indeed: {
              logged_in: Boolean(sessionData.indeed?.logged_in),
              email: sessionData.indeed?.email || null,
            },
          });
        }
      })
      .catch(() => setIsVerified(false));
  }, []);

  useEffect(() => {
    checkStatus();

    const handleProfileUpdate = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail && typeof customEvent.detail.is_verified === 'boolean') {
        const hasSkills = Boolean(customEvent.detail.skills && customEvent.detail.skills.length > 0);
        setIsVerified(customEvent.detail.is_verified && hasSkills);
      } else {
        checkStatus();
      }
    };

    const handleConnectionUpdate = () => {
      checkStatus();
    };

    window.addEventListener('profile-status-changed', handleProfileUpdate);
    window.addEventListener('account-connection-changed', handleConnectionUpdate);
    return () => {
      window.removeEventListener('profile-status-changed', handleProfileUpdate);
      window.removeEventListener('account-connection-changed', handleConnectionUpdate);
    };
  }, [checkStatus, pathname]);

  const handleRunBot = async () => {
    // 1. Client-side check: if profile is not verified, warn and redirect!
    if (isVerified === false) {
      toast.error('Resume & Profile verification required before running bot! Redirecting to Profile...');
      setTimeout(() => {
        router.push('/profile');
      }, 1000);
      return;
    }

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) {
      toast.error('You are not logged in. Redirecting to login...');
      setTimeout(() => {
        router.push('/login');
      }, 1000);
      return;
    }

    setIsRunning(true);
    try {
      const res = await fetch(`${API_BASE_URL}/bot/run-now`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        const data = await res.json();
        const found = data.details?.jobs_found ?? 0;
        const matched = data.details?.jobs_matched ?? 0;
        toast.success(`Bot completed run: ${found} jobs found, ${matched} shortlisted!`);
        // Refresh page data if on dashboard
        if (typeof window !== 'undefined' && window.location.pathname === '/dashboard') {
          setTimeout(() => window.location.reload(), 1500);
        }
      } else if (res.status === 400) {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Resume & Profile verification required before running bot! Redirecting to Profile...');
        setTimeout(() => {
          router.push('/profile');
        }, 1200);
      } else if (res.status === 401) {
        toast.error('Session expired. Please sign in again.');
        localStorage.removeItem('access_token');
        setTimeout(() => {
          router.push('/login');
        }, 1200);
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Bot execution failed');
      }
    } catch {
      toast.error('Failed to communicate with bot server');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 focus:outline-none"
          aria-label="Toggle navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">{title}</h2>
          <p className="hidden sm:block text-[11px] text-slate-500">Autonomous Job Application Pipeline</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Trigger Cycle Button */}
        <Button
          variant="outline"
          size="sm"
          loading={isRunning}
          onClick={handleRunBot}
          className="hidden sm:inline-flex border-indigo-200 text-indigo-600 hover:bg-indigo-50"
        >
          <Play className="w-3.5 h-3.5 fill-indigo-600" />
          <span>Run Bot Now</span>
        </Button>

        {/* Notifications Icon */}
        <div className="relative">
          <Link
            href="/notifications"
            className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors relative block"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white"></span>
          </Link>
        </div>

        {/* Dynamic Profile Verification status pill */}
        {isVerified ? (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Profile Verified</span>
          </div>
        ) : (
          <Link
            href="/profile"
            className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 hover:bg-amber-100 text-xs font-semibold transition-colors"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Complete Profile</span>
          </Link>
        )}

        {/* Connected Platform Badges */}
        {platformStatus.naukri.logged_in && (
          <Link
            href="/bot-controls"
            title={`Naukri Connected${platformStatus.naukri.email ? `: ${platformStatus.naukri.email}` : ''}`}
            className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 hover:bg-indigo-100 text-xs font-semibold transition-colors"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Naukri Logged In</span>
          </Link>
        )}

        {platformStatus.indeed.logged_in && (
          <Link
            href="/bot-controls"
            title={`Indeed Connected${platformStatus.indeed.email ? `: ${platformStatus.indeed.email}` : ''}`}
            className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 text-xs font-semibold transition-colors"
          >
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            <span>Indeed Logged In</span>
          </Link>
        )}

        {/* User Avatar */}
        <Link
          href="/profile"
          title={user?.full_name || 'Profile'}
          className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-xs hover:ring-2 hover:ring-indigo-400 transition-all"
        >
          {initials}
        </Link>
      </div>
    </header>
  );
};
