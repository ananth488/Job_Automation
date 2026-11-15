import type {
  DashboardStats,
  ChartData,
  RecentActivity,
  Job,
  JobMatch,
  Application,
  CandidateProfile,
  Preference,
  BotSettings,
  BotRun,
  Notification,
  Resume,
} from '@/types';

export const mockStats: DashboardStats = {
  total_jobs_found: 1247,
  applications_sent: 89,
  interviews: 12,
  pending_approval: 23,
  jobs_found_trend: 15.2,
  applications_trend: 8.5,
  interviews_trend: 33.3,
  approval_trend: -5.0,
};

export const mockCharts: ChartData = {
  applications_over_time: [
    { date: '2024-01-01', count: 5 },
    { date: '2024-01-08', count: 8 },
    { date: '2024-01-15', count: 12 },
    { date: '2024-01-22', count: 7 },
    { date: '2024-01-29', count: 15 },
    { date: '2024-02-05', count: 11 },
    { date: '2024-02-12', count: 18 },
    { date: '2024-02-19', count: 13 },
  ],
  score_distribution: [
    { range: '0-20', count: 5 },
    { range: '21-40', count: 12 },
    { range: '41-60', count: 28 },
    { range: '61-80', count: 45 },
    { range: '81-100', count: 32 },
  ],
  jobs_by_platform: [
    { platform: 'LinkedIn', count: 450 },
    { platform: 'Indeed', count: 320 },
    { platform: 'Glassdoor', count: 180 },
    { platform: 'Naukri', count: 150 },
    { platform: 'ZipRecruiter', count: 147 },
  ],
};

export const mockRecentActivity: RecentActivity[] = [
  { id: '1', type: 'application', title: 'Applied to Senior Frontend Developer', description: 'Auto-applied at Google via LinkedIn', timestamp: new Date(Date.now() - 1800000).toISOString() },
  { id: '2', type: 'interview', title: 'Interview Scheduled', description: 'Meta - Full Stack Engineer - Tomorrow at 2:00 PM', timestamp: new Date(Date.now() - 7200000).toISOString() },
  { id: '3', type: 'match', title: 'New High Match Found', description: 'Staff Engineer at Netflix - 95% match', timestamp: new Date(Date.now() - 14400000).toISOString() },
  { id: '4', type: 'bot_run', title: 'Bot Run Completed', description: 'Found 23 jobs, matched 8, applied to 3', timestamp: new Date(Date.now() - 28800000).toISOString() },
  { id: '5', type: 'status_change', title: 'Application Viewed', description: 'Amazon - Backend Developer application was viewed', timestamp: new Date(Date.now() - 43200000).toISOString() },
  { id: '6', type: 'application', title: 'Applied to React Developer', description: 'Applied at Stripe via Glassdoor', timestamp: new Date(Date.now() - 86400000).toISOString() },
];

const baseJob = (id: string, overrides: Partial<Job> = {}): Job => ({
  id,
  external_id: `ext_${id}`,
  platform: 'LinkedIn',
  title: 'Senior Frontend Developer',
  company: 'TechCorp',
  location: 'San Francisco, CA',
  work_mode: 'remote',
  description: 'We are looking for a Senior Frontend Developer to join our team and help build amazing user experiences. You will work with React, TypeScript, and modern web technologies to deliver high-quality applications.',
  requirements: ['5+ years React experience', 'TypeScript proficiency', 'CSS/Tailwind expertise', 'REST API integration', 'Git version control'],
  salary_min: 150000,
  salary_max: 200000,
  salary_currency: 'USD',
  job_type: 'full-time',
  experience_level: 'senior',
  skills: ['React', 'TypeScript', 'Next.js', 'Tailwind CSS', 'Node.js', 'GraphQL', 'REST APIs', 'Git'],
  url: 'https://example.com/job/1',
  posted_date: new Date(Date.now() - 86400000 * 2).toISOString(),
  expires_date: null,
  is_active: true,
  scraped_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
  ...overrides,
});

