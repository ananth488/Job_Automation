'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { setAuthCookie, clearAuthCookie } from '@/lib/auth-cookie';

export interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children, title }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (!token) {
        clearAuthCookie();
        router.replace('/login');
      } else {
        setAuthCookie(token);
      }
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar Navigation wrapped in Suspense */}
      <Suspense fallback={<aside className="hidden lg:block w-64 bg-slate-900" />}>
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      </Suspense>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} title={title} />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
};
