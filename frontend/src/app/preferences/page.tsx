'use client';

import React, { useState, useEffect } from 'react';
import {
  Sliders,
  CheckCircle2,
  Save,
  Building,
  MapPin,
  ShieldAlert,
  Percent,
  Clock,
} from 'lucide-react';
import { toast } from 'sonner';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MultiLocationInput } from '@/components/ui/location-autocomplete';

export default function PreferencesPage() {
  const [pref, setPref] = useState<{
    work_mode: string;
    min_salary: number | string;
    max_salary: number | string;
    experience_min: number | string;
    experience_max: number | string;
    notice_period: string;
    match_threshold: number;
    daily_limit: number | string;
    approval_mode: string;
    posted_within_days: number;
  }>({
    work_mode: 'any',
    min_salary: '',
    max_salary: '',
    experience_min: '',
    experience_max: '',
    notice_period: '',
    match_threshold: 75,
    daily_limit: 20,
    approval_mode: 'below_threshold',
    posted_within_days: 30,
  });

  const [rolesText, setRolesText] = useState('');
  const [keywordsText, setKeywordsText] = useState('');
  const [locations, setLocations] = useState<string[]>([]);

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    async function loadPref() {
      try {
        const res = await fetch('http://localhost:8000/api/v1/preferences/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          if (data) {
            setPref({
              work_mode: data.work_mode || 'any',
              min_salary: data.min_salary !== null && data.min_salary !== undefined ? data.min_salary : '',
              max_salary: data.max_salary !== null && data.max_salary !== undefined ? data.max_salary : '',
              experience_min: data.experience_min !== null && data.experience_min !== undefined ? data.experience_min : '',
              experience_max: data.experience_max !== null && data.experience_max !== undefined ? data.experience_max : '',
              notice_period: data.notice_period || '',
              match_threshold: data.match_threshold ?? 75,
              daily_limit: data.daily_limit !== null && data.daily_limit !== undefined ? data.daily_limit : 20,
              approval_mode: data.approval_mode || 'below_threshold',
              posted_within_days: data.posted_within_days ?? 30,
            });
            setRolesText((data.desired_roles || []).join(', '));
            setKeywordsText((data.keywords || []).join(', '));
            setLocations(Array.isArray(data.locations) ? data.locations : []);
          }
        }
      } catch {
        // Fallback
      }
    }
    loadPref();
  }, []);

  const handleSave = async () => {
    const errors: { [key: string]: string } = {};
    if (pref.min_salary && pref.max_salary && Number(pref.min_salary) > Number(pref.max_salary)) {
      errors.min_salary = 'Minimum CTC cannot be greater than Maximum CTC';
    }
    if (pref.experience_min && pref.experience_max && Number(pref.experience_min) > Number(pref.experience_max)) {
      errors.experience_min = 'Min experience cannot exceed max experience';
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      toast.error('Please fix the errors highlighted in red');
      return;
    }

    setFieldErrors({});
    setSaving(true);
    try {
      const payload = {
        desired_roles: rolesText.split(',').map((s) => s.trim()).filter(Boolean),
        keywords: keywordsText.split(',').map((s) => s.trim()).filter(Boolean),
        locations: locations,
        work_mode: pref.work_mode,
        min_salary: pref.min_salary !== '' && pref.min_salary !== null ? Number(pref.min_salary) : null,
        max_salary: pref.max_salary !== '' && pref.max_salary !== null ? Number(pref.max_salary) : null,
        experience_min: pref.experience_min !== '' && pref.experience_min !== null ? Number(pref.experience_min) : null,
        experience_max: pref.experience_max !== '' && pref.experience_max !== null ? Number(pref.experience_max) : null,
        notice_period: pref.notice_period.trim() || null,
        match_threshold: Number(pref.match_threshold) || 75,
        daily_limit: pref.daily_limit !== '' && pref.daily_limit !== null ? Number(pref.daily_limit) : 20,
        approval_mode: pref.approval_mode,
        posted_within_days: Number(pref.posted_within_days) || 30,
      };

      const res = await fetch('http://localhost:8000/api/v1/preferences/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setSuccess(true);
        toast.success('Job preferences saved successfully!');
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('preferences-updated'));
        }
        setTimeout(() => setSuccess(false), 3000);
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Failed to save preferences');
      }
    } catch {
      toast.error('Network error saving preferences');
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardLayout title="Job Search & Matching Preferences">
      <div className="space-y-6 max-w-4xl">
        <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-indigo-950">Matching Filters & Search Criteria</h3>
            <p className="text-xs text-indigo-800/80 mt-0.5">
              These rules govern how the bot identifies, filters, and shortlists vacancies across Naukri & Indeed.
            </p>
          </div>
          <Sliders className="w-5 h-5 text-indigo-600 shrink-0" />
        </div>

        {/* Roles & Locations */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Target Roles & Geography</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Input
                label="Target Roles (comma-separated)"
                placeholder="e.g. Senior Backend Developer, Full Stack Engineer"
                value={rolesText}
                onChange={(e) => setRolesText(e.target.value)}
              />
            </div>

            <div>
              <Input
                label="Search Keywords & Technologies (comma-separated)"
                placeholder="e.g. Python, FastAPI, React, PostgreSQL, Docker"
                value={keywordsText}
                onChange={(e) => setKeywordsText(e.target.value)}
              />
            </div>

            <div>
              <MultiLocationInput
                label="Preferred Work Locations"
                placeholder="Type location to add (e.g. Chennai, Bengaluru, Remote)..."
                locations={locations}
                onChange={(locs) => setLocations(locs)}
                helperText="Jobs in these preferred locations receive higher matching scores from the AI bot."
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                  Work Mode Preference
                </label>
                <select
                  value={pref.work_mode || 'any'}
                  onChange={(e) => setPref({ ...pref, work_mode: e.target.value })}
                  aria-label="Work Mode Preference"
                  className="w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="any">Any Work Mode</option>
                  <option value="remote">Remote Only</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">Onsite Only</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-indigo-600" />
                  Job Freshness / Posted Date
                </label>
                <select
                  value={pref.posted_within_days}
                  onChange={(e) => setPref({ ...pref, posted_within_days: Number(e.target.value) })}
                  aria-label="Job Freshness / Posted Date Filter"
                  className="w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-medium"
                >
                  <option value={30}>Last 30 Days (Default)</option>
                  <option value={15}>Last 15 Days</option>
                  <option value={10}>Last 10 Days</option>
                  <option value={5}>Last 5 Days</option>
                  <option value={3}>Last 3 Days</option>
                  <option value={1}>Last 1 Day (24 Hours)</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Compensation & Experience */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Compensation & Experience Range</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Minimum Desired CTC (INR)"
                type="number"
                placeholder="e.g. 1500000"
                value={pref.min_salary}
                error={fieldErrors.min_salary}
                onChange={(e) => {
                  setPref({ ...pref, min_salary: e.target.value });
                  if (fieldErrors.min_salary) setFieldErrors({ ...fieldErrors, min_salary: '' });
                }}
              />
              <Input
                label="Maximum Target CTC (INR)"
                type="number"
                placeholder="e.g. 3500000"
                value={pref.max_salary}
                onChange={(e) => {
                  setPref({ ...pref, max_salary: e.target.value });
                  if (fieldErrors.min_salary) setFieldErrors({ ...fieldErrors, min_salary: '' });
                }}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Experience Min (Years)"
                type="number"
                placeholder="e.g. 2"
                value={pref.experience_min}
                error={fieldErrors.experience_min}
                onChange={(e) => {
                  setPref({ ...pref, experience_min: e.target.value });
                  if (fieldErrors.experience_min) setFieldErrors({ ...fieldErrors, experience_min: '' });
                }}
              />
              <Input
                label="Experience Max (Years)"
                type="number"
                placeholder="e.g. 6"
                value={pref.experience_max}
                onChange={(e) => {
                  setPref({ ...pref, experience_max: e.target.value });
                  if (fieldErrors.experience_min) setFieldErrors({ ...fieldErrors, experience_min: '' });
                }}
              />
            </div>

            <Input
              label="Official Notice Period"
              placeholder="e.g. Immediate, 15 Days, 30 Days"
              value={pref.notice_period}
              onChange={(e) => setPref({ ...pref, notice_period: e.target.value })}
            />
          </CardContent>
        </Card>

        {/* Automation Thresholds & Compliance Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Automation Thresholds & Rate Limits</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Minimum AI Match Score Threshold: <span className="font-bold text-indigo-600">{pref.match_threshold}%</span>
                </label>
              </div>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={pref.match_threshold}
                onChange={(e) => setPref({ ...pref, match_threshold: Number(e.target.value) })}
                className="w-full accent-indigo-600"
              />
              <p className="text-xs text-slate-400 mt-1">
                Jobs with match score below this threshold are automatically filtered out.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <Input
                label="Daily Application Limit"
                type="number"
                placeholder="e.g. 15"
                value={pref.daily_limit}
                onChange={(e) => setPref({ ...pref, daily_limit: e.target.value })}
                helperText={
                  Number(pref.daily_limit) > 20
                    ? '⚠️ Recommended: 10-20. Starting at 10-20 reduces the chance of your Naukri account being flagged.'
                    : 'Recommended: 10-20 applications/day to keep Naukri & Indeed accounts safe from anti-bot flags.'
                }
              />

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                  Application Approval Mode
                </label>
                <select
                  value={pref.approval_mode || 'below_threshold'}
                  onChange={(e) => setPref({ ...pref, approval_mode: e.target.value })}
                  aria-label="Application Approval Mode"
                  className="w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="always">Always Require Candidate Approval</option>
                  <option value="below_threshold">Approval Queue for All External Platforms</option>
                  <option value="auto">Auto Apply (where permitted by adapter)</option>
                </select>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              {success && (
                <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  Preferences updated successfully!
                </span>
              )}
              {!success && <span></span>}

              <Button variant="primary" size="md" loading={saving} onClick={handleSave}>
                <Save className="w-4 h-4 mr-1.5" />
                <span>Save Preferences</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
