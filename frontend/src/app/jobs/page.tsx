'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Search,
  Filter,
  Building,
  MapPin,
  ExternalLink,
  Sparkles,
  ArrowRight,
  Briefcase,
  Check,
  CheckSquare,
  Square,
  Zap,
  Send,
  Layers,
  Globe,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { API_BASE_URL } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScoreBadge } from '@/components/ui/score-badge';
import { formatSalary } from '@/lib/utils';
import { toast } from 'sonner';

export default function JobsPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [platform, setPlatform] = useState('all');
  const [workMode, setWorkMode] = useState('all');
  const [companyType, setCompanyType] = useState('all');
  const [postedWithin, setPostedWithin] = useState('30');
  const [loading, setLoading] = useState(true);

  const [selectedJobIds, setSelectedJobIds] = useState<number[]>([]);
  const [bulkApplying, setBulkApplying] = useState(false);
  const [bulkQueuing, setBulkQueuing] = useState(false);
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [profile, setProfile] = useState<any>(null);

  useEffect(() => {
    async function loadUserData() {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      try {
        const prefRes = await fetch(`${API_BASE_URL}/preferences/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (prefRes.ok) {
          const data = await prefRes.json();
          if (data && data.posted_within_days !== null && data.posted_within_days !== undefined) {
            setPostedWithin(String(data.posted_within_days));
          }
        }
      } catch {
        // Keep default 30
      }

      try {
        const profRes = await fetch(`${API_BASE_URL}/profile/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (profRes.ok) {
          const profData = await profRes.json();
          setProfile(profData);
        }
      } catch {
        // ignore
      }
    }
    loadUserData();
  }, []);

  useEffect(() => {
    async function fetchJobs() {
      setLoading(true);
      try {
        let url = `${API_BASE_URL}/jobs/?size=50`;
        if (platform !== 'all') url += `&platform=${platform}`;
        if (workMode !== 'all') url += `&work_mode=${workMode}`;
        if (companyType !== 'all') url += `&company_type=${companyType}`;
        if (postedWithin !== 'all') url += `&posted_within_days=${postedWithin}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        const res = await fetch(url, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          setJobs(data.items || []);
        } else {
          setJobs([]);
        }
      } catch {
        setJobs([]);
      } finally {
        setLoading(false);
      }
    }

    const timer = setTimeout(fetchJobs, 200);
    return () => clearTimeout(timer);
  }, [search, platform, workMode, companyType, postedWithin]);

  const toggleSelectJob = (id: number) => {
    setSelectedJobIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    const unapplied = jobs.filter((j) => !j.is_applied).map((j) => j.id);
    if (selectedJobIds.length === unapplied.length && unapplied.length > 0) {
      setSelectedJobIds([]);
    } else {
      setSelectedJobIds(unapplied);
    }
  };

  const handleSelectHighMatches = () => {
    const highMatches = jobs
      .filter((j) => !j.is_applied && (j.match_score || 0) >= 80)
      .map((j) => j.id);
    setSelectedJobIds(highMatches);
    if (highMatches.length > 0) {
      toast.info(`Selected ${highMatches.length} high-fit positions (>80% match)`);
    } else {
      toast.info('No unapplied jobs with >80% match found');
    }
  };

  const handleQueueJobs = async (jobIds: number[]) => {
    if (jobIds.length === 0) return;
    setBulkQueuing(true);
    toast.loading(`Tailoring documents for ${jobIds.length} job(s)...`, { id: 'queue-jobs' });
    try {
      const res = await fetch(`${API_BASE_URL}/applications/bulk-apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({ job_ids: jobIds, auto_approve: false }),
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(`Tailored ${data.applied_count || jobIds.length} positions and queued for review!`, {
          id: 'queue-jobs',
        });
        setSelectedJobIds([]);
        setTimeout(() => {
          router.push('/approval-queue');
        }, 800);
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Failed to queue applications', { id: 'queue-jobs' });
      }
    } catch {
      toast.error('Network error tailoring applications', { id: 'queue-jobs' });
    } finally {
      setBulkQueuing(false);
    }
  };

  const handleApplyOnPortal = async (job: any) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const platformName = job.platform === 'indeed' ? 'Indeed' : 'Naukri';
    setApplyingJobId(job.id);
    toast.info(`Opening ${platformName} portal in your logged-in Chrome session...`, { duration: 4000 });

    try {
      const res = await fetch(`${API_BASE_URL}/browser/open-portal-apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          job_id: job.id,
          platform: job.platform,
          url: job.url,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        toast.info(
          data.message || `Opened on ${platformName}! Complete application in the browser window to register in your official account.`,
          { duration: 8000 }
        );
      } else {
        window.open(job.url, '_blank');
        toast.info(`Opened ${job.title} directly in browser tab.`);
      }
    } catch {
      window.open(job.url, '_blank');
    } finally {
      setApplyingJobId(null);
    }
  };

  const handleApplyJobs = async (jobIds: number[]) => {
    if (jobIds.length === 0) return;
    if (jobIds.length === 1) {
      const targetJob = jobs.find((j) => j.id === jobIds[0]);
      if (targetJob) {
        return handleApplyOnPortal(targetJob);
      }
    }

    setBulkApplying(true);
    toast.loading(`Launching browser automation for ${jobIds.length} job(s)...`, { id: 'apply-jobs' });
    try {
      const res = await fetch(`${API_BASE_URL}/browser/apply-stealth`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify({ job_ids: jobIds }),
      });

      if (res.ok) {
        const data = await res.json();
        const confirmedJobIds = (data.results || [])
          .filter((r: any) => r.status === 'applied' || r.status === 'already_applied')
          .map((r: any) => r.job_id);
        const companyPortalJobs = (data.results || []).filter((r: any) => r.status === 'company_site_redirect');

        if (confirmedJobIds.length > 0) {
          toast.success(`Successfully applied to ${confirmedJobIds.length} position(s) on portal! Reflected in your official accounts.`, {
            id: 'apply-jobs',
            duration: 6000,
          });
          setJobs((prev) =>
            prev.map((j) => (confirmedJobIds.includes(j.id) ? { ...j, is_applied: true } : j))
          );
          setSelectedJobIds((prev) => prev.filter((id) => !confirmedJobIds.includes(id)));
        } else if (companyPortalJobs.length > 0) {
          toast.info(`${companyPortalJobs.length} position(s) require applying on employer website. Check Approval Queue for direct links.`, {
            id: 'apply-jobs',
            duration: 7000,
          });
        } else {
          toast.info(`Automated check completed. Status updated in Tracker.`, { id: 'apply-jobs' });
        }
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Failed to submit applications', { id: 'apply-jobs' });
      }
    } catch {
      toast.error('Network error during application submission', { id: 'apply-jobs' });
    } finally {
      setBulkApplying(false);
      setApplyingJobId(null);
    }
  };

  const unappliedCount = jobs.filter((j) => !j.is_applied).length;
  const highFitCount = jobs.filter((j) => !j.is_applied && (j.match_score || 0) >= 80).length;

  return (
    <DashboardLayout title="Job Discovery & AI Matches">
      <div className="space-y-5">
        {/* Domain Personalization & Onboarding Banner */}
        {profile && (!profile.skills || profile.skills.length === 0) && (
          <div className="bg-gradient-to-r from-amber-500/10 via-indigo-500/10 to-transparent p-4 rounded-2xl border border-amber-200/80 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">📄</span>
              <div>
                <p className="text-xs font-bold text-slate-900">
                  Step 1: Upload Your Resume First
                </p>
                <p className="text-[11px] text-slate-600 mt-0.5">
                  Upload your master resume in <strong>Resume & Profile</strong> so your skills across any domain are parsed dynamically. Then run the bot to fetch jobs tailored specifically for you.
                </p>
              </div>
            </div>
            <Link
              href="/resume"
              className="text-xs font-semibold px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-colors whitespace-nowrap shadow-xs"
            >
              Upload Resume →
            </Link>
          </div>
        )}

        {profile && profile.skills && profile.skills.length > 0 && jobs.length === 0 && (
          <div className="bg-gradient-to-r from-indigo-50/80 via-emerald-50/50 to-white p-4 rounded-2xl border border-indigo-100 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🤖</span>
              <div>
                <p className="text-xs font-bold text-slate-900">
                  Step 2: Trigger Bot Search to Fetch Jobs
                </p>
                <p className="text-[11px] text-slate-600 mt-0.5">
                  Your profile has <strong>{profile.skills.length} verified skills</strong>. Go to <strong>Bot Controls</strong> and click <strong>Run Bot Now</strong> to search and score live positions matching your career!
                </p>
              </div>
            </div>
            <Link
              href="/bot-controls"
              className="text-xs font-semibold px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition-colors whitespace-nowrap shadow-xs"
            >
              Run Bot Now →
            </Link>
          </div>
        )}

        {profile && profile.skills && profile.skills.length > 0 && jobs.length > 0 && (
          <div className="bg-gradient-to-r from-indigo-50/80 via-emerald-50/50 to-white p-3.5 rounded-2xl border border-indigo-100 flex items-center justify-between gap-3 text-xs text-indigo-950">
            <div className="flex items-center gap-2.5">
              <Sparkles className="w-4 h-4 text-indigo-600 shrink-0" />
              <span>
                Showing <strong>{jobs.length} positions</strong> discovered by your bot for <strong>{profile.full_name || 'Candidate'}</strong> — ordered by AI fit score.
              </span>
            </div>
            <Link href="/bot-controls" className="text-[11px] text-indigo-600 hover:underline font-semibold whitespace-nowrap">
              Bot Controls
            </Link>
          </div>
        )}

        {/* Filter Toolbar */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3 sm:space-y-0 sm:flex sm:items-center sm:gap-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by role, company or skill keyword..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 focus:bg-white transition-all"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              aria-label="Filter by Job Platform"
              className="px-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="all">All Platforms</option>
              <option value="naukri">Naukri.com</option>
              <option value="indeed">Indeed.com</option>
            </select>

            <select
              value={workMode}
              onChange={(e) => setWorkMode(e.target.value)}
              aria-label="Filter by Work Mode"
              className="px-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="all">All Modes</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">Onsite</option>
            </select>

            <select
              value={companyType}
              onChange={(e) => setCompanyType(e.target.value)}
              aria-label="Filter by Company Type"
              className="px-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="all">All Companies</option>
              <option value="startup">🚀 Startups (High Fit)</option>
              <option value="saas">☁️ SaaS / Product</option>
              <option value="mid_sized">🏢 Mid-Sized Tech</option>
              <option value="mnc">🌐 Global MNCs</option>
            </select>

            <select
              value={postedWithin}
              onChange={(e) => setPostedWithin(e.target.value)}
              aria-label="Filter by Job Freshness / Posted Date"
              className="px-3 py-2 text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
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

        {/* Bulk Action & Multi-Selection Bar */}
        {jobs.length > 0 && (
          <div className="p-3 sm:p-4 rounded-xl bg-white border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2 flex-wrap">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleSelectAll}
                className="text-xs"
              >
                {selectedJobIds.length > 0 && selectedJobIds.length === unappliedCount ? (
                  <CheckSquare className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                ) : (
                  <Square className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                )}
                <span>Select All Unapplied ({unappliedCount})</span>
              </Button>

              {highFitCount > 0 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleSelectHighMatches}
                  className="text-xs border-emerald-200 text-emerald-800 hover:bg-emerald-50"
                >
                  <Sparkles className="w-3.5 h-3.5 mr-1.5 text-emerald-600" />
                  <span>Select Prime Fits &gt;80% ({highFitCount})</span>
                </Button>
              )}

              {selectedJobIds.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSelectedJobIds([])}
                  className="text-xs text-slate-500 hover:text-slate-800 underline px-1 cursor-pointer"
                >
                  Clear Selection
                </button>
              )}
            </div>

            {selectedJobIds.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  loading={bulkQueuing}
                  onClick={() => handleQueueJobs(selectedJobIds)}
                  className="cursor-pointer border-indigo-200 text-indigo-700 hover:bg-indigo-50 text-xs font-semibold"
                >
                  <Sparkles className="w-3.5 h-3.5 mr-1 text-indigo-600" />
                  <span>Tailor & Add to Queue ({selectedJobIds.length})</span>
                </Button>

                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  loading={bulkApplying}
                  onClick={() => handleApplyJobs(selectedJobIds)}
                  className="cursor-pointer shadow-sm text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  <Zap className="w-3.5 h-3.5 mr-1 text-amber-300" />
                  <span>Bulk Apply Directly ({selectedJobIds.length})</span>
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Results Count & Match Guide */}
        <div className="flex items-center justify-between text-xs text-slate-500 px-1">
          <p>
            Showing <span className="font-bold text-slate-800">{jobs.length}</span> positions ranked by resume similarity
            {selectedJobIds.length > 0 && (
              <span className="ml-2 font-semibold text-indigo-600">({selectedJobIds.length} selected)</span>
            )}
          </p>
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>&gt;85% Prime Fit</span>
            <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 ml-2"></span>
            <span>70-85% Strong Fit</span>
          </div>
        </div>

        {/* Jobs Grid */}
        {jobs.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
              <Briefcase className="w-6 h-6" />
            </div>
            <div className="max-w-md mx-auto space-y-1">
              <h3 className="font-bold text-slate-800 text-base">No Jobs Ingested Yet</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Your database is completely fresh. Upload your resume in Profile and trigger a job ingestion run in Bot Controls to fetch relevant opportunities from Naukri & Indeed.
              </p>
            </div>
            <div className="flex items-center justify-center gap-3 pt-2">
              <Link href="/profile">
                <Button variant="outline" size="sm">
                  Upload Resume
                </Button>
              </Link>
              <Link href="/bot-controls">
                <Button variant="primary" size="sm">
                  <Sparkles className="w-4 h-4 mr-1.5" />
                  Run Bot Now
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {jobs.map((job) => {
              const isSelected = selectedJobIds.includes(job.id);
              return (
                <Card
                  key={job.id}
                  hover
                  className={`flex flex-col justify-between p-5 transition-all ${
                    isSelected ? 'ring-2 ring-indigo-500 bg-indigo-50/20 border-indigo-300' : 'border-slate-200/90'
                  }`}
                >
                  <div className="space-y-3">
                    {/* Top Platform Source Header Badge */}
                    {job.platform === 'indeed' ? (
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

                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-2.5">
                        {!job.is_applied && (
                          <button
                            type="button"
                            onClick={() => toggleSelectJob(job.id)}
                            className="mt-0.5 text-slate-400 hover:text-indigo-600 transition-colors cursor-pointer"
                            aria-label={`Select ${job.title}`}
                          >
                            {isSelected ? (
                              <CheckSquare className="w-4 h-4 text-indigo-600" />
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                          </button>
                        )}
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Link
                              href={`/jobs/${job.id}`}
                              className="font-bold text-base text-slate-900 hover:text-indigo-600 transition-colors line-clamp-1"
                            >
                              {job.title}
                            </Link>
                            {job.company_type === 'startup' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                                🚀 Startup
                              </span>
                            )}
                            {job.company_type === 'saas' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-violet-800 bg-violet-50 px-2 py-0.5 rounded-full border border-violet-200">
                                ☁️ SaaS
                              </span>
                            )}
                            {job.company_type === 'mid_sized' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded-full border border-cyan-200">
                                🏢 Mid-Sized
                              </span>
                            )}
                            {job.company_type === 'mnc' && (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-300">
                                🌐 MNC
                              </span>
                            )}
                            {job.apply_type === 'company_portal' ? (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                                <Globe className="w-3 h-3 text-amber-600" />
                                Company Portal
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-indigo-800 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
                                <Zap className="w-3 h-3 text-amber-500" />
                                1-Click Direct
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-slate-600 flex-wrap">
                            <span className="font-semibold text-slate-800 flex items-center gap-1">
                              <Building className="w-3.5 h-3.5 text-slate-400" />
                              {job.company}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1 text-slate-500">
                              <MapPin className="w-3.5 h-3.5 text-slate-400" />
                              {job.location}
                            </span>
                            {job.url && (
                              <>
                                <span>•</span>
                                <a
                                  href={job.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 underline"
                                  title="Open direct job posting on official portal"
                                >
                                  <span>Direct Job Link</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col items-end gap-1 shrink-0">
                        {job.match_score !== undefined && job.match_score !== null && (
                          <ScoreBadge score={job.match_score} showLabel />
                        )}
                        {job.is_applied && (
                          <Badge variant="success" size="sm" className="text-[10px]">
                            <Check className="w-3 h-3 mr-1" />
                            Applied
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant={job.platform === 'naukri' ? 'primary' : 'info'} size="sm">
                        {job.platform === 'naukri' ? 'Naukri.com' : 'Indeed'}
                      </Badge>
                      <Badge variant="outline" size="sm" className="capitalize">
                        {job.work_mode || 'Flexible'}
                      </Badge>
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/60">
                        {formatSalary(job.salary_min, job.salary_max, 'INR')}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                      {job.description}
                    </p>

                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      {(job.skills_required || []).map((s: string) => (
                        <span
                          key={s}
                          className="text-[11px] font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between gap-3 flex-wrap">
                    <span className="text-[11px] text-slate-400">Direct Portal Integration</span>
                    <div className="flex items-center gap-2 flex-wrap">
                      {!job.is_applied ? (
                        job.apply_type === 'company_portal' ? (
                          <a
                            href={job.company_url || job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white shadow-xs transition-colors"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                            <span>Apply on Company Site</span>
                          </a>
                        ) : (
                          <Button
                            variant="primary"
                            size="sm"
                            loading={applyingJobId === job.id}
                            onClick={() => handleApplyOnPortal(job)}
                            className={`text-xs font-semibold cursor-pointer shadow-xs ${
                              job.platform === 'indeed'
                                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                            }`}
                          >
                            <Zap className="w-3.5 h-3.5 mr-1 text-amber-300" />
                            <span>⚡ Auto-Apply on {job.platform === 'indeed' ? 'Indeed' : 'Naukri'}</span>
                          </Button>
                        )
                      ) : (
                        <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          Applied on Portal
                        </span>
                      )}

                      <Link href={`/jobs/${job.id}`}>
                        <Button variant="outline" size="sm" className="text-xs cursor-pointer">
                          <span>Inspect</span>
                          <ArrowRight className="w-3.5 h-3.5 ml-1" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