export const mockJobs: Job[] = [
  baseJob('1', { title: 'Senior Frontend Developer', company: 'Google', location: 'Mountain View, CA', platform: 'LinkedIn', salary_min: 180000, salary_max: 250000 }),
  baseJob('2', { title: 'Full Stack Engineer', company: 'Meta', location: 'Menlo Park, CA', work_mode: 'hybrid', platform: 'Indeed', salary_min: 170000, salary_max: 230000 }),
  baseJob('3', { title: 'Staff Software Engineer', company: 'Netflix', location: 'Los Gatos, CA', platform: 'Glassdoor', salary_min: 200000, salary_max: 300000 }),
  baseJob('4', { title: 'React Developer', company: 'Stripe', location: 'Remote', platform: 'LinkedIn', salary_min: 140000, salary_max: 190000 }),
  baseJob('5', { title: 'Frontend Architect', company: 'Airbnb', location: 'San Francisco, CA', work_mode: 'hybrid', platform: 'LinkedIn', salary_min: 190000, salary_max: 260000 }),
  baseJob('6', { title: 'UI Engineer', company: 'Figma', location: 'San Francisco, CA', platform: 'Glassdoor', salary_min: 160000, salary_max: 220000, skills: ['React', 'TypeScript', 'Canvas API', 'WebGL', 'CSS'] }),
  baseJob('7', { title: 'Backend Developer', company: 'Amazon', location: 'Seattle, WA', work_mode: 'onsite', platform: 'Indeed', salary_min: 155000, salary_max: 210000, skills: ['Python', 'AWS', 'Docker', 'Kubernetes', 'PostgreSQL'] }),
  baseJob('8', { title: 'DevOps Engineer', company: 'Datadog', location: 'New York, NY', platform: 'LinkedIn', salary_min: 165000, salary_max: 225000, skills: ['Terraform', 'AWS', 'Docker', 'Kubernetes', 'CI/CD'] }),
];

export const mockJobMatches: JobMatch[] = mockJobs.map((job, i) => ({
  id: `match_${job.id}`,
  job_id: job.id,
  user_id: 'user_1',
  job,
  overall_score: [92, 87, 95, 78, 88, 72, 45, 55][i],
  breakdown: { skills: [90, 85, 95, 75, 88, 70, 40, 50][i], experience: [95, 88, 96, 80, 90, 75, 50, 60][i], location: [90, 85, 100, 100, 85, 90, 70, 80][i], salary: [92, 90, 88, 78, 86, 72, 45, 55][i], role_fit: [93, 87, 96, 77, 90, 73, 42, 53][i] },
  matched_skills: ['React', 'TypeScript', 'Next.js', 'Tailwind CSS', 'Git'],
  missing_skills: i < 3 ? ['GraphQL'] : ['GraphQL', 'Node.js', 'Docker'],
  ai_explanation: `This role at ${job.company} is a strong match based on your experience with React and TypeScript. Your portfolio demonstrates relevant project work that aligns well with their requirements.`,
  status: i < 3 ? 'pending' : (['approved', 'applied', 'rejected', 'skipped', 'pending'][i - 3] as JobMatch['status']),
  created_at: new Date(Date.now() - 86400000 * i).toISOString(),
}));

