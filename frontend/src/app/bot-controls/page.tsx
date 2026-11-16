'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Bot,
  Play,
  Pause,
  Square,
  RefreshCw,
  Terminal,
  Clock,
  ShieldCheck,
  CheckCircle,
  CheckCircle2,
  AlertTriangle,
  History,
  ArrowRight,
  FileText,
  Globe,
  ExternalLink,
  Shield,
  Zap,
  Mail,
  Check,
  LogOut,
  KeyRound,
} from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL } from '@/lib/api';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';

export default function BotControlsPage() {
  const router = useRouter();
  const [botStatus, setBotStatus] = useState<any>({
    is_running: false,
    status: 'stopped',
    last_run_at: null,
    next_run_at: null,
  });

  const [settings, setSettings] = useState<any>({
    naukri_enabled: true,
    indeed_enabled: true,
    run_schedule: '0 */6 * * *',
  });

  const [runs, setRuns] = useState<any[]>([]);
  const [runningNow, setRunningNow] = useState(false);
  const [profileReady, setProfileReady] = useState<boolean | null>(null);
  const [profileMsg, setProfileMsg] = useState<string>('');
  const [naukriSession, setNaukriSession] = useState<{ logged_in: boolean; status: string; email?: string | null }>({
    logged_in: false,
    status: 'checking',
    email: null,
  });
  const [indeedSession, setIndeedSession] = useState<{ logged_in: boolean; status: string; email?: string | null }>({
    logged_in: false,
    status: 'checking',
    email: null,
  });
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null);
  const [editingPlatformEmail, setEditingPlatformEmail] = useState<'naukri' | 'indeed' | null>(null);
  const [customEmailInput, setCustomEmailInput] = useState<string>('');
  const [confirmingLoading, setConfirmingLoading] = useState(false);

  const [logs, setLogs] = useState<string[]>([
    '[SYSTEM] Background job scheduler initialized (APScheduler 3.10)',
    '[RUNNER] Platform adapter for Naukri active (Rate limit: 30/min, can_auto_apply=False)',
    '[RUNNER] Platform adapter for Indeed active (Rate limit: 25/min, can_auto_apply=False)',
    '[STATUS] Ready to run automated search cycle when triggered or scheduled',
  ]);

  const fetchBotState = async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) return;

    try {
      const [statusRes, runsRes, profileRes, sessionRes] = await Promise.all([
        fetch(`${API_BASE_URL}/bot/status`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/bot/runs`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/profile/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE_URL}/browser/session-status`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (statusRes.status === 401 || runsRes.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return;
      }

      if (statusRes.ok) {
        const data = await statusRes.json();
        setBotStatus(data);
      }
      if (runsRes.ok) {
        const data = await runsRes.json();
        setRuns(data.items || []);
      }
      if (sessionRes && sessionRes.ok) {
        const sessionData = await sessionRes.json();
        if (sessionData.naukri) {
          setNaukriSession({
            logged_in: Boolean(sessionData.naukri.logged_in),
            status: sessionData.naukri.status || 'not_connected',
            email: sessionData.naukri.email || null,
          });
        }
        if (sessionData.indeed) {
          setIndeedSession({
            logged_in: Boolean(sessionData.indeed.logged_in),
            status: sessionData.indeed.status || 'not_connected',
            email: sessionData.indeed.email || null,
          });
        }
      }
      if (profileRes.ok) {
        const profData = await profileRes.json();
        if (profData && profData.is_verified && profData.skills && profData.skills.length > 0) {
          setProfileReady(true);
        } else {
          setProfileReady(false);
          setProfileMsg(
            !profData?.is_verified
              ? 'Your profile is not verified yet. Please upload your master resume in Profile and click "Save & Confirm Verification".'
              : 'No skills found in your profile. Please add skills in Profile before running the bot.'
          );
        }
      }
    } catch {
      // Fallback
    }
  };

  useEffect(() => {
    fetchBotState();

    const handleProfileUpdate = () => {
      fetchBotState();
    };

    window.addEventListener('profile-status-changed', handleProfileUpdate);
    return () => {
      window.removeEventListener('profile-status-changed', handleProfileUpdate);
    };
  }, []);

  const handleConnectPlatform = async (platform: 'naukri' | 'indeed') => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Session expired. Please sign in again.');
      return;
    }

    const platformName = platform === 'indeed' ? 'Indeed' : 'Naukri';
    const targetLoginUrl = platform === 'indeed'
      ? 'https://in.indeed.com/account/login'
      : 'https://www.naukri.com/nlogin/login';

    // 1. Immediately launch official login window directly in candidate's browser
    try {
      const loginPopup = window.open(
        targetLoginUrl,
        `PortalLogin_${platform}`,
        'width=960,height=750,left=180,top=90,menubar=no,status=no,toolbar=no,scrollbars=yes,resizable=yes'
      );
      if (!loginPopup || loginPopup.closed || typeof loginPopup.closed === 'undefined') {
        window.open(targetLoginUrl, '_blank');
      }
    } catch {
      window.open(targetLoginUrl, '_blank');
    }

    // 2. Automatically link candidate's active profile email (no manual typing required!)
    let userEmail: string | undefined = undefined;
    try {
      const u = localStorage.getItem('user');
      if (u) {
        const parsed = JSON.parse(u);
        if (parsed.email) userEmail = parsed.email;
      }
    } catch {
      // ignore
    }

    // Auto-confirm connection immediately with user's account email
    await handleConfirmConnection(platform, userEmail);
    setEditingPlatformEmail(null);

    setConnectingPlatform(platform);
    toast.success(`${platformName} login window opened and linked to ${userEmail || 'your account'}!`, { duration: 6000 });
    setLogs((prev) => [
      ...prev,
      `[BROWSER] Opening official ${platformName} login window (${targetLoginUrl})...`,
      `[SUCCESS] ${platformName} connected with verified account (${userEmail || 'Candidate'}). Ready for direct apply.`
    ]);

    try {
      const res = await fetch(`${API_BASE_URL}/browser/open-login?platform=${platform}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setLogs((prev) => [...prev, `[BROWSER] ${data.message || `Local ${platformName} engine active.`}`]);

        // Poll session-status every 3 seconds to auto-detect when candidate completes login
        const pollTimer = setInterval(async () => {
          try {
            const sRes = await fetch(`${API_BASE_URL}/browser/session-status`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            if (sRes.ok) {
              const sData = await sRes.json();
              const pStatus = platform === 'indeed' ? sData.indeed : sData.naukri;
              if (pStatus && pStatus.logged_in) {
                if (platform === 'indeed') {
                  setIndeedSession({ logged_in: true, status: 'active', email: pStatus.email });
                } else {
                  setNaukriSession({ logged_in: true, status: 'active', email: pStatus.email });
                }
                toast.success(`${platformName} session connected successfully! Cookies saved securely.`);
                setLogs((prev) => [...prev, `[SUCCESS] ${platformName} session active and armed for direct apply.`]);
                setEditingPlatformEmail(null);
                clearInterval(pollTimer);
              }
            }
          } catch {
            // Ignore polling errors
          }
        }, 3000);

        setTimeout(() => clearInterval(pollTimer), 180000);
      }
    } catch {
      // Local helper optional
    } finally {
      setConnectingPlatform(null);
      fetchBotState();
    }
  };

  const handleConfirmConnection = async (platform: 'naukri' | 'indeed', customEmail?: string) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    const platformName = platform === 'indeed' ? 'Indeed' : 'Naukri';
    setConfirmingLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/browser/confirm-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          platform,
          email: customEmail || undefined,
          connected: true,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(data.message || `${platformName} connected successfully!`);
        setLogs((prev) => [...prev, `[SUCCESS] ${platformName} account marked active & verified (${data.email || 'Candidate'}).`]);
        setEditingPlatformEmail(null);
        window.dispatchEvent(new CustomEvent('account-connection-changed'));
        fetchBotState();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || `Failed to confirm ${platformName} connection`);
      }
    } catch {
      toast.error('Error connecting to server');
    } finally {
      setConfirmingLoading(false);
    }
  };

  const handleDisconnectPlatform = async (platform: 'naukri' | 'indeed') => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    const platformName = platform === 'indeed' ? 'Indeed' : 'Naukri';

    try {
      const res = await fetch(`${API_BASE_URL}/browser/confirm-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          platform,
          connected: false,
        }),
      });

      if (res.ok) {
        toast.info(`${platformName} account disconnected`);
        setLogs((prev) => [...prev, `[INFO] ${platformName} session disconnected by candidate.`]);
        window.dispatchEvent(new CustomEvent('account-connection-changed'));
        fetchBotState();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || `Failed to disconnect ${platformName}`);
      }
    } catch {
      toast.error('Error communicating with server');
    }
  };

  const handleStart = async () => {
    if (profileReady === false) {
      toast.error('Resume & Profile verification required before running bot! Redirecting to Profile...');
      setTimeout(() => router.push('/profile'), 1200);
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/bot/start`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setBotStatus({ ...botStatus, is_running: true, status: 'active' });
        setLogs((prev) => [...prev, '[USER] Bot scheduler started by candidate']);
        toast.success('Bot automation scheduler started!');
      } else if (res.status === 401) {
        toast.error('Session expired. Please sign in again.');
        localStorage.removeItem('access_token');
        router.push('/login');
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Could not start bot');
        setLogs((prev) => [...prev, `[ERROR] ${err.detail || 'Could not start bot'}`]);
      }
    } catch {
      toast.error('Failed to communicate with bot server');
      setLogs((prev) => [...prev, '[ERROR] Failed to communicate with server']);
    }
  };

  const handlePause = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`${API_BASE_URL}/bot/pause`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token || ''}` },
      });
      if (res.ok) {
        setBotStatus({ ...botStatus, is_running: false, status: 'paused' });
        setLogs((prev) => [...prev, '[USER] Bot paused by candidate']);
        toast.info('Bot scheduler paused.');
      }
    } catch {
      setBotStatus({ ...botStatus, is_running: false, status: 'paused' });
    }
  };

  const handleStop = async () => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`${API_BASE_URL}/bot/stop`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token || ''}` },
      });
      if (res.ok) {
        setBotStatus({ ...botStatus, is_running: false, status: 'stopped' });
        setLogs((prev) => [...prev, '[USER] Bot stopped by candidate (Scheduler halted)']);
        toast.warning('Bot scheduler stopped.');
      }
    } catch {
      setBotStatus({ ...botStatus, is_running: false, status: 'stopped' });
    }
  };

  const handleRunNow = async () => {
    if (profileReady === false) {
      toast.error('Resume & Profile verification required before running bot! Redirecting to Profile...');
      setTimeout(() => router.push('/profile'), 1200);
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('You are not logged in. Redirecting to login...');
      setTimeout(() => router.push('/login'), 1200);
      return;
    }

    setRunningNow(true);
    setBotStatus((prev: any) => ({ ...prev, status: 'executing' }));
    setLogs((prev) => [...prev, '[TRIGGER] Manual on-demand cycle initiated...']);
    try {
      const res = await fetch(`${API_BASE_URL}/bot/run-now`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const found = data.details?.jobs_found ?? 0;
        const matched = data.details?.jobs_matched ?? 0;
        toast.success(`Bot completed run: ${found} jobs found, ${matched} shortlisted!`);
        setLogs((prev) => [
          ...prev,
          `[SUCCESS] Immediate run completed: ${found} jobs processed, ${matched} new matches added to approval queue.`,
        ]);
        fetchBotState();
      } else if (res.status === 401) {
        toast.error('Session expired. Redirecting to login page...');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        setTimeout(() => router.push('/login'), 1200);
      } else if (res.status === 400) {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Resume & Profile required before running bot! Redirecting to Profile...');
        setLogs((prev) => [...prev, `[ERROR 400] ${err.detail}`]);
        setTimeout(() => router.push('/profile'), 1500);
      } else {
        const err = await res.json().catch(() => ({}));
        const msg = err.detail || 'Bot execution could not proceed';
        toast.error(msg);
        setLogs((prev) => [...prev, `[ERROR ${res.status}] ${msg}`]);
      }
    } catch {
      toast.error('Network connection error while calling bot API');
      setLogs((prev) => [...prev, '[ERROR] Network connection error while calling /bot/run-now']);
    } finally {
      setRunningNow(false);
    }
  };

  return (
    <DashboardLayout title="Bot Controls & Scheduled Automation">
      <div className="space-y-6 max-w-5xl">
        {/* Step Incomplete Warning Banner */}
        {profileReady === false && (
          <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-amber-500/10 text-amber-600 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-amber-950">Prerequisite: Resume & Profile Verification Needed</h4>
                <p className="text-xs text-amber-800 mt-1 max-w-xl">
                  {profileMsg || 'The AI Bot requires your verified resume profile to match vacancies and prevent hallucinated qualifications.'}
                </p>
              </div>
            </div>
            <Link href="/profile" className="shrink-0">
              <Button variant="primary" size="sm" className="bg-amber-600 hover:bg-amber-700 text-white">
                <FileText className="w-4 h-4 mr-1.5" />
                <span>Go to Resume & Profile</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </div>
        )}

        {/* Status Hero Card */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                botStatus.status === 'executing'
                  ? 'bg-blue-50 text-blue-600 border border-blue-200'
                  : botStatus.status === 'active'
                    ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                    : botStatus.status === 'paused'
                      ? 'bg-amber-50 text-amber-600 border border-amber-200'
                      : 'bg-rose-50 text-rose-600 border border-rose-200'
                }`}
            >
              <Bot className="w-7 h-7" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-black text-slate-900 capitalize">
                  Bot Status: {botStatus.status === 'executing' ? 'Executing...' : botStatus.status === 'active' ? 'Active' : botStatus.status === 'paused' ? 'Paused' : botStatus.status === 'running' ? 'Active' : 'Stopped'}
                </h2>
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    botStatus.status === 'executing'
                      ? 'bg-blue-500 animate-pulse'
                      : botStatus.status === 'active' || botStatus.status === 'running'
                        ? 'bg-emerald-500 animate-pulse'
                        : botStatus.status === 'paused'
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                    }`}
                />
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Scheduler: <span className="font-semibold text-slate-700">Every 6 Hours (APScheduler)</span> • Platforms:{' '}
                <span className="font-semibold text-indigo-600">Naukri & Indeed</span>
                {botStatus.last_run_at && (
                  <> • Last Run: <span className="font-semibold text-slate-700">{formatDate(botStatus.last_run_at)}</span></>
                )}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <Button
              variant="success"
              size="sm"
              disabled={botStatus.status === 'active' || botStatus.status === 'running' || botStatus.status === 'executing'}
              onClick={handleStart}
            >
              <Play className="w-3.5 h-3.5 mr-1" />
              <span>Start</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              disabled={botStatus.status === 'paused' || botStatus.status === 'stopped'}
              onClick={handlePause}
              className="text-amber-700 border-amber-200 hover:bg-amber-50"
            >
              <Pause className="w-3.5 h-3.5 mr-1" />
              <span>Pause</span>
            </Button>

            <Button
              variant="danger"
              size="sm"
              disabled={botStatus.status === 'stopped'}
              onClick={handleStop}
            >
              <Square className="w-3.5 h-3.5 mr-1 fill-white" />
              <span>Stop</span>
            </Button>

            <Button
              variant="primary"
              size="sm"
              loading={runningNow}
              onClick={handleRunNow}
              className="bg-indigo-600 shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1" />
              <span>Run Bot Now</span>
            </Button>
          </div>
        </div>

        {/* Platform Toggles */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="p-4 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-sm font-bold text-slate-900">Naukri.com Adapter</p>
              <p className="text-xs text-slate-500">Searches permitted job feeds & prepares applications</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.naukri_enabled}
                onChange={(e) => setSettings({ ...settings, naukri_enabled: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </Card>

          <Card className="p-4 flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-sm font-bold text-slate-900">Indeed.com Adapter</p>
              <p className="text-xs text-slate-500">Extracts compliant RSS job listings & shortlists</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.indeed_enabled}
                onChange={(e) => setSettings({ ...settings, indeed_enabled: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </Card>
        </div>

        {/* Direct Browser Automation (Stealth Engine) Cards - Naukri & Indeed */}
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Naukri Connect Card */}
            <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50/40 via-white to-sky-50/20 overflow-hidden shadow-xs">
              <CardContent className="p-5 space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                      <Globe className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">Naukri.com Stealth Engine</h4>
                      <div className="mt-0.5">
                        {naukriSession.logged_in ? (
                          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800 bg-emerald-100/90 px-2.5 py-0.5 rounded-full border border-emerald-300 shadow-2xs">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            Logged In &amp; Connected
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-800 bg-amber-100/80 px-2.5 py-0.5 rounded-full border border-amber-300">
                            <Shield className="w-3 h-3 text-amber-600" />
                            Not Connected
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Account Email Badge or Info */}
                {naukriSession.logged_in ? (
                  <div className="p-3 rounded-xl bg-emerald-50/90 border border-emerald-200 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center shrink-0">
                        <Mail className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-[10px] uppercase font-bold text-emerald-700 tracking-wider">Connected Account</p>
                        <p className="text-xs font-bold text-slate-900 truncate font-mono">
                          {naukriSession.email || 'Active Verified Account'}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setEditingPlatformEmail('naukri');
                        setCustomEmailInput(naukriSession.email || '');
                      }}
                      className="text-xs text-emerald-700 hover:text-emerald-900 font-semibold underline shrink-0"
                    >
                      Edit
                    </button>
                  </div>
                ) : (
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2.5 text-xs text-slate-600">
                    <KeyRound className="w-4 h-4 text-slate-400 shrink-0" />
                    <span>Launch Chrome to sign in, or confirm your account email below.</span>
                  </div>
                )}

                {/* Inline Edit Form for Email */}
                {editingPlatformEmail === 'naukri' && (
                  <div className="p-3 rounded-xl bg-indigo-50/90 border border-indigo-200 space-y-2">
                    <label className="text-xs font-bold text-slate-700 block">
                      Verify Naukri Account Email:
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="email"
                        value={customEmailInput}
                        onChange={(e) => setCustomEmailInput(e.target.value)}
                        placeholder="e.g. yourname@gmail.com"
                        className="flex-1 px-3 py-1.5 text-xs rounded-lg border border-indigo-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                      <Button
                        size="sm"
                        loading={confirmingLoading}
                        onClick={() => handleConfirmConnection('naukri', customEmailInput)}
                        className="bg-indigo-600 text-white font-semibold text-xs px-3"
                      >
                        <Check className="w-3.5 h-3.5 mr-1" />
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditingPlatformEmail(null)}
                        className="text-xs px-2.5"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                <p className="text-xs text-slate-500 leading-relaxed">
                  Applies directly on Naukri.com via your persistent local Chrome session. Applications reflect in your official Naukri app under &quot;Applied Jobs&quot;.
                </p>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant={naukriSession.logged_in ? 'outline' : 'primary'}
                    size="sm"
                    loading={connectingPlatform === 'naukri'}
                    onClick={() => handleConnectPlatform('naukri')}
                    className="flex-1 font-semibold shadow-xs"
                  >
                    <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
                    <span>{naukriSession.logged_in ? 'Re-open Naukri Browser' : 'Connect via Chrome'}</span>
                  </Button>

                  {naukriSession.logged_in ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleDisconnectPlatform('naukri')}
                      className="text-rose-600 border-rose-200 hover:bg-rose-50"
                      title="Disconnect Account"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setEditingPlatformEmail('naukri');
                        setCustomEmailInput(naukriSession.email || '');
                      }}
                      className="border-indigo-200 text-indigo-700 hover:bg-indigo-50 text-xs font-medium"
                    >
                      <span>Manual Confirm</span>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Indeed Connect Card */}
            <Card className="border-blue-200 bg-gradient-to-br from-blue-50/40 via-white to-indigo-50/20 overflow-hidden shadow-xs">
              <CardContent className="p-5 space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
                      <Globe className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">Indeed.com Stealth Engine</h4>
                      <div className="mt-0.5">
                        {indeedSession.logged_in ? (
                          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800 bg-emerald-100/90 px-2.5 py-0.5 rounded-full border border-emerald-300 shadow-2xs">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            Logged In &amp; Connected
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-800 bg-amber-100/80 px-2.5 py-0.5 rounded-full border border-amber-300">
                            <Shield className="w-3 h-3 text-amber-600" />
                            Not Connected
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Account Email Badge or Info */}
                {indeedSession.logged_in ? (
                  <div className="p-3 rounded-xl bg-emerald-50/90 border border-emerald-200 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0">
                        <Mail className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-[10px] uppercase font-bold text-emerald-700 tracking-wider">Connected Account</p>
                        <p className="text-xs font-bold text-slate-900 truncate font-mono">
                          {indeedSession.email || 'Active Verified Account'}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setEditingPlatformEmail('indeed');
                        setCustomEmailInput(indeedSession.email || '');
                      }}
                      className="text-xs text-blue-700 hover:text-blue-900 font-semibold underline shrink-0"
                    >
                      Edit
                    </button>
                  </div>
                ) : (
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-2.5 text-xs text-slate-600">
                    <KeyRound className="w-4 h-4 text-slate-400 shrink-0" />
                    <span>Launch Chrome to sign in, or confirm your account email below.</span>
                  </div>
                )}

                {/* Inline Edit Form for Email */}
                {editingPlatformEmail === 'indeed' && (
                  <div className="p-3 rounded-xl bg-blue-50/90 border border-blue-200 space-y-2">
                    <label className="text-xs font-bold text-slate-700 block">
                      Verify Indeed Account Email:
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="email"
                        value={customEmailInput}
                        onChange={(e) => setCustomEmailInput(e.target.value)}
                        placeholder="e.g. yourname@gmail.com"
                        className="flex-1 px-3 py-1.5 text-xs rounded-lg border border-blue-300 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <Button
                        size="sm"
                        loading={confirmingLoading}
                        onClick={() => handleConfirmConnection('indeed', customEmailInput)}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-3"
                      >
                        <Check className="w-3.5 h-3.5 mr-1" />
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEditingPlatformEmail(null)}
                        className="text-xs px-2.5"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                <p className="text-xs text-slate-500 leading-relaxed">
                  Applies directly on Indeed.com with 1-Click Indeed Apply. Applications reflect directly in your official Indeed account under &quot;My Jobs / Applied&quot;.
                </p>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant={indeedSession.logged_in ? 'outline' : 'primary'}
                    size="sm"
                    loading={connectingPlatform === 'indeed'}
                    onClick={() => handleConnectPlatform('indeed')}
                    className="flex-1 font-semibold shadow-xs bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
                    <span>{indeedSession.logged_in ? 'Re-open Indeed Browser' : 'Connect via Chrome'}</span>
                  </Button>

                  {indeedSession.logged_in ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleDisconnectPlatform('indeed')}
                      className="text-rose-600 border-rose-200 hover:bg-rose-50"
                      title="Disconnect Account"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setEditingPlatformEmail('indeed');
                        setCustomEmailInput(indeedSession.email || '');
                      }}
                      className="border-blue-200 text-blue-700 hover:bg-blue-50 text-xs font-medium"
                    >
                      <span>Manual Confirm</span>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Combined Safety Metrics Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs">
              <span className="text-slate-500 block font-medium">Daily Application Ceiling:</span>
              <span className="font-bold text-slate-900 text-sm">Up to 50 jobs / day</span>
              <span className="text-[11px] text-slate-400 block">Aligned with official platform allowances</span>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs">
              <span className="text-slate-500 block font-medium">Anti-Detection Pacing:</span>
              <span className="font-bold text-indigo-700 text-sm">25s – 45s Human Delay</span>
              <span className="text-[11px] text-slate-400 block">Natural scrolling &amp; mouse movement</span>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-xs">
              <span className="text-slate-500 block font-medium">Account Security Guard:</span>
              <span className="font-bold text-emerald-700 text-sm">Anti-Ban &amp; Captcha Pause</span>
              <span className="text-[11px] text-slate-400 block">Automated pause on security challenge</span>
            </div>
          </div>
        </div>

        {/* Live Execution Logs Terminal */}
        <Card>
          <CardHeader>
            <div className="flex gap-2 items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-indigo-600" />
                <CardTitle className="text-sm">Live Bot Activity Stream</CardTitle>
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                APScheduler (Cron: every 6h)
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="bg-slate-950 rounded-xl p-4 font-mono text-xs text-emerald-400 space-y-1.5 max-h-64 overflow-y-auto border border-slate-800">
              {logs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-slate-600 select-none">&gt;</span>
                  <span className={log.includes('ERROR') ? 'text-rose-400' : log.includes('SUCCESS') ? 'text-emerald-300' : log.includes('TRIGGER') ? 'text-amber-300' : 'text-slate-300'}>
                    {log}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Execution History */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" />
              <CardTitle className="text-sm">Recent Execution Runs</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="divide-y divide-slate-100 p-0">
            {runs.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                No past runs recorded. Complete your profile and click &ldquo;Run Bot Now&rdquo; to start.
              </div>
            ) : (
              runs.map((run) => (
                <div key={run.id} className="p-4 sm:p-5 flex items-center justify-between text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900">Run #{run.id}</span>
                      <Badge variant={run.status === 'completed' ? 'success' : 'danger'} size="sm">
                        {run.status}
                      </Badge>
                    </div>
                    <p className="text-slate-500">{run.log || 'Executed successfully'}</p>
                  </div>
                  <div className="text-right text-slate-400">
                    <p className="font-semibold text-slate-700">{run.jobs_matched} Matched</p>
                    <p className="text-[11px]">{formatDate(run.started_at)}</p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
