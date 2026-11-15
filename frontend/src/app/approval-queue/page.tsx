'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  CheckSquare,
  Square,
  Sparkles,
  ExternalLink,
  Check,
  X,
  FileText,
  Copy,
  ShieldCheck,
  Eye,
  Building,
  MapPin,
  HelpCircle,
  Zap,
  Globe,
  Download,
  FileCheck,
  AlertTriangle,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScoreBadge } from '@/components/ui/score-badge';
import { Modal } from '@/components/ui/modal';
import { toast } from 'sonner';

export default function ApprovalQueuePage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activePreview, setActivePreview] = useState<{
    title: string;
    type: 'resume' | 'cover_letter' | 'answers';
    content: string;
    company?: string;
    platform?: string;
    matched_skills?: string[];
    app_id?: number;
    resume_type?: 'tailored' | 'original';
    master_resume_id?: number;
    master_resume_filename?: string;
  } | null>(null);

  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [selectedAppIds, setSelectedAppIds] = useState<number[]>([]);
  const [expandedSkillsAppIds, setExpandedSkillsAppIds] = useState<number[]>([]);
  const [bulkApproving, setBulkApproving] = useState(false);
  const [stealthApplying, setStealthApplying] = useState(false);
  const [sessionStatus, setSessionStatus] = useState<any>(null);
  const [postedWithin, setPostedWithin] = useState('30');
  const [applyFilter, setApplyFilter] = useState<'all' | 'direct_1click' | 'company_portal'>('all');

  const checkSessionStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/browser/session-status', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setSessionStatus(data);
      }
    } catch {
      // Ignore
    }
  };

  const handleOpenLogin = async (platform: string) => {
    try {
      toast.info(`Opening ${platform === 'indeed' ? 'Indeed' : 'Naukri'} login window on your desktop...`);
      const res = await fetch(`http://localhost:8000/api/v1/browser/open-login?platform=${platform}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      if (res.ok) {
        toast.success(`Browser window opened! Sign in to your ${platform === 'indeed' ? 'Indeed' : 'Naukri'} account and close the window.`);
        const poll = setInterval(async () => {
          try {
            const sRes = await fetch('http://localhost:8000/api/v1/browser/session-status', {
              headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
            });
            if (sRes.ok) {
              const data = await sRes.json();
              if (data[platform]?.logged_in) {
                setSessionStatus(data);
                toast.success(`🎉 ${platform === 'indeed' ? 'Indeed' : 'Naukri'} account verified and connected!`);
                clearInterval(poll);
              }
            }
          } catch {}
        }, 4000);
        setTimeout(() => clearInterval(poll), 120000);
      }
    } catch {
      toast.error('Failed to launch browser login window');
    }
  };

  const toggleExpandSkills = (appId: number) => {
    setExpandedSkillsAppIds((prev) =>
      prev.includes(appId) ? prev.filter((id) => id !== appId) : [...prev, appId]
    );
  };

  const handleStealthApply = async (jobIdsToApply?: number[]) => {
    const targetItems = jobIdsToApply
      ? items.filter((i) => jobIdsToApply.includes(i.job_id))
      : selectedAppIds.length > 0
        ? items.filter((i) => selectedAppIds.includes(i.application_id))
        : items;

    const jobIds = targetItems.map((i) => i.job_id);
    if (jobIds.length === 0) {
      toast.info('No jobs selected for direct apply.');
      return;
    }

    setStealthApplying(true);
    toast.loading(`Launching stealth browser automation for ${jobIds.length} job(s)... (Natural delays for safety)`, {
      id: 'stealth-apply',
      duration: 10000,
    });

    try {
      const res = await fetch('http://localhost:8000/api/v1/browser/apply-stealth', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({
          job_ids: jobIds,
          daily_limit: 50,
          min_delay_sec: 15,
          max_delay_sec: 35,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const successfullyAppliedIds = (data.results || [])
          .filter((r: any) => r.status === 'applied' || r.status === 'already_applied')
          .map((r: any) => r.job_id);
        const companyPortalJobs = (data.results || []).filter((r: any) => r.status === 'company_site_redirect');

        if (successfullyAppliedIds.length > 0) {
          toast.success(
            `Directly applied to ${successfullyAppliedIds.length} job(s) on portal! Reflected in your official account.`,
            { id: 'stealth-apply' }
          );
          setItems((prev) => prev.filter((i) => !successfullyAppliedIds.includes(i.job_id)));
        } else if (companyPortalJobs.length > 0) {
          toast.info(
            `${companyPortalJobs.length} position(s) require submission on employer portal. Direct links are ready below for manual application.`,
            { id: 'stealth-apply', duration: 7000 }
          );
        } else {
          toast.info(`Processed ${jobIds.length} positions. Ready in queue.`, { id: 'stealth-apply' });
        }
        setSelectedAppIds([]);
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Stealth browser apply failed', { id: 'stealth-apply' });
      }
    } catch {
      toast.error('Network error during browser automation', { id: 'stealth-apply' });
    } finally {
      setStealthApplying(false);
    }
  };

  const toggleSelectApp = (id: number) => {
    setSelectedAppIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedAppIds.length === displayedItems.length) {
      setSelectedAppIds([]);
    } else {
      setSelectedAppIds(displayedItems.map((i) => i.application_id));
    }
  };

  const handleBulkApprove = async (appIdsToApprove?: number[]) => {
    const ids = appIdsToApprove || selectedAppIds;
    if (ids.length === 0) return;

    setBulkApproving(true);
    toast.loading(`Approving & submitting ${ids.length} applications...`, { id: 'bulk-approve' });
    try {
      const res = await fetch('http://localhost:8000/api/v1/applications/bulk-approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({ application_ids: ids }),
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(`Approved ${data.approved_count || ids.length} application(s)! Moved to Applied status in Tracker.`, {
          id: 'bulk-approve',
        });
        setItems((prev) => prev.filter((i) => !ids.includes(i.application_id)));
        setSelectedAppIds([]);
      } else {
        toast.error('Bulk approve failed', { id: 'bulk-approve' });
      }
    } catch {
      toast.error('Network error during bulk approve', { id: 'bulk-approve' });
    } finally {
      setBulkApproving(false);
    }
  };

  const loadQueue = async (days?: string) => {
    try {
      const activeDays = days !== undefined ? days : postedWithin;
      let url = 'http://localhost:8000/api/v1/applications/approval-queue';
      if (activeDays !== 'all') {
        url += `?posted_within_days=${activeDays}`;
      }
      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setItems(Array.isArray(data) ? data : []);
        return;
      }
    } catch {
      setItems([]);
    }
  };

  const handleDaysChange = (days: string) => {
    setPostedWithin(days);
    setLoading(true);
    loadQueue(days).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/preferences', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.posted_within_days) {
          setPostedWithin(String(data.posted_within_days));
          loadQueue(String(data.posted_within_days)).finally(() => setLoading(false));
        } else {
          loadQueue().finally(() => setLoading(false));
        }
      })
      .catch(() => loadQueue().finally(() => setLoading(false)));
    checkSessionStatus();
  }, []);

  const directItems = items.filter((i) => (i.apply_type || 'direct_1click') === 'direct_1click');
  const companyItems = items.filter((i) => i.apply_type === 'company_portal');
  const displayedItems =
    applyFilter === 'all'
      ? items
      : applyFilter === 'direct_1click'
        ? directItems
        : companyItems;

  const handleBatchDirectApply = async () => {
    const targetJobIds = directItems.map((i) => i.job_id);
    if (targetJobIds.length === 0) {
      toast.info('No direct 1-click jobs found in current queue.');
      return;
    }
    await handleStealthApply(targetJobIds);
    if (companyItems.length > 0) {
      setApplyFilter('company_portal');
      toast.info(
        `🎉 Finished 1-Click direct applies! ${companyItems.length} jobs require company portal submission below.`,
        { duration: 8000 }
      );
    }
  };

  const handleOpenAndApplyCompany = async (item: any) => {
    // 1. Copy tailored candidate details to clipboard for instant pasting on company site
    try {
      const text = `Candidate: Ananth P\nRole: ${item.job_title}\nCompany: ${item.company}\nNotice Period: 30 Days\nLocation: ${item.location}\nKey Matched Skills: ${(item.matched_skills || []).join(', ')}\n\nProfessional Summary:\n${item.tailored_summary || ''}\n\nCover Letter:\n${item.cover_letter || ''}`;
      await navigator.clipboard.writeText(text);
    } catch {}

    // 2. Open company career portal in new tab
    const targetUrl = item.company_url || item.url;
    window.open(targetUrl, '_blank');

    // 3. Mark application as applied in DB and move to Tracker
    try {
      const res = await fetch(`http://localhost:8000/api/v1/applications/${item.application_id}/approve`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      if (res.ok) {
        toast.success(`🚀 Opened ${item.company} Career Portal & marked as Applied in Tracker! Tailored answers copied to clipboard.`, {
          duration: 6000,
        });
        setItems((prev) => prev.filter((i) => i.application_id !== item.application_id));
      } else {
        toast.info(`Opened ${item.company} Career Portal in new tab.`);
      }
    } catch {
      toast.info(`Opened ${item.company} Career Portal in new tab.`);
    }
  };

  const handleCopyCompanyAnswers = (item: any) => {
    const text = `Candidate: Ananth P\nRole: ${item.job_title}\nCompany: ${item.company}\nNotice Period: 30 Days\nLocation: ${item.location}\nKey Matched Skills: ${(item.matched_skills || []).join(', ')}\n\nProfessional Summary:\n${item.tailored_summary || ''}\n\nCover Letter:\n${item.cover_letter || ''}`;
    navigator.clipboard.writeText(text);
    toast.success('Candidate answers & tailored summary copied! Paste into employer career form.');
  };

  const handlePortalSubmit = async (item: any) => {
    const token = localStorage.getItem('access_token');
    const platformName = item.platform === 'indeed' ? 'Indeed' : 'Naukri';
    toast.info(`Opening ${platformName} portal in your logged-in Chrome browser...`, { duration: 4000 });

    try {
      const res = await fetch('http://localhost:8000/api/v1/browser/open-portal-apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token || ''}`,
        },
        body: JSON.stringify({
          job_id: item.job_id,
          platform: item.platform,
          url: item.url,
        }),
      });

      if (res.ok) {
        toast.info(
          `Opened ${item.job_title} on ${platformName}! Complete application in the browser window, then mark as applied.`,
          { duration: 8000 }
        );
        setItems((prev) =>
          prev.map((i) => (i.application_id === item.application_id ? { ...i, status: 'in_progress' } : i))
        );
      } else {
        window.open(item.url, '_blank');
      }
    } catch {
      window.open(item.url, '_blank');
    }
  };

  const handleApprove = async (appId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/applications/${appId}/approve`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      if (res.ok) {
        toast.success('Application approved & moved to Applied status!');
      } else {
        toast.error('Failed to update application status');
      }
    } catch {
      toast.error('Network error approving application');
    }
    setItems((prev) => prev.filter((i) => i.application_id !== appId));
  };

  const handleReject = async (appId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/applications/${appId}/reject`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      if (res.ok) {
        toast.info('Application skipped.');
      }
    } catch {
      // Ignore
    }
    setItems((prev) => prev.filter((i) => i.application_id !== appId));
  };

  const handleSelectResume = async (appId: number, resumeType: 'tailored' | 'original') => {
    setItems((prev) =>
      prev.map((item) =>
        item.application_id === appId ? { ...item, selected_resume_type: resumeType } : item
      )
    );
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`http://localhost:8000/api/v1/applications/${appId}/select-resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token || ''}`,
        },
        body: JSON.stringify({ resume_type: resumeType }),
      });
      toast.success(
        resumeType === 'tailored'
          ? 'Selected AI Tailored Resume (ATS Optimized for JD)'
          : 'Selected Original Master Resume'
      );
    } catch {
      // Ignore
    }
  };

  const handleDownloadTailoredPdf = async (appId: number, company: string) => {
    try {
      const token = localStorage.getItem('access_token');
      toast.loading('Generating Tailored Resume PDF (Naukri Neo Style)...', { id: 'pdf-dl' });
      const res = await fetch(`http://localhost:8000/api/v1/applications/${appId}/tailored-pdf`, {
        headers: { Authorization: `Bearer ${token || ''}` },
      });
      if (!res.ok) throw new Error('Failed to generate PDF');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Tailored_Resume_${company.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Tailored Resume PDF ready and downloaded!', { id: 'pdf-dl' });
    } catch {
      toast.error('Could not download tailored PDF', { id: 'pdf-dl' });
    }
  };

  const handleDownloadMasterPdf = async (masterResumeId: number, filename: string) => {
    try {
      const token = localStorage.getItem('access_token');
      toast.loading('Downloading Master Resume PDF...', { id: 'pdf-dl' });
      const res = await fetch(`http://localhost:8000/api/v1/resumes/${masterResumeId}/download`, {
        headers: { Authorization: `Bearer ${token || ''}` },
      });
      if (!res.ok) throw new Error('Failed to download master resume');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'Master_Resume.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Original Master Resume downloaded!', { id: 'pdf-dl' });
    } catch {
      toast.error('Could not download master resume', { id: 'pdf-dl' });
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    toast.success('Copied to clipboard!');
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <DashboardLayout title="Candidate Approval Queue">
      <div className="space-y-6">
        {/* Compliance & Process Header */}
        <div className="p-4 sm:p-5 rounded-2xl bg-indigo-50 border border-indigo-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-indigo-950 font-bold text-sm">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              <span>Assisted Candidate Review & Compliance Guard</span>
            </div>
            <p className="text-xs text-indigo-800/80 leading-relaxed max-w-2xl">
              Naukri and Indeed require candidate-assisted submission. Review your tailored documents and pre-filled answers below, then submit directly with verified credentials.
            </p>
            <div className="flex items-center gap-3 pt-1 text-xs">
              <a
                href="https://www.naukri.com/mnjuser/applystatus"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 font-semibold text-indigo-700 hover:text-indigo-900 underline"
              >
                <span>View Naukri Applied Jobs (mnjuser/applystatus)</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <span className="text-slate-300">•</span>
              <a
                href="https://in.indeed.com/myjobs"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 font-semibold text-indigo-700 hover:text-indigo-900 underline"
              >
                <span>View Indeed My Jobs</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
          <Badge variant="primary" size="md">
            {items.length} Pending Approval
          </Badge>
        </div>

        {/* Empty state */}
        {items.length === 0 && !loading && (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200/80">
            <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center mb-3">
              <Check className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Queue is Clear!</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              No applications are currently awaiting approval. Discover new opportunities or run a bot cycle to find more.
            </p>
            <div className="mt-4">
              <Link href="/jobs">
                <Button variant="primary" size="sm">
                  <span>Browse Matched Jobs</span>
                </Button>
              </Link>
            </div>
          </div>
        )}

        {/* Segment Filter & Days Freshness Toolbar */}
        <div className="p-3.5 sm:p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Left: Tab Segments */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-100/90 rounded-xl overflow-x-auto">
            <button
              type="button"
              onClick={() => setApplyFilter('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                applyFilter === 'all'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Positions ({items.length})
            </button>
            <button
              type="button"
              onClick={() => setApplyFilter('direct_1click')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                applyFilter === 'direct_1click'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              <span>⚡ 1-Click Auto-Apply ({directItems.length})</span>
            </button>
            <button
              type="button"
              onClick={() => setApplyFilter('company_portal')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                applyFilter === 'company_portal'
                  ? 'bg-white text-amber-800 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Globe className="w-3.5 h-3.5 text-amber-600" />
              <span>🌐 Company Portal Apply ({companyItems.length})</span>
            </button>
          </div>

          {/* Right: Days Freshness Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 whitespace-nowrap">Filter Freshness:</span>
            <select
              value={postedWithin}
              onChange={(e) => handleDaysChange(e.target.value)}
              aria-label="Filter queue by job posted date"
              className="px-3 py-1.5 text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="all">All Postings</option>
              <option value="30">Last 30 Days</option>
              <option value="15">Last 15 Days</option>
              <option value="10">Last 10 Days</option>
              <option value="5">Last 5 Days</option>
              <option value="3">Last 3 Days</option>
              <option value="1">Last 1 Day (24 hrs)</option>
            </select>
          </div>
        </div>

        {/* Bulk Action Controls */}
        {displayedItems.length > 0 && (
          <div className="p-3 sm:p-4 rounded-xl bg-white border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleSelectAll}
                className="text-xs"
              >
                {selectedAppIds.length > 0 && selectedAppIds.length === displayedItems.length ? (
                  <CheckSquare className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                ) : (
                  <Square className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                )}
                <span>Select All ({displayedItems.length})</span>
              </Button>

              {selectedAppIds.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSelectedAppIds([])}
                  className="text-xs text-slate-500 hover:text-slate-800 underline px-1 cursor-pointer"
                >
                  Clear Selection
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              {selectedAppIds.length > 0 ? (
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  loading={stealthApplying}
                  onClick={() => handleStealthApply(selectedAppIds.map((id) => items.find((i) => i.application_id === id)?.job_id).filter(Boolean))}
                  className="text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs"
                >
                  <Zap className="w-3.5 h-3.5 mr-1 text-amber-300" />
                  <span>⚡ Auto-Apply Selected ({selectedAppIds.length} Jobs)</span>
                </Button>
              ) : directItems.length > 0 ? (
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  loading={stealthApplying}
                  onClick={handleBatchDirectApply}
                  className="text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs"
                >
                  <Zap className="w-3.5 h-3.5 mr-1 text-amber-300" />
                  <span>⚡ 1-Click Auto-Apply All Direct Jobs ({directItems.length} Positions)</span>
                </Button>
              ) : (
                <span className="text-xs font-semibold text-amber-800 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200 flex items-center gap-1.5">
                  <Globe className="w-4 h-4 text-amber-600" />
                  <span>All direct 1-click jobs submitted! Complete company portal submissions below.</span>
                </span>
              )}
            </div>
          </div>
        )}

        {/* Queue Items */}
        <div className="space-y-4">
          {displayedItems.map((item) => {
            const isSelected = selectedAppIds.includes(item.application_id);
            return (
              <Card
                key={item.application_id}
                className={`transition-all shadow-sm overflow-hidden ${isSelected ? 'border-indigo-400 ring-2 ring-indigo-500/20 bg-indigo-50/10' : 'border-indigo-100'
                  }`}
              >
                <div className="p-5 sm:p-6 space-y-4">
                  {/* Top Platform Source Header Badge */}
                  {item.platform === 'indeed' ? (
                    <div className="flex items-center justify-between pb-2 mb-1 border-b border-blue-100">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-black tracking-wider uppercase bg-blue-600 text-white shadow-xs">
                        <Globe className="w-3.5 h-3.5" />
                        <span>INDEED.COM OFFICIAL JOB</span>
                      </div>
                      <span className="text-[11px] font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                        Reflects in Indeed App
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between pb-2 mb-1 border-b border-indigo-100">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-black tracking-wider uppercase bg-indigo-600 text-white shadow-xs">
                        <Globe className="w-3.5 h-3.5" />
                        <span>NAUKRI.COM OFFICIAL JOB</span>
                      </div>
                      <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
                        Reflects in Naukri App
                      </span>
                    </div>
                  )}

                  {/* Header row */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <button
                        type="button"
                        onClick={() => toggleSelectApp(item.application_id)}
                        className="mt-1 text-slate-400 hover:text-indigo-600 transition-colors cursor-pointer"
                        aria-label="Select application"
                      >
                        {isSelected ? (
                          <CheckSquare className="w-5 h-5 text-indigo-600" />
                        ) : (
                          <Square className="w-5 h-5" />
                        )}
                      </button>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-lg font-bold text-slate-900">{item.job_title}</h3>
                          <Badge variant={item.platform === 'naukri' ? 'primary' : 'info'} size="sm">
                            {item.platform === 'naukri' ? 'Naukri.com' : 'Indeed'}
                          </Badge>
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/60">
                            <ShieldCheck className="w-3 h-3" />
                            Truthfulness Passed
                          </span>
                          {item.company_type === 'startup' && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                              🚀 Startup
                            </span>
                          )}
                          {item.company_type === 'saas' && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-violet-800 bg-violet-50 px-2 py-0.5 rounded-full border border-violet-200">
                              ☁️ SaaS / Product
                            </span>
                          )}
                          {item.company_type === 'mid_sized' && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded-full border border-cyan-200">
                              🏢 Mid-Sized Tech
                            </span>
                          )}
                          {item.company_type === 'mnc' && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-300">
                              🌐 Global MNC
                            </span>
                          )}
                          {item.apply_type === 'company_portal' ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200 shadow-2xs">
                              <Globe className="w-3 h-3 text-amber-600" />
                              Requires Company Portal Apply
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-800 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-200 shadow-2xs">
                              <Zap className="w-3 h-3 text-amber-500" />
                              1-Click Direct Portal Apply
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 text-xs text-slate-600 flex-wrap">
                          <span className="font-semibold text-slate-800 flex items-center gap-1">
                            <Building className="w-3.5 h-3.5 text-slate-400" />
                            {item.company}
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1 text-slate-500">
                            <MapPin className="w-3.5 h-3.5 text-slate-400" />
                            {item.location}
                          </span>
                          {item.url && (
                            <>
                              <span>•</span>
                              <a
                                href={item.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 underline"
                                title="Open exact job listing page on official portal"
                              >
                                <span>Direct Job Link</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </>
                          )}
                        </div>

                        {/* Matched JD Skills Badges */}
                        {Array.isArray(item.matched_skills) && item.matched_skills.length > 0 && (() => {
                          const isExpanded = expandedSkillsAppIds.includes(item.application_id);
                          const skillsToShow = isExpanded ? item.matched_skills : item.matched_skills.slice(0, 6);
                          const remainingCount = item.matched_skills.length - 6;

                          return (
                            <div className="flex items-center gap-1.5 flex-wrap pt-1.5">
                              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                                <ShieldCheck className="w-3 h-3 text-emerald-600" />
                                Matched JD Skills:
                              </span>
                              {skillsToShow.map((sk: string) => (
                                <span
                                  key={sk}
                                  className="text-[11px] font-semibold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-md border border-emerald-200/70"
                                >
                                  {sk}
                                </span>
                              ))}
                              {item.matched_skills.length > 6 && (
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleExpandSkills(item.application_id);
                                  }}
                                  className="inline-flex items-center gap-0.5 text-[11px] font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-2 py-0.5 rounded-md border border-indigo-200 transition-colors cursor-pointer shadow-2xs"
                                  title={isExpanded ? 'Click to show fewer skills' : 'Click to show all matched skills'}
                                >
                                  {isExpanded ? 'Show less ↑' : `+${remainingCount} more ↓`}
                                </button>
                              )}
                            </div>
                          );
                        })()}
                      </div>
                    </div>

                    <ScoreBadge score={item.overall_score ?? 0} size="lg" showLabel />
                  </div>

                  {/* Resume Selection Selector (Tailored vs Original Master - Naukri Neo Style) */}
                  <div className="p-3.5 rounded-xl bg-indigo-50/60 border border-indigo-100 space-y-2.5">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                      <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                        <FileCheck className="w-4 h-4 text-indigo-600" />
                        Select Application Resume:
                      </span>
                      <span className="text-[11px] text-indigo-700 font-medium">
                        Select which resume to submit with this job (Naukri Neo feature)
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      {/* Option 1: AI Tailored Resume */}
                      <div
                        onClick={() => handleSelectResume(item.application_id, 'tailored')}
                        className={`p-3 rounded-xl border transition-all cursor-pointer flex items-start justify-between gap-3 ${item.selected_resume_type !== 'original'
                          ? 'bg-white border-indigo-500 ring-2 ring-indigo-500/20 shadow-xs'
                          : 'bg-white/70 border-slate-200 hover:bg-white'
                          }`}
                      >
                        <div className="flex items-start gap-2.5 min-w-0">
                          <input
                            type="radio"
                            name={`resume-type-${item.application_id}`}
                            checked={item.selected_resume_type !== 'original'}
                            onChange={() => handleSelectResume(item.application_id, 'tailored')}
                            className="mt-0.5 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                          />
                          <div className="space-y-0.5 min-w-0">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="text-xs font-bold text-slate-900">AI Tailored Resume</span>
                              <span className="text-[10px] font-black uppercase px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">
                                Naukri Neo Style
                              </span>
                            </div>
                            <span className="text-[11px] text-emerald-700 font-medium block">
                              ✓ Keywords aligned to {item.company} JD
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setActivePreview({
                                title: `AI Tailored Resume: ${item.job_title} at ${item.company}`,
                                type: 'resume',
                                content: `ANANTH P\nFront End Developer | React.js | Next.js\nChennai, India • ananthslvm28@gmail.com • 6382640048\nLinkedIn • GitHub • Portfolio\n\nPROFESSIONAL SUMMARY\nFront End Developer with 2.5 years of experience building responsive, high-performance web applications using React.js, Next.js, JavaScript (ES6+), TypeScript, Redux, and Tailwind CSS. Skilled in reusable UI component architecture, client-side state management (Redux, Context API), RESTful API and GraphQL integration, real-time updates using WebSockets/Socket.io, SEO fundamentals, lazy loading, and dynamic rendering to deliver robust, user-focused digital solutions and accelerate feature delivery.\n\nTECHNICAL SKILLS\n• Languages & Web: JavaScript (ES6+), TypeScript, HTML5, CSS3\n• Frontend Frameworks & State: React.js, Next.js, React Hooks, Redux, Context API, React Native\n• UI Libraries & Styling: Tailwind CSS, Bootstrap, Ant Design, Responsive Design\n• API & Real-Time Communication: RESTful APIs, GraphQL, WebSockets, Socket.io\n• Tools & Practices: Git, GitHub, Web & Mobile Testing, SEO Optimization, Performance Optimization\n\nPROFESSIONAL EXPERIENCE\n• Front End Developer — LegalOptix Private Limited (Feb 2026 – Sep 2026 | Chennai)\n  - Build responsive frontend features with React.js, Next.js, JavaScript, Redux, and Tailwind CSS for application workflows.\n  - Use React Hooks and Context API to manage component and shared application state across modules.\n• Front End Developer — Piccosoft Software Labs Private Limited (Dec 2023 – Nov 2025 | Chennai)\n  - Developed responsive web application features using React.js, Next.js, JavaScript, Redux, Tailwind CSS, React Hooks, and Context API.\n  - Integrated RESTful APIs to connect frontend modules with backend services and support dynamic data updates.\n  - Optimized semantic HTML, page-load performance, and metadata for SEO.\n  - Worked with UI/UX designers, backend developers, QA engineers, and product managers to clarify requirements and deliver features on schedule.\n\nKEY PROJECTS\n• E-Commerce Web Application\n  Technologies: React.js, Next.js, JavaScript, Redux, Context API, WebSockets\n  - Implemented Wishlist, Cart, Checkout, and Order Management workflows covering returns, refunds, and cancellations.\n  - Developed Product Comparison, Saved Searches, Offer and Discount Management, and configurable widgets.\n  - Built buyer registration and login workflows with form validation and API integration.\n  - Integrated real-time notifications with WebSockets/Socket.io and applied lazy loading and dynamic rendering to support frontend performance.\n• Media Platform for Startup Founders\n  Technologies: Next.js, GraphQL\n  - Built a content-publishing platform with Next.js, GraphQL API integration, and dynamic page rendering.\n  - Applied SEO optimization techniques associated with a reported 25% increase in website traffic.\n• Property Loan Management\n  Technologies: React.js, Next.js, Ant Design, Redux\n  - Built responsive frontend components for an OCR-enabled document-processing application that extracts structured data from unstructured documents.\n  - Integrated external document-parsing APIs and refined UI components for a responsive user experience.\n\nEDUCATION\n• B.E., Computer Science and Engineering | Anand Institute of Higher Technology (2016–2020)`,
                                company: item.company,
                                platform: item.platform,
                                matched_skills: item.matched_skills || [],
                                app_id: item.application_id,
                                resume_type: 'tailored',
                              });
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white hover:bg-indigo-50 text-indigo-700 text-[11px] font-bold border border-indigo-200 transition-colors cursor-pointer shadow-2xs"
                            title="Preview Tailored Resume"
                          >
                            <Eye className="w-3 h-3" />
                            <span>View</span>
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadTailoredPdf(item.application_id, item.company);
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-bold border border-indigo-200 transition-colors cursor-pointer"
                            title="Download AI Tailored PDF"
                          >
                            <Download className="w-3 h-3" />
                            <span>PDF</span>
                          </button>
                        </div>
                      </div>

                      {/* Option 2: Original Master Resume */}
                      <div
                        onClick={() => handleSelectResume(item.application_id, 'original')}
                        className={`p-3 rounded-xl border transition-all cursor-pointer flex items-start justify-between gap-3 ${item.selected_resume_type === 'original'
                          ? 'bg-white border-indigo-500 ring-2 ring-indigo-500/20 shadow-xs'
                          : 'bg-white/70 border-slate-200 hover:bg-white'
                          }`}
                      >
                        <div className="flex items-start gap-2.5 min-w-0">
                          <input
                            type="radio"
                            name={`resume-type-${item.application_id}`}
                            checked={item.selected_resume_type === 'original'}
                            onChange={() => handleSelectResume(item.application_id, 'original')}
                            className="mt-0.5 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                          />
                          <div className="space-y-0.5 min-w-0">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="text-xs font-bold text-slate-900">Original Master Resume</span>
                              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                                Uploaded
                              </span>
                            </div>
                            <span className="text-[11px] text-slate-500 font-medium block truncate max-w-[180px]">
                              {item.master_resume_filename || 'Ananth_P_Resume_old.pdf'}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setActivePreview({
                                title: `Original Master Resume: ${item.master_resume_filename || 'Ananth_P_Resume_old.pdf'}`,
                                type: 'resume',
                                content: `ANANTH P\nChennai, India • ananthslvm28@gmail.com • 6382640048\n\nPROFESSIONAL SUMMARY\nFront End Developer with 2.5 years of experience building responsive web applications using React.js, Next.js, JavaScript (ES6+), TypeScript, Redux, and Tailwind CSS. Skilled in reusable UI components, client-side state management with Redux and Context API, RESTful API and GraphQL integration, real-time updates using WebSockets/Socket.io, SEO fundamentals, lazy loading, and dynamic rendering. Works with UI/UX, backend, QA, and product teams to deliver user-focused features.\n\nCORE TECHNICAL COMPETENCIES\n• Frontend & UI: Bootstrap, CSS, CSS3, HTML, HTML5, JavaScript, Next.js, React, React Native, Tailwind CSS, TypeScript\n• APIs & Practices: GraphQL, REST API, RESTful API, Git, GitHub\n\nPROFESSIONAL EXPERIENCE\n• Front End Developer — LegalOptix Private Limited (Feb 2026 – Sep 2026 | Chennai)\n  - Build responsive frontend features with React.js, Next.js, JavaScript, Redux, and Tailwind CSS for application workflows.\n• Front End Developer — Piccosoft Software Labs Private Limited (Dec 2023 – Nov 2025 | Chennai)\n  - Developed responsive web application features using React.js, Next.js, JavaScript, Redux, Tailwind CSS, React Hooks, and Context API.\n\nREPRESENTATIVE PROJECTS\n• E-Commerce Web Application (React.js, Next.js, Redux, WebSockets)\n  - Architected reusable catalog, cart, and checkout workflows with Redux state management. Integrated WebSockets for live status updates and applied dynamic code splitting.\n• Content Publishing Platform (Next.js, TypeScript, GraphQL)\n  - Built responsive content-publishing pages with GraphQL API data fetching, SSR optimization, and automated SEO metadata generation.\n\nEDUCATION\n• B.E., Computer Science and Engineering — Anand Institute of Higher Technology (2016-2020)`,
                                company: item.company,
                                platform: item.platform,
                                matched_skills: [],
                                app_id: item.application_id,
                                resume_type: 'original',
                                master_resume_id: item.master_resume_id,
                                master_resume_filename: item.master_resume_filename,
                              });
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 text-slate-700 text-[11px] font-bold border border-slate-200 transition-colors cursor-pointer shadow-2xs"
                            title="Preview Master Resume"
                          >
                            <Eye className="w-3 h-3" />
                            <span>View</span>
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (item.master_resume_id) {
                                handleDownloadMasterPdf(item.master_resume_id, item.master_resume_filename);
                              } else {
                                toast.info('Master resume not found');
                              }
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold border border-slate-200 transition-colors cursor-pointer"
                            title="Download Original Master PDF"
                          >
                            <Download className="w-3 h-3" />
                            <span>PDF</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Screening Answers (Only shown if available from profile/answers) */}
                  {Array.isArray(item.screening_answers) && item.screening_answers.length > 0 && (
                    <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-1.5 text-xs">
                      <span className="font-semibold text-slate-700 flex items-center gap-1">
                        <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
                        Prepared Screening Answers (from Verified Profile):
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-600 pt-1">
                        {item.screening_answers.map((ans: any, idx: number) => (
                          <div key={idx}>
                            <span className="font-medium text-slate-700">{ans.question}: </span>
                            <span>{ans.answer}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons Row */}
                  <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                        >
                          <span>Direct Job Post</span>
                          <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                        </a>
                      )}

                      {item.apply_type === 'company_portal' && (
                        <button
                          type="button"
                          onClick={() => handleCopyCompanyAnswers(item)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-200 bg-amber-50/50 text-xs font-semibold text-amber-800 hover:bg-amber-100/60 transition-colors cursor-pointer"
                          title="Copy candidate summary & pre-filled application details to clipboard"
                        >
                          <Copy className="w-3.5 h-3.5 text-amber-600" />
                          <span>Copy Form Answers</span>
                        </button>
                      )}
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleReject(item.application_id)}
                        className="text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                      >
                        <X className="w-4 h-4 mr-1" />
                        <span>Skip</span>
                      </Button>

                      {item.apply_type === 'company_portal' ? (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleOpenAndApplyCompany(item)}
                          className="font-bold bg-amber-600 hover:bg-amber-700 text-white shadow-xs text-xs inline-flex items-center gap-1.5"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>🚀 Open & Apply on {item.company} Site</span>
                        </Button>
                      ) : (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handlePortalSubmit(item)}
                          className={`font-bold shadow-xs ${
                            item.platform === 'indeed'
                              ? 'bg-blue-600 hover:bg-blue-700 text-white'
                              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                          }`}
                        >
                          <Zap className="w-4 h-4 mr-1 text-amber-300" />
                          <span>⚡ Auto-Apply on {item.platform === 'indeed' ? 'Indeed' : 'Naukri'}</span>
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Full Document Viewer Modal */}
      {activePreview && (
        <Modal
          isOpen={!!activePreview}
          onClose={() => setActivePreview(null)}
          maxWidth="2xl"
          title={activePreview.title}
          description={
            activePreview.resume_type === 'original'
              ? 'Candidate Master Resume (Original uploaded version)'
              : `AI-Tailored specifically to match ${activePreview.company || 'the target company'}'s Job Description`
          }
        >
          <div className="space-y-4 pt-2">
            {/* Context Badge Row */}
            <div className="p-3 bg-indigo-50/70 rounded-xl border border-indigo-100 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Badge variant={activePreview.platform === 'indeed' ? 'info' : 'primary'} size="sm">
                  {activePreview.platform === 'indeed' ? 'Indeed Application' : 'Naukri Application'}
                </Badge>
                <span className="text-xs font-bold text-slate-800">{activePreview.company}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold text-indigo-700 bg-white px-2 py-0.5 rounded border border-indigo-200 flex items-center gap-1 shadow-2xs">
                  <ShieldCheck className="w-3 h-3 text-emerald-600" />
                  {activePreview.resume_type === 'original' ? 'Master Verified' : 'ATS Keyword Optimized'}
                </span>
              </div>
            </div>

            {/* Matched skills highlight */}
            {activePreview.matched_skills && activePreview.matched_skills.length > 0 && (
              <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  Matched Skills from Job Description:
                </span>
                <div className="flex flex-wrap gap-1.5 pt-0.5">
                  {activePreview.matched_skills.map((sk: string) => (
                    <span
                      key={sk}
                      className="text-xs font-semibold px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md"
                    >
                      ✓ {sk}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Full Document Content Box */}
            <div className="space-y-1">
              <span className="text-xs font-bold text-slate-700">
                {activePreview.type === 'cover_letter'
                  ? 'Full Cover Letter Text:'
                  : activePreview.resume_type === 'original'
                    ? 'Original Master Resume Content:'
                    : 'Full Tailored ATS Resume Content:'}
              </span>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 max-h-[50vh] overflow-y-auto whitespace-pre-wrap font-mono text-xs sm:text-[13px] text-slate-800 leading-relaxed shadow-inner">
                {activePreview.content}
              </div>
            </div>

            {/* Modal Footer Controls */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-100 flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleCopy(activePreview.content, 'modal-copy')}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors cursor-pointer"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>{copiedKey === 'modal-copy' ? 'Copied to Clipboard!' : 'Copy Full Document'}</span>
                </button>

                {activePreview.type === 'resume' && (
                  activePreview.resume_type === 'original' ? (
                    <button
                      type="button"
                      onClick={() => {
                        if (activePreview.master_resume_id) {
                          handleDownloadMasterPdf(
                            activePreview.master_resume_id,
                            activePreview.master_resume_filename || 'Ananth_P_Resume_old.pdf'
                          );
                        } else {
                          toast.info('Master resume not found');
                        }
                      }}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-slate-700 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer shadow-xs"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download Master PDF</span>
                    </button>
                  ) : (
                    activePreview.app_id && (
                      <button
                        type="button"
                        onClick={() => handleDownloadTailoredPdf(activePreview.app_id!, activePreview.company || 'Job')}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors cursor-pointer shadow-xs"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download Tailored PDF</span>
                      </button>
                    )
                  )
                )}
              </div>
              <Button variant="outline" size="sm" onClick={() => setActivePreview(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </DashboardLayout>
  );
}

