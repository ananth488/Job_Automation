'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Briefcase,
  Send,
  Calendar,
  Clock,
  Sparkles,
  ArrowUpRight,
  Play,
  Upload,
  CheckCircle,
  Building,
  MapPin,
  TrendingUp,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { StatCard } from '@/components/ui/stat-card';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScoreBadge } from '@/components/ui/score-badge';
import { Badge } from '@/components/ui/badge';
import { formatSalary } from '@/lib/utils';
import { API_BASE_URL } from '@/lib/api';
import { useAuth } from '@/lib/use-auth';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    total_jobs: 0,
    total_matches: 0,
    total_applications: 0,
    pending_approval: 0,
    applied: 0,
    hr_shortlisted: 0,
    interviews: 0,
    offers: 0,
    rejected: 0,
    avg_match_score: 0,
    new_jobs_today: 0,
  });

  const [candidateProfile, setCandidateProfile] = useState<any>(null);
  const [targetRoles, setTargetRoles] = useState<string[]>([]);
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [preferences, setPreferences] = useState({
    daily_limit: 20,
    match_threshold: 75,
    approval_mode: 'below_threshold',
    work_mode: 'any',
  });
  const [botStatus, setBotStatus] = useState({
    is_running: false,
    status: 'Ready',
    schedule: 'Every 6 Hours',
  });
  const [platformAccounts, setPlatformAccounts] = useState<{
    naukri: { connected: boolean; email?: string | null };
    indeed: { connected: boolean; email?: string | null };
  }>({
    naukri: { connected: false, email: null },
    indeed: { connected: false, email: null },
  });

  const loadData = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token') || '';
      const [statsRes, jobsRes, prefRes, botRes, sessionRes, profileRes] = await Promise.all([
        fetch(`${API_BASE_URL}/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/jobs/?size=5`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/preferences/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/bot/status`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/browser/session-status`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/profile/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
      if (profileRes.ok) {
        const profData = await profileRes.json();
        setCandidateProfile(profData);
      }
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setRecentJobs(jobsData.items || []);
      }
      if (prefRes.ok) {
        const prefData = await prefRes.json();
        if (prefData) {
          setPreferences({
            daily_limit: prefData.daily_limit !== null && prefData.daily_limit !== undefined ? prefData.daily_limit : 20,
            match_threshold: prefData.match_threshold !== null && prefData.match_threshold !== undefined ? prefData.match_threshold : 75,
            approval_mode: prefData.approval_mode || 'below_threshold',
            work_mode: prefData.work_mode || 'any',
          });
          if (prefData.desired_roles && prefData.desired_roles.length > 0) {
            setTargetRoles(prefData.desired_roles);
          }
        }
      }
      if (botRes.ok) {
        const botData = await botRes.json();
        setBotStatus((prev) => ({
          ...prev,
          is_running: Boolean(botData.is_running),
          status: botData.status === 'active' || botData.status === 'running' ? 'Active' : botData.status === 'executing' ? 'Executing...' : botData.status === 'paused' ? 'Paused' : 'Ready',
        }));
      }
      if (sessionRes && sessionRes.ok) {
        const sessionData = await sessionRes.json();
        setPlatformAccounts({
          naukri: {
            connected: Boolean(sessionData.naukri?.logged_in),
            email: sessionData.naukri?.email || null,
          },
          indeed: {
            connected: Boolean(sessionData.indeed?.logged_in),
            email: sessionData.indeed?.email || null,
          },
        });
      }
    } catch {
      // Leave empty if offline or error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    const handlePrefUpdate = () => {
      loadData();
    };
    window.addEventListener('preferences-updated', handlePrefUpdate);
    window.addEventListener('focus', handlePrefUpdate);

    return () => {
      window.removeEventListener('preferences-updated', handlePrefUpdate);
      window.removeEventListener('focus', handlePrefUpdate);
    };
  }, [loadData]);

  return (
    <DashboardLayout title="Overview Dashboard">
      <div className="space-y-6">
        {/* Banner with Candidate Info & Verification Status */}
        <div className="pt-7 pb-6 px-6 sm:px-8 rounded-2xl bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 text-white shadow-xl relative overflow-hidden">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/30 border border-indigo-400/40 text-indigo-200 text-xs font-medium mb-3">
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI Job Search Engine Active</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-black tracking-tight">
                Welcome back, {user?.full_name || 'Candidate'}
              </h1>
              <p className="text-sm text-indigo-200/90 mt-1.5 max-w-xl">
                {targetRoles.length > 0 ? (
                  <>
                    Your bot is targeted for <span className="font-semibold text-white">{targetRoles.join(', ')}</span> roles based on your verified skills.
                  </>
                ) : candidateProfile?.is_verified || (candidateProfile?.skills && candidateProfile.skills.length > 0) ? (
                  <>
                    Your profile is verified. The AI Job Search Engine is actively monitoring Naukri & Indeed for high-match roles.
                  </>
                ) : (
                  <>Upload your master resume in profile or configure target roles in preferences to begin matching.</>
                )}
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <Link href="/profile">
                <Button variant="outline" className="bg-white/10 text-white border-white/20 hover:bg-white/20">
                  <Upload className="w-4 h-4 mr-1.5" />
                  <span>Update Resume</span>
                </Button>
              </Link>
              <Link href="/approval-queue">
                <Button className="bg-white text-indigo-900 hover:bg-indigo-50 font-semibold shadow-md">
                  <span>Review Approval Queue ({stats.pending_approval})</span>
                  <ArrowUpRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </div>
          </div>
          <div className="absolute -right-8 -bottom-8 w-48 h-48 bg-indigo-500/10 rounded-full blur-2xl"></div>
        </div>

        {/* 6 KPI Counters in Logical Recruitment Lifecycle: Discovered -> AI Matched -> Pending Review -> Applications Sent -> HR Shortlisted -> Interviews */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <StatCard
            title="Jobs Discovered"
            value={stats.total_jobs}
            subtitle="Naukri & Indeed"
            icon={<Briefcase className="w-4 h-4" />}
            color="indigo"
            trend={stats.total_jobs > 0 ? { value: `+${stats.new_jobs_today || stats.total_jobs} new`, label: "scanned", isPositive: true } : undefined}
          />
          <StatCard
            title="AI Matched"
            value={stats.total_matches}
            subtitle="Best fit ≥ 75%"
            icon={<Sparkles className="w-4 h-4" />}
            color="sky"
            trend={stats.total_matches > 0 ? { value: `${stats.avg_match_score || 85}% avg`, label: "fit score", isPositive: true } : undefined}
          />
          <StatCard
            title="Pending Review"
            value={stats.pending_approval}
            subtitle="In approval queue"
            icon={<Clock className="w-4 h-4" />}
            color="amber"
            trend={stats.pending_approval > 0 ? { value: `Cap: ${preferences.daily_limit}`, label: "daily limit", isPositive: true } : undefined}
          />
          <StatCard
            title="Applications Sent"
            value={stats.applied || 0}
            subtitle={stats.applied > 0 ? "Submitted to portals" : "Awaiting approval"}
            icon={<Send className="w-4 h-4" />}
            color="emerald"
            trend={stats.applied > 0 ? { value: `${stats.applied} sent`, label: "official total", isPositive: true } : undefined}
          />
          <StatCard
            title="HR Shortlisted"
            value={stats.hr_shortlisted || 0}
            subtitle="Recruiter shortlist"
            icon={<CheckCircle className="w-4 h-4" />}
            color="purple"
            trend={stats.hr_shortlisted > 0 ? { value: `${stats.hr_shortlisted} selected`, label: "by employers", isPositive: true } : undefined}
          />
          <StatCard
            title="Interviews"
            value={(stats.interviews || 0) + (stats.offers || 0)}
            subtitle="Calls & offers"
            icon={<Calendar className="w-4 h-4" />}
            color="rose"
          />
        </div>

        {/* High-Score Matched Jobs & Quick Status */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Column: Top Matched Opportunities */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>
                    {candidateProfile?.is_verified ? 'Top AI-Matched Opportunities' : 'Discovered Market Opportunities (50 Jobs)'}
                  </CardTitle>
                  <p className="text-xs text-slate-500">
                    {candidateProfile?.is_verified
                      ? 'Sorted by relevance to your verified resume profile'
                      : 'Live market vacancies discovered from Naukri & Indeed. Upload your resume to see your personalized AI match %'}
                  </p>
                </div>
                <Link href="/jobs" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
                  View All Jobs <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </CardHeader>

              {!candidateProfile?.is_verified && (
                <div className="mx-4 sm:mx-6 my-2 p-3.5 rounded-xl bg-indigo-50/80 border border-indigo-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-indigo-900">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-600 shrink-0" />
                    <span>
                      These 50 jobs are live postings in the market database. <strong>Upload your master resume</strong> to calculate your ATS match scores!
                    </span>
                  </div>
                  <Link href="/profile">
                    <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0 text-xs h-7.5 px-3 shadow-xs">
                      <Upload className="w-3.5 h-3.5 mr-1" />
                      Upload Resume
                    </Button>
                  </Link>
                </div>
              )}

              <CardContent className="divide-y divide-slate-100 p-0">
                {recentJobs.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs">
                    No matching jobs found yet. Upload your resume or run a bot search to discover vacancies.
                  </div>
                ) : (
                  recentJobs.slice(0, 4).map((job) => (
                    <div key={job.id} className="p-4 sm:p-5 hover:bg-slate-50/80 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1.5 flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          {job.platform === 'indeed' ? (
                            <span className="inline-flex items-center gap-1 text-[10px] font-black tracking-wider uppercase px-2 py-0.5 rounded bg-blue-600 text-white shadow-2xs">
                              INDEED.COM
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[10px] font-black tracking-wider uppercase px-2 py-0.5 rounded bg-indigo-600 text-white shadow-2xs">
                              NAUKRI.COM
                            </span>
                          )}
                          <Link href={`/jobs/${job.id}`} className="font-semibold text-sm text-slate-900 hover:text-indigo-600 transition-colors">
                            {job.title}
                          </Link>
                          <Badge variant="outline" size="sm" className="capitalize">
                            {job.work_mode || 'Flexible'}
                          </Badge>
                        </div>

                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span className="flex items-center gap-1 font-medium text-slate-700">
                            <Building className="w-3.5 h-3.5" />
                            {job.company}
                          </span>
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5" />
                            {job.location}
                          </span>
                          <span className="font-medium text-slate-800">
                            {formatSalary(job.salary_min, job.salary_max, 'INR')}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 pt-1 flex-wrap">
                          {(job.skills_required || []).slice(0, 4).map((skill: string) => (
                            <span key={skill} className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center sm:flex-col sm:items-end justify-between gap-2 shrink-0">
                        {job.match_score !== undefined && job.match_score !== null ? (
                          <ScoreBadge score={job.match_score} showLabel />
                        ) : null}
                        <Link href={`/jobs/${job.id}`}>
                          <Button variant="outline" size="sm" className="text-xs">
                            Review & Apply
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Sidebar: Bot Status & Pipeline Breakdown */}
          <div className="space-y-6">
            {/* Bot Controls Widget */}
            <Card className="border-indigo-100 bg-gradient-to-b from-indigo-50/40 to-white">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${botStatus.is_running ? 'bg-emerald-500 animate-pulse' : 'bg-emerald-400'}`}></div>
                  <CardTitle className="text-sm">Automation Status</CardTitle>
                </div>
                <Badge variant={botStatus.is_running ? 'success' : 'outline'} size="sm">
                  {botStatus.status || 'Active'}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <div className="space-y-2 text-xs text-slate-600">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Match Threshold:</span>
                    <span className="font-semibold text-slate-800">{preferences.match_threshold}% &amp; above</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Daily Apply Cap:</span>
                    <span className="font-semibold text-indigo-700 font-bold">{preferences.daily_limit} apps / day</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Search Pool:</span>
                    <span className="font-semibold text-slate-800">50 scanned / run</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Schedule:</span>
                    <span className="font-semibold text-slate-800">{botStatus.schedule}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Submission Mode:</span>
                    <span className="font-semibold text-indigo-600">
                      {preferences.approval_mode === 'auto'
                        ? 'Auto Apply'
                        : preferences.approval_mode === 'manual'
                          ? 'Assisted Manual'
                          : 'Approval Queue'}
                    </span>
                  </div>

                  {/* Connected Accounts Badges */}
                  <div className="pt-2.5 mt-2 border-t border-slate-100 space-y-1.5">
                    <div className="flex justify-between items-center text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      <span>Connected Accounts</span>
                      <Link href="/bot-controls" className="text-indigo-600 font-semibold lowercase hover:underline">
                        manage
                      </Link>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs py-0.5">
                        <span className="text-slate-600 font-medium">Naukri:</span>
                        {platformAccounts.naukri.connected ? (
                          <span className="inline-flex items-center gap-1 font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 text-[10px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            {platformAccounts.naukri.email || 'Connected'}
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Not Connected</span>
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs py-0.5">
                        <span className="text-slate-600 font-medium">Indeed:</span>
                        {platformAccounts.indeed.connected ? (
                          <span className="inline-flex items-center gap-1 font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200 text-[10px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                            {platformAccounts.indeed.email || 'Connected'}
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[11px]">Not Connected</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <Link href="/bot-controls" className="block w-full">
                  <Button variant="primary" size="sm" className="w-full">
                    <span>Manage Bot Controls</span>
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Compliance Guarantee Widget */}
            <Card>
              <CardContent className="p-4 space-y-2.5">
                <div className="flex items-center gap-2 text-indigo-700 font-semibold text-xs">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span>Platform Compliance Active</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  The bot adheres strictly to Naukri and Indeed terms. Tailored resumes are verified against your master profile to eliminate hallucinated qualifications.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

