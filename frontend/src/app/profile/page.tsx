'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  FileText,
  CheckCircle2,
  Plus,
  Trash2,
  Save,
  ShieldCheck,
  AlertCircle,
  ExternalLink,
  FileCheck,
  Briefcase,
  Building2,
  Pencil,
  X,
  Download,
  RefreshCw,
} from 'lucide-react';
import { toast } from 'sonner';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { LocationAutocomplete } from '@/components/ui/location-autocomplete';
import { useAuth } from '@/lib/use-auth';

export default function ProfilePage() {
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [profile, setProfile] = useState<any>({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    preferred_locations: [],
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
    summary: '',
    skills: [],
    experience: [],
    total_experience_years: 0,
    is_verified: false,
  });

  const [newSkill, setNewSkill] = useState('');
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [latestResume, setLatestResume] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});
  const [editingExpIndex, setEditingExpIndex] = useState<number | 'new' | null>(null);
  const [expForm, setExpForm] = useState<{
    title: string;
    company: string;
    location: string;
    start: string;
    end: string;
    description: string;
  }>({
    title: '',
    company: '',
    location: '',
    start: '',
    end: '',
    description: '',
  });

  const handleStartAddExp = () => {
    setExpForm({
      title: '',
      company: '',
      location: '',
      start: '',
      end: '',
      description: '',
    });
    setEditingExpIndex('new');
  };

  const handleStartEditExp = (idx: number) => {
    const item = (profile.experience || [])[idx] || {};
    setExpForm({
      title: item.title || '',
      company: item.company || '',
      location: item.location || '',
      start: item.start || '',
      end: item.end || '',
      description: item.description || '',
    });
    setEditingExpIndex(idx);
  };

  const handleSaveExp = () => {
    if (!expForm.title.trim()) {
      toast.error('Job Title is required');
      return;
    }
    if (!expForm.company.trim()) {
      toast.error('Company Name is required');
      return;
    }

    const currentExp = Array.isArray(profile.experience) ? [...profile.experience] : [];
    if (editingExpIndex === 'new') {
      currentExp.push(expForm);
      toast.success('Work experience entry added');
    } else if (typeof editingExpIndex === 'number') {
      currentExp[editingExpIndex] = expForm;
      toast.success('Work experience entry updated');
    }

    setProfile((prev: any) => ({ ...prev, experience: currentExp }));
    setEditingExpIndex(null);
  };

  const handleDeleteExp = (idx: number) => {
    const currentExp = Array.isArray(profile.experience) ? [...profile.experience] : [];
    currentExp.splice(idx, 1);
    setProfile((prev: any) => ({ ...prev, experience: currentExp }));
    toast.success('Work experience removed');
  };

  useEffect(() => {
    async function loadProfile() {
      try {
        const token = localStorage.getItem('access_token') || '';
        const [profileRes, resumesRes] = await Promise.all([
          fetch('http://localhost:8000/api/v1/profile/', {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch('http://localhost:8000/api/v1/resume/', {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        if (resumesRes.ok) {
          const resumes = await resumesRes.json();
          if (Array.isArray(resumes) && resumes.length > 0) {
            setUploadedFileName(resumes[0].filename);
            setLatestResume(resumes[0]);
          }
        }

        if (profileRes.ok) {
          const data = await profileRes.json();
          if (data) {
            setProfile({
              ...data,
              skills: Array.isArray(data.skills) ? data.skills : [],
              experience: Array.isArray(data.experience) ? data.experience : [],
              preferred_locations: Array.isArray(data.preferred_locations) ? data.preferred_locations : [],
            });
            if (typeof window !== 'undefined') {
              window.dispatchEvent(
                new CustomEvent('profile-status-changed', {
                  detail: {
                    is_verified: Boolean(data.is_verified),
                    skills: data.skills || [],
                  },
                })
              );
            }
          }
        }
      } catch {
        // Fallback
      }

      // If profile is fresh, populate with logged in user name and email
      const cached = localStorage.getItem('user');
      if (cached) {
        const u = JSON.parse(cached);
        setProfile((prev: any) => ({
          ...prev,
          full_name: prev.full_name || u.full_name || '',
          email: prev.email || u.email || '',
        }));
      }
    }
    loadProfile();
  }, []);

  const handleAddSkill = () => {
    if (newSkill.trim() && !(profile.skills || []).includes(newSkill.trim())) {
      setProfile({
        ...profile,
        skills: [...(profile.skills || []), newSkill.trim()],
      });
      setNewSkill('');
      if (fieldErrors.skills) {
        setFieldErrors((prev) => ({ ...prev, skills: '' }));
      }
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setProfile({
      ...profile,
      skills: (profile.skills || []).filter((s: string) => s !== skillToRemove),
    });
  };

  const handleSave = async () => {
    const errors: { [key: string]: string } = {};
    if (!profile.full_name?.trim()) {
      errors.full_name = 'Full name is required';
    }
    if (!profile.email?.trim()) {
      errors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email.trim())) {
      errors.email = 'Please enter a valid email address';
    }
    if (!profile.skills || profile.skills.length === 0) {
      errors.skills = 'Please add at least 1 verified technical skill';
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
        ...profile,
        total_experience_years:
          profile.total_experience_years !== '' && profile.total_experience_years !== null && profile.total_experience_years !== undefined
            ? Number(profile.total_experience_years)
            : 0,
        preferred_locations: Array.isArray(profile.preferred_locations) ? profile.preferred_locations : [],
      };

      const res = await fetch('http://localhost:8000/api/v1/profile/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error('Failed to update candidate profile');
      }

      await fetch('http://localhost:8000/api/v1/profile/verify', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });

      setProfile({ ...profile, is_verified: true });
      setSaveSuccess(true);

      // Immediately notify Header and entire app without needing page refresh
      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new CustomEvent('profile-status-changed', {
            detail: {
              is_verified: true,
              skills: profile.skills || [],
            },
          })
        );
      }

      toast.success('Profile verified and saved successfully! You can now run the Job Bot.');
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      toast.error(err.message || 'Error saving profile. Please check connection.');
    } finally {
      setSaving(false);
    }
  };

  const uploadFile = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(ext || '')) {
      toast.error('Unsupported file format. Please upload a PDF or DOCX file.');
      return;
    }

    setUploading(true);
    setUploadedFileName(file.name);
    toast.loading(`Extracting data from ${file.name}...`, { id: 'resume-upload' });
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/v1/resume/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUploadedFileName(data.filename || file.name);
        setLatestResume(data);
        if (data.parsed_data) {
          const parsed = data.parsed_data;
          setProfile((prev: any) => ({
            ...prev,
            full_name: parsed.full_name || prev.full_name,
            email: parsed.email || prev.email,
            phone: parsed.phone || prev.phone,
            location: parsed.location || prev.location,
            summary: parsed.summary || prev.summary,
            skills: parsed.skills && parsed.skills.length > 0 ? parsed.skills : (prev.skills || []),
            total_experience_years: parsed.total_experience_years !== null ? parsed.total_experience_years : prev.total_experience_years,
            experience: parsed.experience && parsed.experience.length > 0 ? parsed.experience : (prev.experience || []),
            education: parsed.education && parsed.education.length > 0 ? parsed.education : (prev.education || []),
          }));
          setFieldErrors({});
          const expCount = parsed.experience?.length || 0;
          const skillsCount = parsed.skills?.length || 0;
          toast.success(
            `Extracted ${skillsCount} skills and ${expCount} work experiences! Review and click Save & Confirm Verification.`,
            { id: 'resume-upload' }
          );
        } else {
          toast.success('Resume uploaded successfully! Please review details.', { id: 'resume-upload' });
        }
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Resume upload failed', { id: 'resume-upload' });
      }
    } catch {
      toast.error('Network error during file upload', { id: 'resume-upload' });
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      await uploadFile(file);
    }
  };

  return (
    <DashboardLayout title="Resume & Verified Candidate Profile">
      <div className="space-y-6 max-w-5xl">
        {/* Verification Alert Banner */}
        <div
          className={`p-4 sm:p-5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors ${
            profile.is_verified ? 'bg-emerald-50 border-emerald-200/80' : 'bg-amber-50 border-amber-200/80'
          }`}
        >
          <div className="space-y-1">
            <div
              className={`flex items-center gap-2 font-bold text-sm ${
                profile.is_verified ? 'text-emerald-950' : 'text-amber-950'
              }`}
            >
              <ShieldCheck className={`w-4 h-4 ${profile.is_verified ? 'text-emerald-600' : 'text-amber-600'}`} />
              <span>{profile.is_verified ? 'Strict Truthfulness Policy Active' : 'Action Required: Verification Pending'}</span>
            </div>
            <p
              className={`text-xs leading-relaxed max-w-2xl ${
                profile.is_verified ? 'text-emerald-800/80' : 'text-amber-800/80'
              }`}
            >
              {profile.is_verified
                ? 'Only verified candidate profile facts are utilized by the bot. Experience dates, employers, and skills will never be hallucinated or exaggerated during application tailoring.'
                : 'Upload your resume below. AI will automatically extract and display your verified skills. Click "Save & Confirm Verification" to enable the Job Bot.'}
            </p>
          </div>
          <Badge variant={profile.is_verified ? 'success' : 'warning'} size="md">
            {profile.is_verified ? 'Profile Verified' : 'Pending Verification'}
          </Badge>
        </div>

        {/* Upload Resume Box with HTML5 Drag & Drop */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle className="text-sm">Master Resume Upload</CardTitle>
              <p className="text-xs text-slate-500">
                Upload your latest PDF or DOCX resume. AI will automatically extract and display verified skills.
              </p>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Active Resume Status Card (Persists across refreshes) */}
            {uploadedFileName && !uploading && (
              <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-slate-900">{uploadedFileName}</span>
                      <Badge variant="success" size="sm">
                        Active Master Resume
                      </Badge>
                      {latestResume?.version && (
                        <Badge variant="outline" size="sm" className="text-slate-600 bg-white">
                          v{latestResume.version}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Stored on server • Used for AI matching and automated tailored applications
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {latestResume?.id && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(`http://localhost:8000/api/v1/resume/${latestResume.id}/download`, '_blank');
                      }}
                      className="cursor-pointer text-xs bg-white hover:bg-slate-50"
                      title="Download active resume"
                    >
                      <Download className="w-3.5 h-3.5 mr-1" />
                      <span>Download</span>
                    </Button>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    className="cursor-pointer text-xs bg-white text-indigo-700 border-indigo-200 hover:bg-indigo-50"
                    title="Upload a new resume"
                  >
                    <RefreshCw className="w-3.5 h-3.5 mr-1" />
                    <span>Upload New Resume</span>
                  </Button>
                </div>
              </div>
            )}

            {/* Drag & Drop Upload Zone */}
            <div
              onDragOver={handleDragOver}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-7 text-center cursor-pointer transition-all duration-200 ${
                isDragging
                  ? 'border-indigo-600 bg-indigo-50/70 scale-[1.01] shadow-md ring-4 ring-indigo-500/10'
                  : 'border-slate-200 hover:border-indigo-400 hover:bg-slate-50/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) uploadFile(file);
                }}
                className="hidden"
              />

              <div className="w-11 h-11 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-2.5">
                {uploading ? (
                  <Upload className="w-5 h-5 animate-bounce" />
                ) : uploadedFileName ? (
                  <FileCheck className="w-5 h-5 text-emerald-600" />
                ) : (
                  <Upload className="w-5 h-5" />
                )}
              </div>

              <p className="text-sm font-bold text-slate-800">
                {uploading
                  ? 'Analyzing & Extracting Skills with AI...'
                  : isDragging
                  ? 'Drop your resume file here now!'
                  : uploadedFileName
                  ? `Active File: ${uploadedFileName} (Click or Drop to replace)`
                  : 'Drag & Drop your resume file here, or click to browse'}
              </p>
              <p className="text-xs text-slate-400 mt-1">Supports PDF & DOCX formats (Up to 10MB)</p>

              <div className="mt-3">
                <span className="inline-flex items-center px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors pointer-events-none">
                  <Upload className="w-3.5 h-3.5 mr-1.5" />
                  {uploadedFileName ? 'Upload Different Resume' : 'Select File from Computer'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Verified Profile Form */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Candidate Information (Verified Profile)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <Input
                label="Full Name *"
                placeholder="e.g. John Doe"
                value={profile.full_name || ''}
                error={fieldErrors.full_name}
                onChange={(e) => {
                  setProfile({ ...profile, full_name: e.target.value });
                  if (fieldErrors.full_name) setFieldErrors({ ...fieldErrors, full_name: '' });
                }}
              />
              <Input
                label="Email *"
                type="email"
                placeholder="you@example.com"
                value={profile.email || ''}
                error={fieldErrors.email}
                onChange={(e) => {
                  setProfile({ ...profile, email: e.target.value });
                  if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: '' });
                }}
              />
              <Input
                label="Phone Number"
                placeholder="+91 9876543210"
                value={profile.phone || ''}
                onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
              />
              <LocationAutocomplete
                label="Current Location"
                placeholder="Type location (e.g. Chennai, Bengaluru)..."
                value={profile.location || ''}
                onChange={(loc) => setProfile({ ...profile, location: loc })}
              />
              <Input
                label="Total Experience (Years)"
                type="number"
                placeholder="e.g. 5"
                value={profile.total_experience_years !== null && profile.total_experience_years !== undefined ? profile.total_experience_years : ''}
                onChange={(e) => setProfile({ ...profile, total_experience_years: e.target.value })}
              />
              <Input
                label="LinkedIn URL"
                placeholder="https://linkedin.com/in/..."
                value={profile.linkedin_url || ''}
                onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
              />
              <Input
                label="GitHub URL"
                placeholder="https://github.com/..."
                value={profile.github_url || ''}
                onChange={(e) => setProfile({ ...profile, github_url: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Executive Professional Summary
              </label>
              <textarea
                rows={3}
                placeholder="Brief candidate summary..."
                value={profile.summary || ''}
                onChange={(e) => setProfile({ ...profile, summary: e.target.value })}
                className="w-full px-3.5 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
              />
            </div>

            {/* Skills Tag Management */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                Verified Technical Skills * ({profile.skills?.length || 0})
              </label>
              {fieldErrors.skills && (
                <p className="mb-2 text-xs text-red-600 font-semibold flex items-center gap-1.5">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-600 shrink-0"></span>
                  <span>{fieldErrors.skills}</span>
                </p>
              )}
              <div className="flex items-center gap-2 mb-3">
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSkill())}
                  placeholder="Type a skill and press Enter..."
                  className="px-3.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
                <Button variant="outline" size="sm" onClick={handleAddSkill}>
                  <Plus className="w-3.5 h-3.5 mr-1" />
                  <span>Add Skill</span>
                </Button>
              </div>

              <div className="flex items-center gap-1.5 flex-wrap">
                {(profile.skills || []).map((skill: string) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-800 border border-indigo-200/60"
                  >
                    <span>{skill}</span>
                    <button
                      onClick={() => handleRemoveSkill(skill)}
                      className="text-indigo-400 hover:text-indigo-700"
                      aria-label={`Remove skill ${skill}`}
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Work Experience History */}
            <div className="pt-4 border-t border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-indigo-600" />
                  <label className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                    Work Experience History ({profile.experience?.length || 0})
                  </label>
                </div>
                {editingExpIndex === null && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleStartAddExp}
                    className="cursor-pointer text-xs"
                  >
                    <Plus className="w-3.5 h-3.5 mr-1" />
                    <span>Add Experience</span>
                  </Button>
                )}
              </div>

              {/* Add / Edit Experience Form */}
              {editingExpIndex !== null && (
                <div className="p-4 mb-4 rounded-xl bg-slate-50 border-2 border-indigo-200/80 space-y-3.5 shadow-sm">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                      {editingExpIndex === 'new' ? 'Add New Work Experience' : 'Edit Work Experience'}
                    </span>
                    <button
                      type="button"
                      onClick={() => setEditingExpIndex(null)}
                      className="text-slate-400 hover:text-slate-600 cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Job Title / Role *
                      </label>
                      <Input
                        type="text"
                        placeholder="e.g. Front End Developer"
                        value={expForm.title}
                        onChange={(e) => setExpForm({ ...expForm, title: e.target.value })}
                        className="text-xs bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Company Name *
                      </label>
                      <Input
                        type="text"
                        placeholder="e.g. LegalOptix Private Limited"
                        value={expForm.company}
                        onChange={(e) => setExpForm({ ...expForm, company: e.target.value })}
                        className="text-xs bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Location
                      </label>
                      <Input
                        type="text"
                        placeholder="e.g. Chennai, India"
                        value={expForm.location}
                        onChange={(e) => setExpForm({ ...expForm, location: e.target.value })}
                        className="text-xs bg-white"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          Start Date
                        </label>
                        <Input
                          type="text"
                          placeholder="e.g. Feb 2026"
                          value={expForm.start}
                          onChange={(e) => setExpForm({ ...expForm, start: e.target.value })}
                          className="text-xs bg-white"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          End Date
                        </label>
                        <Input
                          type="text"
                          placeholder="e.g. Present"
                          value={expForm.end}
                          onChange={(e) => setExpForm({ ...expForm, end: e.target.value })}
                          className="text-xs bg-white"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Responsibilities & Highlights
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Describe key responsibilities, features developed, and technical impact..."
                      value={expForm.description}
                      onChange={(e) => setExpForm({ ...expForm, description: e.target.value })}
                      className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditingExpIndex(null)}
                      className="cursor-pointer text-xs"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      onClick={handleSaveExp}
                      className="cursor-pointer text-xs"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                      <span>{editingExpIndex === 'new' ? 'Add Entry' : 'Update Entry'}</span>
                    </Button>
                  </div>
                </div>
              )}

              {/* Experience List Cards */}
              {(!profile.experience || profile.experience.length === 0) && editingExpIndex === null ? (
                <div className="p-6 text-center rounded-xl border border-dashed border-slate-300 bg-slate-50/60">
                  <Briefcase className="w-8 h-8 text-slate-400 mx-auto mb-2 opacity-60" />
                  <p className="text-xs font-semibold text-slate-700">No work experience entries added yet</p>
                  <p className="text-[11px] text-slate-500 mt-0.5 mb-3">
                    Upload your resume to extract automatically, or add your work experience manually.
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleStartAddExp}
                    className="cursor-pointer text-xs"
                  >
                    <Plus className="w-3.5 h-3.5 mr-1" />
                    <span>Add First Experience</span>
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {(profile.experience || []).map((exp: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 hover:border-slate-300 transition-colors space-y-2 group"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-bold text-slate-900">{exp.title}</span>
                            <Badge variant="outline" size="sm" className="font-medium text-[11px]">
                              {exp.start || 'N/A'} - {exp.end || 'Present'}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-indigo-700 font-semibold">
                            <Building2 className="w-3.5 h-3.5 shrink-0" />
                            <span>{exp.company}</span>
                            {exp.location && (
                              <>
                                <span className="text-slate-300">•</span>
                                <span className="text-slate-500 font-normal">{exp.location}</span>
                              </>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            type="button"
                            onClick={() => handleStartEditExp(idx)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-white transition-colors cursor-pointer"
                            title="Edit Experience"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteExp(idx)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-white transition-colors cursor-pointer"
                            title="Delete Experience"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {exp.description && (
                        <p className="text-xs text-slate-600 leading-relaxed pt-1.5 border-t border-slate-200/50">
                          {exp.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Save & Verify Button */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              {saveSuccess && (
                <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  Profile saved and verified successfully!
                </span>
              )}
              {!saveSuccess && <span></span>}

              <Button variant="primary" size="md" loading={saving} onClick={handleSave}>
                <Save className="w-4 h-4 mr-1.5" />
                <span>Save & Confirm Verification</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
