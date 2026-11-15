'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Send,
  Building,
  MapPin,
  Calendar,
  Clock,
  CheckCircle,
  FileText,
  Filter,
  CheckSquare,
  ArrowUpRight,
  ExternalLink,
  Globe,
  Zap,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import { toast } from 'sonner';
import { API_BASE_URL } from '@/lib/api';

export default function ApplicationsPage() {
  const [activeTab, setActiveTab] = useState('all');
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const handleSyncNaukri = async () => {
    setSyncing(true);
    toast.loading('Syncing applied jobs from your official Naukri account...', { id: 'naukri-sync' });
    try {
      const res = await fetch(`${API_BASE_URL}/browser/sync-naukri-applied`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message || 'Synced successfully!', { id: 'naukri-sync' });
        const aRes = await fetch(`${API_BASE_URL}/applications/`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
        });
        if (aRes.ok) {
          const aData = await aRes.json();
          setApplications(aData.items || []);
        }
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Could not sync from Naukri. Ensure your account is connected.', { id: 'naukri-sync' });
      }
    } catch {
      toast.error('Network error syncing from Naukri', { id: 'naukri-sync' });
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    async function loadApps() {
      try {
        const res = await fetch(`${API_BASE_URL}/applications/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          setApplications(data.items || []);
          return;
        }
      } catch {
        setApplications([]);
      }
    }

    loadApps().finally(() => setLoading(false));
  }, []);

  const handleUpdateStatus = async (appId: number, newStatus: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/applications/${appId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        toast.success(`Application status updated to "${newStatus}"`);
      } else {
        toast.error('Failed to update status');
      }
    } catch {
      toast.error('Network error updating status');
    }
    setApplications((prev) =>
      prev.map((a) => (a.id === appId ? { ...a, status: newStatus } : a))
    );
  };

  const handleRetryPortal = async (app: any) => {
    try {
      toast.info(`Opening ${app.company} in browser to retry...`);
      const res = await fetch(`${API_BASE_URL}/browser/open-portal-apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          job_id: app.job_id,
          platform: app.platform,
          url: app.url,
        }),
      });
      if (res.ok) {
        toast.success(`Opened ${app.job_title} on ${app.platform}! Complete application on the portal.`);
      } else {
        window.open(app.url, '_blank');
      }
    } catch {
      window.open(app.url, '_blank');
    }
  };

  const filteredApps =
    activeTab === 'all'
      ? applications
      : applications.filter((a) => a.status === activeTab);

  const getStatusVariant = (st: string) => {
    switch (st) {
      case 'interview':
        return 'success';
      case 'applied':
        return 'primary';
      case 'pending_approval':
        return 'warning';
      case 'rejected':
      case 'withdrawn':
      case 'failed':
        return 'danger';
      default:
        return 'default';
    }
  };

  const tabs = [
    { id: 'all', label: 'All Applications', count: applications.length },
    {
      id: 'pending_approval',
      label: 'Pending Review',
      count: applications.filter((a) => a.status === 'pending_approval').length,
    },
    {
      id: 'applied',
      label: 'Applied',
      count: applications.filter((a) => a.status === 'applied').length,
    },
    {
      id: 'failed',
      label: 'Failed / Action Needed',
      count: applications.filter((a) => a.status === 'failed').length,
    },
    {
      id: 'interview',
      label: 'Interviews',
      count: applications.filter((a) => a.status === 'interview').length,
    },
  ];

  return (
    <DashboardLayout title="Application Tracking & Pipeline">
      <div className="space-y-6">
        {/* Filter Tabs & Sync Action Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200">
          <div className="flex items-center gap-2 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 text-xs font-semibold rounded-lg flex items-center gap-2 whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                    activeTab === tab.id
                      ? 'bg-white/20 text-white'
                      : 'bg-slate-200 text-slate-700'
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            loading={syncing}
            onClick={handleSyncNaukri}
            className="text-xs font-semibold text-indigo-700 border-indigo-200 hover:bg-indigo-50 shrink-0 self-start sm:self-auto cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
            <span>Sync Naukri Applied Jobs</span>
          </Button>
        </div>

        {/* Application Cards */}
        <div className="space-y-3">
          {filteredApps.length === 0 && !loading && (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/80">
              <p className="text-sm font-bold text-slate-800">No applications in this category</p>
              <p className="text-xs text-slate-500 mt-1">Browse matched jobs and add them to your pipeline.</p>
              <div className="mt-4">
                <Link href="/jobs">
                  <Button variant="primary" size="sm">
                    <span>Browse Jobs</span>
                  </Button>
                </Link>
              </div>
            </div>
          )}
          {filteredApps.map((app) => (
            <Card key={app.id} hover className="p-5 flex flex-col justify-between gap-3">
              {/* Top Platform Source Header Badge */}
              {app.platform === 'indeed' ? (
                <div className="flex items-center justify-between pb-2 mb-1 border-b border-blue-100">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-black tracking-wider uppercase bg-blue-600 text-white shadow-xs">
                    <Globe className="w-3.5 h-3.5" />
                    <span>INDEED.COM APPLICATION</span>
                  </div>
                  <a
                    href="https://in.indeed.com/myjobs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 px-2.5 py-0.5 rounded-full border border-blue-200 flex items-center gap-1 transition-colors"
                    title="Check official Indeed account"
                  >
                    <span>Check Indeed Portal</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              ) : (
                <div className="flex items-center justify-between pb-2 mb-1 border-b border-indigo-100">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-black tracking-wider uppercase bg-indigo-600 text-white shadow-xs">
                    <Globe className="w-3.5 h-3.5" />
                    <span>NAUKRI.COM APPLICATION</span>
                  </div>
                  <a
                    href="https://www.naukri.com/mnjuser/homepage"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-2.5 py-0.5 rounded-full border border-indigo-200 flex items-center gap-1 transition-colors"
                    title="Check official Naukri account"
                  >
                    <span>Check Naukri &quot;Applied Jobs&quot;</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-sm sm:text-base text-slate-900">
                      {app.job_title}
                    </span>
                    <Badge variant={getStatusVariant(app.status)} size="sm" className="capitalize">
                      {app.status.replace('_', ' ')}
                    </Badge>
                    {app.score !== undefined && app.score !== null && (
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {app.score}% Match
                      </span>
                    )}
                    <Badge variant="outline" size="sm" className="capitalize">
                      Method: {app.method}
                    </Badge>
                  </div>

                <div className="flex items-center gap-4 text-xs text-slate-600 flex-wrap">
                  <span className="font-semibold text-slate-800 flex items-center gap-1">
                    <Building className="w-3.5 h-3.5 text-slate-400" />
                    {app.company}
                  </span>
                  {app.location && (
                    <span className="flex items-center gap-1 text-slate-500">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {app.location}
                    </span>
                  )}
                  <span className="flex items-center gap-1 text-slate-400">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    Applied: {formatDate(app.submitted_at || app.created_at)}
                  </span>
                </div>

                {app.notes && (
                  <p className="text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    {app.notes}
                  </p>
                )}
              </div>

              {/* Status Action Selector */}
              <div className="flex items-center gap-2 shrink-0">
                {app.url && (
                  <a
                    href={app.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-slate-100 transition-colors"
                    title="Open vacancy posting"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}

                <select
                  value={app.status}
                  onChange={(e) => handleUpdateStatus(app.id, e.target.value)}
                  aria-label="Update Application Status"
                  className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="pending_approval">Pending Review</option>
                  <option value="applied">Applied</option>
                  <option value="failed">Failed / Attention Needed</option>
                  <option value="viewed">Viewed by Recruiter</option>
                  <option value="interview">Interview Scheduled</option>
                  <option value="offer">Offer Received</option>
                  <option value="rejected">Rejected</option>
                  <option value="withdrawn">Withdrawn</option>
                </select>

                {app.status === 'failed' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRetryPortal(app)}
                    className="text-xs border-rose-300 text-rose-700 hover:bg-rose-50"
                  >
                    <Zap className="w-3.5 h-3.5 mr-1" />
                    <span>Retry Apply</span>
                  </Button>
                )}

                {app.status === 'pending_approval' && (
                  <Link href="/approval-queue">
                    <Button variant="primary" size="sm">
                      <CheckSquare className="w-3.5 h-3.5 mr-1" />
                      <span>Review</span>
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
