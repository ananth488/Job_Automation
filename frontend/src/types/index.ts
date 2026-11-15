// ============================================================
// TypeScript types matching the backend schemas
// ============================================================

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Resume {
  id: string;
  user_id: string;
  filename: string;
  file_path: string;
  version: number;
  is_primary: boolean;
  parsed_data: Record<string, unknown> | null;
  uploaded_at: string;
}

export interface Experience {
  company: string;
  title: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string;
  location: string;
}

export interface Education {
  institution: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date: string | null;
  gpa: string | null;
}

export interface Certification {
  name: string;
  issuer: string;
  date_obtained: string;
  expiry_date: string | null;
  credential_id: string | null;
}

export interface Project {
  name: string;
  description: string;
  technologies: string[];
  url: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface CandidateProfile {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  phone: string;
  location: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  summary: string;
  skills: string[];
  experience: Experience[];
  education: Education[];
  certifications: Certification[];
  projects: Project[];
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface Preference {
  id: string;
  user_id: string;
  desired_roles: string[];
  keywords: string[];
  locations: string[];
  work_mode: 'remote' | 'hybrid' | 'onsite' | 'any';
  min_salary: number | null;
  max_salary: number | null;
  min_experience: number | null;
  max_experience: number | null;
  notice_period: string | null;
  preferred_companies: string[];
  blocked_companies: string[];
  job_types: string[];
  match_threshold: number;
  daily_application_limit: number;
  approval_mode: 'auto' | 'manual' | 'threshold';
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: string;
  external_id: string;
  platform: string;
  title: string;
  company: string;
  location: string;
  work_mode: 'remote' | 'hybrid' | 'onsite';
  description: string;
  requirements: string[];
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  job_type: string;
  experience_level: string;
  skills: string[];
  url: string;
  posted_date: string;
  expires_date: string | null;
  is_active: boolean;
  scraped_at: string;
  created_at: string;
}

export interface MatchBreakdown {
  skills: number;
  experience: number;
  location: number;
  salary: number;
  role_fit: number;
}

export interface JobMatch {
  id: string;
  job_id: string;
  user_id: string;
  job: Job;
  overall_score: number;
  breakdown: MatchBreakdown;
  matched_skills: string[];
  missing_skills: string[];
  ai_explanation: string;
  status: 'pending' | 'approved' | 'rejected' | 'applied' | 'skipped';
  created_at: string;
}

export interface ApplicationStatusHistory {
  status: string;
  timestamp: string;
  notes: string | null;
}

export interface Application {
  id: string;
  user_id: string;
  job_id: string;
  job_match_id: string;
  job: Job;
  match_score: number;
  status: 'pending' | 'applied' | 'viewed' | 'interview' | 'offer' | 'rejected' | 'withdrawn';
  method: 'auto' | 'manual';
  applied_at: string | null;
  resume_used: string | null;
  cover_letter: string | null;
  screening_answers: Record<string, string> | null;
  notes: string;
  status_history: ApplicationStatusHistory[];
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  type: 'interview' | 'approval' | 'summary' | 'status_change' | 'bot_update' | 'system';
  title: string;
  message: string;
  is_read: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface BotSettings {
  id: string;
  user_id: string;
  is_enabled: boolean;
  schedule: string;
  platforms: string[];
  daily_limit: number;
  auto_apply: boolean;
  match_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface BotRun {
  id: string;
  user_id: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  jobs_found: number;
  jobs_matched: number;
  jobs_applied: number;
  errors: string[];
  log: string;
}

export interface DashboardStats {
  total_jobs_found: number;
  applications_sent: number;
  interviews: number;
  pending_approval: number;
  jobs_found_trend: number;
  applications_trend: number;
  interviews_trend: number;
  approval_trend: number;
}

export interface ChartData {
  applications_over_time: { date: string; count: number }[];
  score_distribution: { range: string; count: number }[];
  jobs_by_platform: { platform: string; count: number }[];
}

export interface RecentActivity {
  id: string;
  type: 'application' | 'match' | 'bot_run' | 'interview' | 'status_change';
  title: string;
  description: string;
  timestamp: string;
}

export type PageParams<T extends Record<string, string> = Record<string, string>> = {
  params: Promise<T>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};