export const mockApplications: Application[] = [
  { id: 'app_1', user_id: 'user_1', job_id: '1', job_match_id: 'match_1', job: mockJobs[0], match_score: 92, status: 'interview', method: 'auto', applied_at: new Date(Date.now() - 86400000 * 5).toISOString(), resume_used: 'resume_v3.pdf', cover_letter: 'Dear Hiring Manager, I am excited to apply for the Senior Frontend Developer role at Google...', screening_answers: { 'Years of experience?': '7 years', 'Willing to relocate?': 'Yes' }, notes: 'Great opportunity - matches career goals', status_history: [{ status: 'pending', timestamp: new Date(Date.now() - 86400000 * 6).toISOString(), notes: null }, { status: 'applied', timestamp: new Date(Date.now() - 86400000 * 5).toISOString(), notes: 'Auto-applied' }, { status: 'viewed', timestamp: new Date(Date.now() - 86400000 * 3).toISOString(), notes: null }, { status: 'interview', timestamp: new Date(Date.now() - 86400000).toISOString(), notes: 'Phone screen scheduled' }], created_at: new Date(Date.now() - 86400000 * 6).toISOString(), updated_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'app_2', user_id: 'user_1', job_id: '2', job_match_id: 'match_2', job: mockJobs[1], match_score: 87, status: 'applied', method: 'auto', applied_at: new Date(Date.now() - 86400000 * 3).toISOString(), resume_used: 'resume_v3.pdf', cover_letter: 'Dear Hiring Manager, I am excited about the Full Stack Engineer position at Meta...', screening_answers: null, notes: '', status_history: [{ status: 'pending', timestamp: new Date(Date.now() - 86400000 * 4).toISOString(), notes: null }, { status: 'applied', timestamp: new Date(Date.now() - 86400000 * 3).toISOString(), notes: 'Auto-applied' }], created_at: new Date(Date.now() - 86400000 * 4).toISOString(), updated_at: new Date(Date.now() - 86400000 * 3).toISOString() },
  { id: 'app_3', user_id: 'user_1', job_id: '4', job_match_id: 'match_4', job: mockJobs[3], match_score: 78, status: 'viewed', method: 'manual', applied_at: new Date(Date.now() - 86400000 * 7).toISOString(), resume_used: 'resume_v2.pdf', cover_letter: null, screening_answers: null, notes: 'Applied manually through website', status_history: [{ status: 'applied', timestamp: new Date(Date.now() - 86400000 * 7).toISOString(), notes: null }, { status: 'viewed', timestamp: new Date(Date.now() - 86400000 * 2).toISOString(), notes: null }], created_at: new Date(Date.now() - 86400000 * 7).toISOString(), updated_at: new Date(Date.now() - 86400000 * 2).toISOString() },
  { id: 'app_4', user_id: 'user_1', job_id: '5', job_match_id: 'match_5', job: mockJobs[4], match_score: 88, status: 'offer', method: 'auto', applied_at: new Date(Date.now() - 86400000 * 14).toISOString(), resume_used: 'resume_v3.pdf', cover_letter: 'Dear Hiring Manager...', screening_answers: null, notes: 'Received offer!', status_history: [{ status: 'applied', timestamp: new Date(Date.now() - 86400000 * 14).toISOString(), notes: null }, { status: 'viewed', timestamp: new Date(Date.now() - 86400000 * 12).toISOString(), notes: null }, { status: 'interview', timestamp: new Date(Date.now() - 86400000 * 7).toISOString(), notes: 'Technical round' }, { status: 'offer', timestamp: new Date(Date.now() - 86400000).toISOString(), notes: '$250k TC' }], created_at: new Date(Date.now() - 86400000 * 14).toISOString(), updated_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'app_5', user_id: 'user_1', job_id: '7', job_match_id: 'match_7', job: mockJobs[6], match_score: 45, status: 'rejected', method: 'auto', applied_at: new Date(Date.now() - 86400000 * 10).toISOString(), resume_used: 'resume_v2.pdf', cover_letter: null, screening_answers: null, notes: '', status_history: [{ status: 'applied', timestamp: new Date(Date.now() - 86400000 * 10).toISOString(), notes: null }, { status: 'rejected', timestamp: new Date(Date.now() - 86400000 * 4).toISOString(), notes: 'Position filled' }], created_at: new Date(Date.now() - 86400000 * 10).toISOString(), updated_at: new Date(Date.now() - 86400000 * 4).toISOString() },
  { id: 'app_6', user_id: 'user_1', job_id: '3', job_match_id: 'match_3', job: mockJobs[2], match_score: 95, status: 'pending', method: 'auto', applied_at: null, resume_used: null, cover_letter: null, screening_answers: null, notes: '', status_history: [{ status: 'pending', timestamp: new Date(Date.now() - 3600000).toISOString(), notes: null }], created_at: new Date(Date.now() - 3600000).toISOString(), updated_at: new Date(Date.now() - 3600000).toISOString() },
];

