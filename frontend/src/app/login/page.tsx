'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle,
  UserPlus,
  LogIn,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { API_BASE_URL } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');

  // Form states
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});
  const [formError, setFormError] = useState<string>('');

  const validate = () => {
    const errors: { [key: string]: string } = {};
    if (mode === 'register' && !fullName.trim()) {
      errors.fullName = 'Full Name is required';
    }
    if (!email.trim()) {
      errors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errors.email = 'Please enter a valid email address';
    }
    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) {
      toast.error('Please fix the errors highlighted in red');
      return;
    }

    setLoading(true);
    setFieldErrors({});
    setFormError('');

    try {
      const formData = new URLSearchParams();
      formData.append('username', email.trim());
      formData.append('password', password);

      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const msg = errorData.detail || 'Incorrect email or password';
        toast.error(msg);
        setFormError(msg);
        if (msg.toLowerCase().includes('password')) {
          setFieldErrors({ password: msg });
        } else {
          setFieldErrors({ email: msg });
        }
        return;
      }

      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      toast.success(`Welcome back, ${data.user?.full_name || 'Candidate'}!`);
      router.push('/dashboard');
    } catch (err: any) {
      toast.error(err.message || 'Login failed. Please check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) {
      toast.error('Please fix the errors highlighted in red');
      return;
    }

    setLoading(true);
    setFieldErrors({});

    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: email.trim(),
          password: password,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const msg = errorData.detail || 'Registration failed. Email might already exist.';
        toast.error(msg);
        setFieldErrors({ email: msg });
        return;
      }

      toast.success('Account created successfully! Logging you in...');

      // Immediately log in new user
      const formData = new URLSearchParams();
      formData.append('username', email.trim());
      formData.append('password', password);

      const loginRes = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      if (loginRes.ok) {
        const tokenData = await loginRes.json();
        localStorage.setItem('access_token', tokenData.access_token);
        if (tokenData.user) {
          localStorage.setItem('user', JSON.stringify(tokenData.user));
        }
        router.push('/dashboard');
      } else {
        setMode('login');
      }
    } catch (err: any) {
      toast.error(err.message || 'Registration failed. Server unreachable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden">
        {/* Brand Header */}
        <div className="bg-slate-950 p-6 sm:p-8 text-center text-white relative">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 mx-auto flex items-center justify-center shadow-lg shadow-indigo-600/40 mb-3">
            <Sparkles className="w-6 h-6 text-indigo-100" />
          </div>
          <h1 className="text-xl font-bold tracking-tight">AI Job Application Bot</h1>
          <p className="text-xs text-slate-400 mt-1">Multi-user personal assistant for Naukri & Indeed</p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex border-b border-slate-100 bg-slate-50">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setFieldErrors({});
            }}
            className={`flex-1 py-3 text-xs font-bold flex items-center justify-center gap-1.5 transition-colors border-b-2 ${
              mode === 'login'
                ? 'border-indigo-600 text-indigo-600 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setFieldErrors({});
              setFormError('');
            }}
            className={`flex-1 py-3 text-xs font-bold flex items-center justify-center gap-1.5 transition-colors border-b-2 ${
              mode === 'register'
                ? 'border-indigo-600 text-indigo-600 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            <UserPlus className="w-4 h-4" />
            <span>Create New Account</span>
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6 sm:p-8 space-y-4">
          {formError && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-start gap-2.5 animate-fadeIn">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold leading-relaxed">{formError}</p>
                {(formError.includes('register') || formError.includes('Create New Account')) && (
                  <button
                    type="button"
                    onClick={() => {
                      setMode('register');
                      setFormError('');
                      setFieldErrors({});
                    }}
                    className="mt-1.5 inline-flex items-center gap-1 text-xs font-bold text-indigo-700 hover:text-indigo-900 underline cursor-pointer"
                  >
                    <span>Click here to create account with this email</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          )}

          {mode === 'login' ? (
            <form onSubmit={handleLogin} noValidate className="space-y-4">
              <Input
                label="Email Address"
                type="email"
                value={email}
                error={fieldErrors.email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: '' });
                }}
                placeholder="you@example.com"
                required
              />
              <Input
                label="Password"
                type="password"
                value={password}
                error={fieldErrors.password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: '' });
                }}
                placeholder="••••••••"
                required
              />

              <Button type="submit" loading={loading} className="w-full mt-2" size="lg">
                <span>Sign In to Dashboard</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </form>
          ) : (
            <form onSubmit={handleRegister} noValidate className="space-y-4">
              <Input
                label="Full Name"
                type="text"
                value={fullName}
                error={fieldErrors.fullName}
                onChange={(e) => {
                  setFullName(e.target.value);
                  if (fieldErrors.fullName) setFieldErrors({ ...fieldErrors, fullName: '' });
                }}
                placeholder="e.g. John Doe"
                required
              />
              <Input
                label="Email Address"
                type="email"
                value={email}
                error={fieldErrors.email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: '' });
                }}
                placeholder="you@example.com"
                required
              />
              <Input
                label="Password"
                type="password"
                value={password}
                error={fieldErrors.password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: '' });
                }}
                placeholder="Choose a strong password (min 6 chars)"
                required
              />

              <Button type="submit" loading={loading} className="w-full mt-2" size="lg">
                <span>Create Account & Setup Profile</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </form>
          )}

          <div className="mt-6 pt-4 border-t border-slate-100 text-center">
            <p className="text-[11px] text-slate-400 flex items-center justify-center gap-1">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
              Isolated user data: resume, preferences & application queue
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
