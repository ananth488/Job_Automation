# 🤖 AI Job Application Bot (Naukri.com + Indeed.com)

A personal, production-ready AI job-search assistant that automatically searches, matches, tailors resumes, and assists application submissions for opportunities on **Naukri.com** and **Indeed.com** based on a candidate's verified resume profile.

---

## 🌟 Key Highlights & Architecture

- **Frontend:** Next.js 16 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Mobile-First Responsive Design
- **Backend:** Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0 ORM, SQLite / PostgreSQL
- **AI Matching Engine:** Multi-dimensional scoring (Skills 35%, Experience 20%, Role Fit 20%, Location 15%, Salary 10%)
- **Tailoring Engine & Truthfulness Validator:** Generates job-specific resume summaries and cover letters, ensuring zero hallucinated experience or fabricated skills
- **Compliance Guard:** Adheres strictly to Naukri and Indeed policies; features a candidate **Approval Queue** with copy-ready pre-filled screening answers and assisted manual submission workflows
- **Background Scheduler:** APScheduler background worker with run-interval controls, platform enablement toggles, and execution logs

---

## 📸 Application Pages & UI Experience

| Page | URL | Description |
|---|---|---|
| **Login** | `/login` | Centered modern login with preloaded credentials (`demo@jobbot.com` / `password123`) |
| **Dashboard** | `/dashboard` | High-level metrics, KPI trend cards, AI matched jobs preview, and quick run controls |
| **Job Discovery** | `/jobs` | Filterable list with match scores, platform badges, salary ranges, and skills tags |
| **Job Detail & Match** | `/jobs/[id]` | Full job description, multi-dimensional score breakdown, and "Add to Queue" action |
| **Approval Queue** | `/approval-queue` | Review generated resumes, cover letters, copy screening answers, and approve/skip |
| **Applications** | `/applications` | Pipeline tracking across stages (Pending Review → Applied → Interview → Offer) |
| **Resume & Profile** | `/profile` | PDF/DOCX master resume upload, AI structured extraction, and verified profile form |
| **Preferences** | `/preferences` | Target roles, keywords, salary range, experience, match threshold (e.g. 75%), daily limits |
| **Bot Controls** | `/bot-controls` | Start / Pause / Stop controls, platform toggles, and live terminal execution stream |
| **Notifications** | `/notifications` | Interview alerts, approval notifications, and daily cycle summaries |
| **Settings** | `/settings` | AI provider configuration, notification email preferences, and security policies |

---

## 🚀 Quick Start Guide

### Option 1: Local Development

#### 1. Start the Backend API (FastAPI)
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
- Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### 2. Start the Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
- Open [http://localhost:3000](http://localhost:3000) in your browser.
- Demo Login: **`demo@jobbot.com`** / **`password123`**

---

### Option 2: Docker Compose
```bash
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

---

## 🔒 Compliance & Non-Negotiable Rules

1. **Permitted Access Only:** Platform adapters query authorized job feeds and permitted endpoints.
2. **Capability Layer:** Every platform adapter implements `can_search` and `can_auto_apply`. Because platforms like Naukri and Indeed restrict automated submission, `can_auto_apply` is set to `False`, systematically routing applications into the **Approval Queue** for candidate-assisted submission.
3. **Strict Truthfulness Check:** AI tailoring diffs generated documents against the candidate's verified profile. Fabricating skills or dates is blocked.
4. **Rate Limiting & Politeness:** Request limits and polite delays prevent account flags or rate limiting.