export const mockProfile: CandidateProfile = {
  id: 'profile_1',
  user_id: 'user_1',
  full_name: 'Alex Johnson',
  email: 'alex.johnson@email.com',
  phone: '+1 (555) 123-4567',
  location: 'San Francisco, CA',
  linkedin_url: 'https://linkedin.com/in/alexjohnson',
  github_url: 'https://github.com/alexjohnson',
  portfolio_url: 'https://alexjohnson.dev',
  summary: 'Senior Frontend Developer with 7+ years of experience building scalable web applications. Passionate about user experience, performance optimization, and modern JavaScript frameworks.',
  skills: ['React', 'TypeScript', 'Next.js', 'Tailwind CSS', 'Node.js', 'Python', 'PostgreSQL', 'MongoDB', 'Docker', 'AWS', 'Git', 'CI/CD', 'GraphQL', 'REST APIs', 'Agile'],
  experience: [
    { company: 'TechStartup Inc.', title: 'Senior Frontend Developer', start_date: '2022-01-01', end_date: null, is_current: true, description: 'Lead frontend development for a SaaS platform serving 50k+ users. Implemented micro-frontend architecture, reducing build times by 60%.', location: 'San Francisco, CA' },
    { company: 'Digital Agency Co.', title: 'Frontend Developer', start_date: '2019-06-01', end_date: '2021-12-31', is_current: false, description: 'Developed responsive web applications for enterprise clients using React and TypeScript.', location: 'New York, NY' },
    { company: 'WebDev Studio', title: 'Junior Developer', start_date: '2017-03-01', end_date: '2019-05-31', is_current: false, description: 'Built and maintained client websites using modern web technologies.', location: 'Austin, TX' },
  ],
  education: [
    { institution: 'Stanford University', degree: 'Master of Science', field_of_study: 'Computer Science', start_date: '2015-09-01', end_date: '2017-06-01', gpa: '3.9' },
    { institution: 'UC Berkeley', degree: 'Bachelor of Science', field_of_study: 'Computer Science', start_date: '2011-09-01', end_date: '2015-06-01', gpa: '3.7' },
  ],
  certifications: [
    { name: 'AWS Certified Developer', issuer: 'Amazon Web Services', date_obtained: '2023-06-01', expiry_date: '2026-06-01', credential_id: 'AWS-DEV-12345' },
    { name: 'Google Cloud Professional', issuer: 'Google', date_obtained: '2022-09-01', expiry_date: null, credential_id: 'GCP-PRO-67890' },
  ],
  projects: [
    { name: 'E-Commerce Platform', description: 'Full-stack e-commerce platform with real-time inventory management', technologies: ['React', 'Node.js', 'MongoDB', 'Stripe'], url: 'https://github.com/alexjohnson/ecommerce', start_date: '2023-01-01', end_date: '2023-06-01' },
    { name: 'Task Management App', description: 'Collaborative task management tool with real-time updates', technologies: ['Next.js', 'TypeScript', 'PostgreSQL', 'WebSocket'], url: 'https://github.com/alexjohnson/taskapp', start_date: '2022-06-01', end_date: '2022-12-01' },
  ],
  is_verified: true,
  created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
  updated_at: new Date(Date.now() - 86400000 * 2).toISOString(),
};

export const mockPreferences: Preference = {
  id: 'pref_1',
  user_id: 'user_1',
  desired_roles: ['Senior Frontend Developer', 'Staff Engineer', 'Full Stack Developer', 'Frontend Architect'],
  keywords: ['React', 'TypeScript', 'Next.js', 'Frontend'],
  locations: ['San Francisco, CA', 'New York, NY', 'Remote'],
  work_mode: 'remote',
  min_salary: 150000,
  max_salary: 300000,
  min_experience: 5,
  max_experience: 10,
  notice_period: '2 weeks',
  preferred_companies: ['Google', 'Meta', 'Netflix', 'Stripe', 'Airbnb'],
  blocked_companies: ['OldTech Corp'],
  job_types: ['full-time'],
  match_threshold: 70,
  daily_application_limit: 10,
  approval_mode: 'threshold',
  created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
  updated_at: new Date(Date.now() - 86400000 * 2).toISOString(),
};

export const mockBotSettings: BotSettings = {
  id: 'bot_1',
  user_id: 'user_1',
  is_enabled: true,
  schedule: '0 9 * * 1-5',
  platforms: ['LinkedIn', 'Indeed', 'Glassdoor'],
  daily_limit: 10,
  auto_apply: true,
  match_threshold: 70,
  created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
  updated_at: new Date(Date.now() - 86400000).toISOString(),
};

