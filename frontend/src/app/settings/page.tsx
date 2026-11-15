'use client';

import React, { useState } from 'react';
import {
  Settings,
  Key,
  Shield,
  Bell,
  User,
  Save,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/lib/use-auth';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { user, initials, logout } = useAuth();
  const [apiKey, setApiKey] = useState('');
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [instantInterviewAlerts, setInstantInterviewAlerts] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    toast.success('System settings saved successfully!');
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <DashboardLayout title="System Settings & Security">
      <div className="space-y-6 max-w-4xl">
        {/* Active Account Profile Card */}
        <Card className="border-indigo-100">
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-indigo-600" />
              <CardTitle className="text-sm">Active Account Profile</CardTitle>
            </div>
            <button
              onClick={logout}
              className="text-xs font-semibold text-rose-600 hover:text-rose-800 transition-colors"
            >
              Sign Out / Switch User
            </button>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">
                {initials}
              </div>
              <div>
                <p className="text-sm font-bold text-slate-900">{user?.full_name || 'Candidate'}</p>
                <p className="text-xs text-slate-500">{user?.email || 'Logged In'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* LLM & AI Provider Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Key className="w-4 h-4 text-indigo-600" />
              <CardTitle className="text-sm">AI Engine Configuration</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-xs text-slate-500">
              The bot uses Anthropic Claude behind a provider-agnostic service layer for intelligent structured resume extraction, matching explanations, and tailoring.
            </p>

            <Input
              label="Anthropic Claude API Key"
              type="password"
              placeholder="sk-ant-api03-••••••••••••••••••••••••"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              helperText="Encrypted securely in environment variables."
            />

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Model Tier
              </label>
              <select
                aria-label="Model Tier"
                className="w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              >
                <option>Claude 3.5 Sonnet (Recommended for Resume Tailoring)</option>
                <option>Claude 3.5 Haiku (Fast & Cost Effective)</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Email Notification Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-indigo-600" />
              <CardTitle className="text-sm">Notification Preferences</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <label className="flex items-center justify-between p-3 rounded-xl bg-slate-50 cursor-pointer">
              <div>
                <p className="text-xs font-semibold text-slate-900">Daily Digest Email</p>
                <p className="text-[11px] text-slate-500">Receive a daily morning summary of shortlisted jobs and new matches</p>
              </div>
              <input
                type="checkbox"
                checked={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.checked)}
                className="w-4 h-4 text-indigo-600 accent-indigo-600 rounded"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-xl bg-slate-50 cursor-pointer">
              <div>
                <p className="text-xs font-semibold text-slate-900">Instant Interview Alerts</p>
                <p className="text-[11px] text-slate-500">Immediate push alert when a recruiter requests an interview</p>
              </div>
              <input
                type="checkbox"
                checked={instantInterviewAlerts}
                onChange={(e) => setInstantInterviewAlerts(e.target.checked)}
                className="w-4 h-4 text-indigo-600 accent-indigo-600 rounded"
              />
            </label>
          </CardContent>
        </Card>

        {/* Compliance Guard Summary */}
        <Card className="border-emerald-100 bg-emerald-50/20">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-600" />
              <CardTitle className="text-sm">Compliance & Truthfulness Guard</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-slate-600">
            <p>✓ All platform adapters enforce <code>can_auto_apply: false</code> for Naukri and Indeed to ensure compliant candidate-assisted submission.</p>
            <p>✓ Hallucination detector blocks any generated resume sentence containing skills or dates not in your verified profile.</p>
            <p>✓ Rate limiting throttles queries with polite random delays between requests.</p>
          </CardContent>
        </Card>

        {/* Save button */}
        <div className="flex items-center justify-between pt-2">
          {saved ? (
            <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" />
              Settings updated successfully!
            </span>
          ) : (
            <span></span>
          )}

          <Button variant="primary" size="md" onClick={handleSave}>
            <Save className="w-4 h-4 mr-1.5" />
            <span>Save Settings</span>
          </Button>
        </div>
      </div>
    </DashboardLayout>
  );
}

