'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Bell,
  Calendar,
  CheckSquare,
  Sparkles,
  Check,
  CheckCheck,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatRelativeTime } from '@/lib/utils';
import { toast } from 'sonner';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadNotifs() {
      try {
        const res = await fetch('http://localhost:8000/api/v1/notifications/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          setNotifications(data.items || []);
          return;
        }
      } catch {
        setNotifications([]);
      }
    }

    loadNotifs().finally(() => setLoading(false));
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await fetch('http://localhost:8000/api/v1/notifications/read-all', {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      toast.success('All notifications marked as read');
    } catch {
      // Ignore
    }
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const handleMarkSingleRead = async (id: number) => {
    try {
      await fetch(`http://localhost:8000/api/v1/notifications/${id}/read`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      toast.success('Notification marked as read');
    } catch {
      // Ignore
    }
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'interview_alert':
        return <Calendar className="w-5 h-5 text-purple-600" />;
      case 'approval_needed':
        return <CheckSquare className="w-5 h-5 text-amber-600" />;
      default:
        return <Sparkles className="w-5 h-5 text-indigo-600" />;
    }
  };

  return (
    <DashboardLayout title="Notifications & Alerts">
      <div className="space-y-6 max-w-4xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Activity Alerts & Daily Summaries</h2>
            <p className="text-xs text-slate-500">Instant updates for recruiter invitations and approval requests</p>
          </div>

          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
            <CheckCheck className="w-3.5 h-3.5 mr-1" />
            <span>Mark All as Read</span>
          </Button>
        </div>

        {/* Notifications List */}
        <div className="space-y-3">
          {notifications.length === 0 && !loading && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/80">
              <p className="text-sm font-bold text-slate-800">No Notifications</p>
              <p className="text-xs text-slate-500 mt-1">You are all caught up! New alerts and summaries will appear here.</p>
            </div>
          )}
          {notifications.map((n) => (
            <Card
              key={n.id}
              className={`p-4 sm:p-5 transition-all ${
                !n.is_read ? 'border-l-4 border-l-indigo-600 bg-indigo-50/20' : 'bg-white'
              }`}
            >
              <div className="flex items-start gap-3.5">
                <div className="p-2.5 rounded-xl bg-slate-100 shrink-0">
                  {getIcon(n.type)}
                </div>

                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-sm font-bold text-slate-900">{n.title}</h3>
                    <span className="text-[11px] text-slate-400 whitespace-nowrap">
                      {formatRelativeTime(n.created_at)}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{n.message}</p>

                  <div className="pt-2 flex items-center justify-between">
                    {n.type === 'approval_needed' ? (
                      <Link href="/approval-queue">
                        <span className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
                          Go to Approval Queue <ArrowRight className="w-3 h-3" />
                        </span>
                      </Link>
                    ) : (
                      <span></span>
                    )}

                    {!n.is_read && (
                      <button
                        onClick={() => handleMarkSingleRead(n.id)}
                        className="text-[11px] font-semibold text-slate-500 hover:text-indigo-600 flex items-center gap-1"
                      >
                        <Check className="w-3 h-3" />
                        <span>Mark read</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
