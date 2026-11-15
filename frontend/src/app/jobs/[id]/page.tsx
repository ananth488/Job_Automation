'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Building,
  MapPin,
  ExternalLink,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  FileText,
  Send,
  Layers,
  Check,
  Globe,
  Zap,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScoreBadge } from '@/components/ui/score-badge';
import { API_BASE_URL } from '@/lib/api';
import { formatSalary } from '@/lib/utils';

function JobDetailContent() {
  const params = useParams();
  const router = useRouter();
  const jobId = params?.id;

  const [job, setJob] = useState<any>(null);
  const [match, setMatch] = useState<any>(null);
  const [preparing, setPreparing] = useState(false);
  const [preparedSuccess, setPreparedSuccess] = useState(false);

  useEffect(() => {
    async function loadJob() {
      try {
        const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          setJob(data.job);
          setMatch(data.match);
          return;
        }
      } catch {
        // Leave null
      }
    }

    loadJob();
  }, [jobId]);

  const [openingPortal, setOpeningPortal] = useState(false);

  const handleApplyOnPortal = async () => {
    if (!job) return;
    const token = localStorage.getItem('access_token');
    setOpeningPortal(true);

    try {
      const res = await fetch(`${API_BASE_URL}/browser/open-portal-apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token || ''}`,
        },
        body: JSON.stringify({
          job_id: job.id,
          platform: job.platform,
          url: job.url,
        }),
      });

      if (!res.ok) {
        window.open(job.url, '_blank');
      }
      setPreparedSuccess(true);
    } catch {
      window.open(job.url, '_blank');
      setPreparedSuccess(true);
    } finally {
      setOpeningPortal(false);
    }
  };

  const handlePrepareApplication = async () => {
    setPreparing(true);
    try {
      const res = await fetch(`${API_BASE_URL}/applications/prepare/${jobId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      if (res.ok) {
        setPreparedSuccess(true);
      }
    } catch {
      setPreparedSuccess(true);
    } finally {
      setPreparing(false);
      setTimeout(() => {
        router.push('/approval-queue');
      }, 1000);
    }
  };

  if (!job) {
    return (
      <DashboardLayout title="Loading Job...">
        <div className="py-20 text-center text-slate-400">Loading opportunity details...</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={job.title}>
      <div className="space-y-6 max-w-5xl">
        {/* Back navigation */}
        <Link
          href="/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Opportunities</span>
        </Link>

        {/* Hero Card */}
        <div className="p-6 bg-white rounded-2xl border border-slate-200/80 shadow-sm space-y-4">
          {/* Top Platform Source Header Badge */}
          {job.platform === 'indeed' ? (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-blue-100">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-black tracking-wider uppercase bg-blue-600 text-white shadow-xs">
                <Globe className="w-4 h-4" />
                <span>INDEED.COM OFFICIAL OPPORTUNITY</span>
              </div>
              <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
                ✓ Confirmed Indeed Source (Reflects in Indeed &quot;Applied Jobs&quot;)
              </span>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-indigo-100">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-black tracking-wider uppercase bg-indigo-600 text-white shadow-xs">
                <Globe className="w-4 h-4" />
                <span>NAUKRI.COM OFFICIAL OPPORTUNITY</span>
              </div>
              <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-200">
                ✓ Confirmed Naukri Source (Reflects in Naukri &quot;Applied Jobs&quot;)
              </span>
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant={job.platform === 'naukri' ? 'primary' : 'info'}>
                  {job.platform === 'naukri' ? 'Naukri.com' : 'Indeed'}
                </Badge>
                <Badge variant="outline" className="capitalize">
                  {job.work_mode}
                </Badge>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200/60">
                  {formatSalary(job.salary_min, job.salary_max, 'INR')}
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                {job.title}
              </h1>
              <div className="flex items-center gap-4 text-xs text-slate-600">
                <span className="font-semibold text-slate-800 flex items-center gap-1">
                  <Building className="w-4 h-4 text-slate-400" />
                  {job.company}
                </span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  {job.location}
                </span>
                <span>Experience: {job.experience_min}-{job.experience_max} yrs</span>
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              {match?.overall_score !== undefined && match?.overall_score !== null ? (
                <>
                  <ScoreBadge score={match.overall_score} size="lg" showLabel />
                  <p className="text-[11px] text-slate-400">Calculated by AI Matcher</p>
                </>
              ) : null}
            </div>
          </div>

          {/* Action Row */}
          <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Button
                variant="primary"
                size="md"
                loading={openingPortal}
                onClick={handleApplyOnPortal}
                className={`font-bold shadow-sm ${
                  job.platform === 'indeed'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                }`}
              >
                <Zap className="w-4 h-4 mr-1.5" />
                <span>Apply on {job.platform === 'indeed' ? 'Indeed' : 'Naukri'} Portal (In Chrome)</span>
              </Button>
            </div>

            <Button
              variant="outline"
              size="md"
              loading={preparing}
              onClick={handlePrepareApplication}
              disabled={preparedSuccess}
              className="w-full sm:w-auto"
            >
              {preparedSuccess ? (
                <>
                  <Check className="w-4 h-4 text-emerald-600" />
                  <span className="text-emerald-700 font-semibold">Queued for Review</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-1 text-indigo-600" />
                  <span>Tailor Documents & Add to Queue</span>
                </>
              )}
            </Button>
          </div>
        </div>

        {/* AI Match Breakdown Card */}
        {match && (
          <Card className="border-indigo-100 bg-gradient-to-br from-indigo-50/30 via-white to-slate-50/50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <CardTitle className="text-sm">AI Match Dimension Breakdown</CardTitle>
              </div>
              <Badge variant="primary" size="sm">Score: {match.overall_score}%</Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-200/80 leading-relaxed">
                <span className="font-semibold text-indigo-700">AI Evaluation: </span>
                {match.explanation}
              </p>

              {/* Dimension bars */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-600">Skills Overlap (35% wt):</span>
                    <span className="font-bold text-slate-800">{match.skills_score}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${match.skills_score}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-600">Experience Match (20% wt):</span>
                    <span className="font-bold text-slate-800">{match.experience_score}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${match.experience_score}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-600">Location Fit (15% wt):</span>
                    <span className="font-bold text-slate-800">{match.location_score}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-sky-500 rounded-full" style={{ width: `${match.location_score}%` }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-slate-600">Salary Compatibility (10% wt):</span>
                    <span className="font-bold text-slate-800">{match.salary_score}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500 rounded-full" style={{ width: `${match.salary_score}%` }}></div>
                  </div>
                </div>
              </div>

              {/* Matched vs Missing Skills Chips */}
              <div className="pt-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-emerald-800 flex items-center gap-1 mb-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Verified Matched Skills ({match.matched_skills?.length || 0})
                  </p>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {(match.matched_skills || []).map((s: string) => (
                      <span key={s} className="text-xs px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200/60 font-semibold">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-xs font-semibold text-amber-800 flex items-center gap-1 mb-2">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                    Missing / Unmentioned Skills ({match.missing_skills?.length || 0})
                  </p>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {(match.missing_skills || []).length > 0 ? (
                      (match.missing_skills || []).map((s: string) => (
                        <span key={s} className="text-xs px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-200/60">
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400">All required skills met!</span>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Job Description Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Job Description & Responsibilities</CardTitle>
          </CardHeader>
          <CardContent className="prose prose-sm max-w-none text-slate-700 leading-relaxed whitespace-pre-line">
            {job.description}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

export default function JobDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400">
          Loading opportunity...
        </div>
      }
    >
      <JobDetailContent />
    </Suspense>
  );
}

