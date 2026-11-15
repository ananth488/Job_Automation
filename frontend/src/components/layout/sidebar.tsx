'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Briefcase,
  CheckSquare,
  Send,
  FileText,
  Sliders,
  Bot,
  Bell,
  Settings,
  Sparkles,
  ChevronRight,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/use-auth';

export interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const pathname = usePathname();
  const { user, initials, logout } = useAuth();
  const [counts, setCounts] = useState<{ queue: number; notifs: number }>({ queue: 0, notifs: 0 });

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) return;

    Promise.all([
      fetch('http://localhost:8000/api/v1/dashboard/stats', {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch('http://localhost:8000/api/v1/notifications/unread-count', {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : { count: 0 })).catch(() => ({ count: 0 })),
    ]).then(([statsData, notifData]) => {
      setCounts({
        queue: statsData?.pending_approval ?? 0,
        notifs: notifData?.count || 0,
      });
    });
  }, [pathname]);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Resume & Profile', href: '/profile', icon: FileText },
    { name: 'Preferences', href: '/preferences', icon: Sliders },
    { name: 'Job Discovery', href: '/jobs', icon: Briefcase },
    {
      name: 'Approval Queue',
      href: '/approval-queue',
      icon: CheckSquare,
      badge: counts.queue > 0 ? String(counts.queue) : undefined,
    },
    { name: 'Applications Tracker', href: '/applications', icon: Send },
    { name: 'Bot Controls', href: '/bot-controls', icon: Bot },
    {
      name: 'Notifications',
      href: '/notifications',
      icon: Bell,
      badge: counts.notifs > 0 ? String(counts.notifs) : undefined,
    },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={cn(
          'fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-900 text-white flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 border-r border-slate-800',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Brand header */}
        <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800/80">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-md shadow-indigo-500/30">
            <Sparkles className="w-5 h-5 text-indigo-100" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
              AI Job Bot
              <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
                PRO
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">Naukri & Indeed Automated</p>
          </div>
        </div>

        {/* Bot active indicator pill */}
        <div className="px-4 py-3 mx-4 my-3 rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-medium text-slate-200">Bot Active</span>
          </div>
          <span className="text-[10px] text-slate-400">Every 6h</span>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'group flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={cn(
                      'w-4 h-4 transition-colors',
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'
                    )}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      'text-[10px] font-bold px-1.5 py-0.5 rounded-full',
                      isActive ? 'bg-white/20 text-white' : 'bg-indigo-500/30 text-indigo-300'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User footer info & Switch User / Sign Out */}
        <div className="p-3 mx-2 my-2 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-indigo-600/40 border border-indigo-500/50 flex items-center justify-center font-bold text-xs text-indigo-300 shrink-0">
              {initials}
            </div>
            <div className="overflow-hidden min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.full_name || 'Candidate'}</p>
              <p className="text-[10px] text-slate-400 truncate">{user?.email || 'Logged In'}</p>
            </div>
          </div>
          <button
            onClick={logout}
            title="Sign Out / Switch User"
            className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-700/50 transition-colors shrink-0"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>
    </>
  );
};