export const mockBotRuns: BotRun[] = [
  { id: 'run_1', user_id: 'user_1', status: 'completed', started_at: new Date(Date.now() - 3600000).toISOString(), completed_at: new Date(Date.now() - 1800000).toISOString(), duration_seconds: 1800, jobs_found: 23, jobs_matched: 8, jobs_applied: 3, errors: [], log: '[09:00:00] Bot started\n[09:00:05] Scanning LinkedIn...\n[09:10:00] Found 15 jobs on LinkedIn\n[09:10:30] Scanning Indeed...\n[09:18:00] Found 8 jobs on Indeed\n[09:18:30] Running match analysis...\n[09:25:00] 8 jobs matched (threshold: 70%)\n[09:25:30] Auto-applying to 3 jobs...\n[09:30:00] Bot completed successfully' },
  { id: 'run_2', user_id: 'user_1', status: 'completed', started_at: new Date(Date.now() - 86400000).toISOString(), completed_at: new Date(Date.now() - 86400000 + 2400000).toISOString(), duration_seconds: 2400, jobs_found: 31, jobs_matched: 12, jobs_applied: 5, errors: [], log: 'Bot run completed successfully' },
  { id: 'run_3', user_id: 'user_1', status: 'failed', started_at: new Date(Date.now() - 86400000 * 2).toISOString(), completed_at: new Date(Date.now() - 86400000 * 2 + 600000).toISOString(), duration_seconds: 600, jobs_found: 5, jobs_matched: 0, jobs_applied: 0, errors: ['LinkedIn rate limit exceeded', 'Session expired'], log: '[09:00:00] Bot started\n[09:05:00] LinkedIn rate limit hit\n[09:10:00] Bot stopped due to errors' },
  { id: 'run_4', user_id: 'user_1', status: 'completed', started_at: new Date(Date.now() - 86400000 * 3).toISOString(), completed_at: new Date(Date.now() - 86400000 * 3 + 1500000).toISOString(), duration_seconds: 1500, jobs_found: 18, jobs_matched: 6, jobs_applied: 4, errors: [], log: 'Bot run completed successfully' },
];

export const mockNotifications: Notification[] = [
  { id: 'notif_1', user_id: 'user_1', type: 'interview', title: 'Interview Scheduled!', message: 'Your interview with Google for Senior Frontend Developer is scheduled for tomorrow at 2:00 PM PST.', is_read: false, metadata: { job_id: '1', application_id: 'app_1' }, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 'notif_2', user_id: 'user_1', type: 'approval', title: 'New Jobs Need Approval', message: '5 new job matches are waiting for your review. Highest match: Staff Engineer at Netflix (95%).', is_read: false, metadata: null, created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: 'notif_3', user_id: 'user_1', type: 'summary', title: 'Daily Summary', message: 'Today\'s bot run found 23 jobs, matched 8, and auto-applied to 3. View details for more information.', is_read: false, metadata: { run_id: 'run_1' }, created_at: new Date(Date.now() - 14400000).toISOString() },
  { id: 'notif_4', user_id: 'user_1', type: 'status_change', title: 'Application Viewed', message: 'Your application for React Developer at Stripe has been viewed by the hiring team.', is_read: true, metadata: { application_id: 'app_3' }, created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'notif_5', user_id: 'user_1', type: 'bot_update', title: 'Bot Run Completed', message: 'Daily bot run completed successfully. Applied to 5 new positions.', is_read: true, metadata: { run_id: 'run_2' }, created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'notif_6', user_id: 'user_1', type: 'system', title: 'Profile Verified', message: 'Your candidate profile has been verified successfully. You\'re all set for auto-applications!', is_read: true, metadata: null, created_at: new Date(Date.now() - 86400000 * 3).toISOString() },
  { id: 'notif_7', user_id: 'user_1', type: 'interview', title: 'Interview Reminder', message: 'Reminder: You have an interview with Airbnb tomorrow at 10:00 AM PST.', is_read: true, metadata: null, created_at: new Date(Date.now() - 86400000 * 5).toISOString() },
];

export const mockResumes: Resume[] = [
  { id: 'resume_1', user_id: 'user_1', filename: 'Alex_Johnson_Resume_v3.pdf', file_path: '/uploads/resume_v3.pdf', version: 3, is_primary: true, parsed_data: null, uploaded_at: new Date(Date.now() - 86400000 * 2).toISOString() },
  { id: 'resume_2', user_id: 'user_1', filename: 'Alex_Johnson_Resume_v2.pdf', file_path: '/uploads/resume_v2.pdf', version: 2, is_primary: false, parsed_data: null, uploaded_at: new Date(Date.now() - 86400000 * 15).toISOString() },
  { id: 'resume_3', user_id: 'user_1', filename: 'Alex_Johnson_Resume_v1.pdf', file_path: '/uploads/resume_v1.pdf', version: 1, is_primary: false, parsed_data: null, uploaded_at: new Date(Date.now() - 86400000 * 30).toISOString() },
];
