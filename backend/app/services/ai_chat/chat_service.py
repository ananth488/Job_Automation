"""AI Career Copilot & Universal Chat Service.

Connects to Google Gemini API (gemini-2.0-flash / gemini-1.5-flash) with
live database context injection (today's jobs, applications, approval queue,
candidate profile, and bot status).
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import logging
import os
import re
from typing import Any

import httpx
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import (
    User,
    CandidateProfile,
    Preference,
    Job,
    JobMatch,
    Application,
    BotSettings,
    BotRun,
)

logger = logging.getLogger(__name__)


class AIChatService:
    """Universal AI Chat service backed by Gemini API with live DB state."""

    def __init__(self):
        self.gemini_model = "gemini-2.0-flash"
        self.fallback_model = "gemini-1.5-flash"

    def _get_api_key(self) -> str:
        """Resolve Gemini API key from settings or OS environment."""
        key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        return key.strip()

    def gather_live_context(self, user: User, db: Session) -> dict[str, Any]:
        """Fetch live candidate profile, statistics, and top jobs for real-time awareness."""
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

        # 1. Profile
        profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user.id))
        user_skills = profile.skills if profile and profile.skills else []
        experiences = profile.experience if profile and profile.experience else []
        role_title = experiences[0].get("title", "Frontend Developer") if experiences else "Developer"

        # 2. Preferences
        pref = db.scalar(select(Preference).where(Preference.user_id == user.id))

        # 3. Bot Settings & Status
        bot_settings = db.scalar(select(BotSettings).where(BotSettings.user_id == user.id))
        latest_run = db.scalar(
            select(BotRun).where(BotRun.user_id == user.id).order_by(desc(BotRun.started_at))
        )

        # 4. Job & Application Counts
        total_jobs_found = db.scalar(select(func.count(Job.id))) or 0
        total_shortlisted = db.scalar(
            select(func.count(JobMatch.id)).where(
                (JobMatch.user_id == user.id) & (JobMatch.status == "shortlisted")
            )
        ) or 0
        total_applications = db.scalar(
            select(func.count(Application.id)).where(Application.user_id == user.id)
        ) or 0
        applications_sent = db.scalar(
            select(func.count(Application.id)).where(
                (Application.user_id == user.id) & (Application.status == "applied")
            )
        ) or 0
        applications_sent_today = db.scalar(
            select(func.count(Application.id)).where(
                (Application.user_id == user.id)
                & (Application.status == "applied")
                & (Application.submitted_at >= today_start)
            )
        ) or 0
        pending_approval = db.scalar(
            select(func.count(Application.id)).where(
                (Application.user_id == user.id) & (Application.status == "pending_approval")
            )
        ) or 0

        # Latest jobs in Approval Queue
        pending_apps = db.scalars(
            select(Application)
            .where((Application.user_id == user.id) & (Application.status == "pending_approval"))
            .order_by(desc(Application.created_at))
            .limit(5)
        ).all()

        queue_preview: list[dict[str, Any]] = []
        for app in pending_apps:
            job = db.scalar(select(Job).where(Job.id == app.job_id))
            match = db.scalar(select(JobMatch).where(JobMatch.id == app.match_id)) if app.match_id else None
            if job:
                queue_preview.append({
                    "id": app.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "match_score": match.overall_score if match else 85,
                    "platform": job.platform,
                    "url": job.url,
                })

        return {
            "candidate_name": profile.full_name if profile and profile.full_name else user.full_name or "Candidate",
            "candidate_email": user.email,
            "target_role": role_title,
            "location": profile.location if profile and profile.location else "Chennai, India",
            "skills": user_skills,
            "experience_years": profile.total_experience_years if profile else 2,
            "profile_verified": profile.is_verified if profile else False,
            "today_stats": {
                "jobs_found": total_jobs_found,
                "shortlisted": total_shortlisted,
                "applications_sent_total": applications_sent,
                "applications_sent_today": applications_sent_today,
                "pending_approval": pending_approval,
                "daily_limit": pref.daily_limit if pref else 20,
            },
            "bot_status": {
                "is_running": bot_settings.is_running if bot_settings else False,
                "schedule": "Every 6 Hours (APScheduler)",
                "last_run": latest_run.started_at.isoformat() if latest_run and latest_run.started_at else None,
            },
            "approval_queue_top": queue_preview,
        }

    def _build_system_prompt(self, context: dict[str, Any]) -> str:
        """Construct the prompt giving AI live application awareness and universal intelligence."""
        stats = context["today_stats"]
        bot = context["bot_status"]
        skills_str = ", ".join(context["skills"][:15]) if context["skills"] else "React, Next.js, TypeScript"
        queue_str = "\n".join(
            [f"- {q['title']} at {q['company']} ({q['location']}) - Score: {q['match_score']}%" for q in context["approval_queue_top"]]
        ) or "None currently pending."

        return f"""You are **Antigravity AI**, the highly capable, friendly, and universal AI Career Copilot embedded directly inside Ananth's Job Automation platform.

### YOUR TWO PRIMARY CAPABILITIES:
1. **LIVE APPLICATION DATA & STATUS**:
   You have accurate real-time knowledge of the user's dashboard and job pipeline. When the user asks about jobs, applications sent, approval queue, or bot status, cite these EXACT figures:
   - **Candidate Name:** {context['candidate_name']} ({context['target_role']})
   - **Location:** {context['location']}
   - **Verified Skills:** {skills_str}
   - **Jobs Discovered / Scanned:** {stats['jobs_found']} jobs (Naukri & Indeed)
   - **Shortlisted (AI Match >= 75%):** {stats['shortlisted']} jobs
   - **Applications Sent (Verified):** {stats['applications_sent_total']} total ({stats['applications_sent_today']} today)
   - **Pending in Approval Queue:** {stats['pending_approval']} jobs awaiting candidate approval
   - **Daily Application Ceiling:** {stats['daily_limit']} jobs/day
   - **Bot Scheduler:** {bot['schedule']} • Active: {'Yes (Running)' if bot['is_running'] else 'Stopped / Standby'}
   - **Top Jobs in Queue:**
{queue_str}

   Always provide helpful clickable markdown links to relevant app pages when mentioning them:
   - Approval Queue: `[Approval Queue](/approval-queue)`
   - Applications Tracker: `[Applications Tracker](/applications)`
   - Job Discovery: `[Job Discovery](/jobs)`
   - Bot Controls: `[Bot Controls](/bot-controls)`
   - Profile & Resume: `[Resume & Profile](/profile)`

2. **UNIVERSAL WORLD & TECHNICAL INTELLIGENCE**:
   You are NOT limited to job questions. You are an expert senior developer, career mentor, and universal assistant:
   - Answer ANY question the user asks: coding (React, Next.js, Python, TypeScript, algorithms), interview preparation, resume bullet improvements, cold email drafting, system design, math, science, general knowledge, or creative writing.
   - Give complete, clean code snippets and structured bullet points when asked technical questions.

### LANGUAGE & TONE GUIDELINES:
- **Multilingual:** The user speaks English, Tamil, and Tanglish (e.g. "innaki evlo apply pannen", "react hooks pathi sollu").
- Respond naturally in the SAME language/style the user writes to you in:
  - If they ask in Tanglish/Tamil, reply warmly in Tanglish/Tamil.
  - If they ask in English, reply in crisp professional English.
- Be concise, accurate, encouraging, and structured.
"""

    async def generate_response(
        self,
        message: str,
        history: list[dict[str, str]],
        user: User,
        db: Session,
    ) -> dict[str, Any]:
        """Generate AI response using Gemini API or live heuristic fallback."""
        context = self.gather_live_context(user, db)
        system_prompt = self._build_system_prompt(context)
        api_key = self._get_api_key()

        # If Gemini API Key is present, call Google Gemini 2.0 Flash
        if api_key:
            try:
                reply = await self._call_gemini(message, history, system_prompt, api_key)
                return {
                    "reply": reply,
                    "model": self.gemini_model,
                    "live_stats": context["today_stats"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                logger.warning("Gemini API call failed (%s), falling back to heuristic engine", e)

        # Fallback heuristic engine (always responds accurately with live DB data)
        reply = self._generate_heuristic_response(message, context)
        return {
            "reply": reply,
            "model": "built-in-copilot",
            "live_stats": context["today_stats"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _call_gemini(
        self,
        message: str,
        history: list[dict[str, str]],
        system_prompt: str,
        api_key: str,
    ) -> str:
        """Call Gemini REST generateContent endpoint using httpx."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={api_key}"

        contents: list[dict[str, Any]] = []
        # Append up to last 8 turns of history
        for h in history[-8:]:
            role = "model" if h.get("role") in ("model", "assistant") else "user"
            content = h.get("content", "").strip()
            if content:
                contents.append({"role": role, "parts": [{"text": content}]})

        # Append current user message
        contents.append({"role": "user", "parts": [{"text": message}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"]
            else:
                logger.error("Gemini API error %s: %s", res.status_code, res.text)
                raise RuntimeError(f"Gemini error {res.status_code}")

        return "I could not generate a response at this time. Please try again."

    def _generate_heuristic_response(self, message: str, context: dict[str, Any]) -> str:
        """Intelligent local fallback when Gemini API key is not yet configured or offline."""
        msg = message.lower().strip()
        stats = context["today_stats"]
        name = context["candidate_name"]

        # Today's jobs / how many jobs / apply counts
        if any(w in msg for w in ("evlo", "evolo", "how many", "today", "innaki", "innaiku", "jobs", "apply", "applied", "sent", "shortlist", "count", "stat")):
            return (
                f"வணக்கம் {name}! உங்களது Application-ன் இன்றைய நேரடி நிலவரம் இதோ:\n\n"
                f"- 🔍 **Jobs Found:** மொத்தம் **{stats['jobs_found']}** வேலைகள் (Naukri & Indeed) கண்டறியப்பட்டுள்ளன.\n"
                f"- 🎯 **Shortlisted (AI Match >= 75%):** **{stats['shortlisted']}** வேலைகள் உங்கள் Profile-க்கு பொருந்துகின்றன.\n"
                f"- 🚀 **Applications Sent:** **{stats['applications_sent_total']}** வேலைகளுக்கு Applications வெற்றிகரமாக அனுப்பப்பட்டுள்ளன (இன்று: {stats['applications_sent_today']}).\n"
                f"- ⏳ **Pending Review:** **{stats['pending_approval']}** வேலைகள் Approval Queue-ல் காத்திருக்கின்றன.\n"
                f"- 🛡️ **Daily Limit:** {stats['daily_limit']} jobs/day.\n\n"
                f"உடனே விண்ணப்பிக்க [👉 Approval Queue](/approval-queue) பக்கத்திற்கு செல்லலாம்!"
            )

        # Bot status / scheduler
        if any(w in msg for w in ("bot", "schedule", "running", "status", "stop", "start", "run")):
            bot = context["bot_status"]
            status_text = "Active & Running" if bot["is_running"] else "Standby / Stopped"
            return (
                f"🤖 **Bot Operating Status:**\n\n"
                f"- **Current State:** {status_text}\n"
                f"- **Schedule:** {bot['schedule']}\n"
                f"- **Last Run:** {bot['last_run'] or 'Recent'}\n\n"
                f"புதிய வேலைகளைத் தேட உடனடியாக [👉 Bot Controls](/bot-controls) பக்கத்தில் **'Run Bot Now'** கொடுக்கலாம்."
            )

        # Approval Queue
        if any(w in msg for w in ("queue", "approval", "pending", "review")):
            top = context["approval_queue_top"]
            if top:
                job_list = "\n".join([f"- **{j['title']}** at {j['company']} ({j['location']}) — *{j['match_score']}% Match*" for j in top])
                return (
                    f"📋 **Approval Queue-ல் உள்ள Top Jobs ({stats['pending_approval']} pending):**\n\n"
                    f"{job_list}\n\n"
                    f"இவற்றை Review செய்து Apply செய்ய [👉 Approval Queue-க்கு செல்லுங்கள்](/approval-queue)."
                )
            return f"தற்போது Approval Queue-ல் புதிய வேலைகள் எதுவும் நிலுவையில் இல்லை. புதிய வேலைகளைக் கண்டறிய [👉 Bot Controls](/bot-controls)-ல் Bot-ஐ Run செய்யுங்கள்."

        # Skills / Profile
        if any(w in msg for w in ("skill", "profile", "resume", "experience")):
            skills = ", ".join(context["skills"]) or "React, Next.js, TypeScript"
            return (
                f"👤 **Candidate Profile Details:**\n\n"
                f"- **Name:** {name}\n"
                f"- **Role:** {context['target_role']}\n"
                f"- **Location:** {context['location']}\n"
                f"- **Key Skills:** {skills}\n"
                f"- **Experience:** {context['experience_years']} Years\n\n"
                f"Profile-ஐ மாற்ற [👉 Resume & Profile](/profile) பக்கத்திற்கு செல்லலாம்."
            )

        # General question fallback
        return (
            f"வணக்கம் {name}! நான் உங்களது **AI Career Copilot**.\n\n"
            f"நமது Application-ல் உள்ள Jobs, Applications, Approval Queue, மற்றும் Bot Controls பற்றி எதை வேண்டுமானாலும் என்னிடம் கேட்கலாம்.\n\n"
            f"💡 *குறிப்பு: உலகளாவிய Coding, Interview preparation மற்றும் பொதுவான கேள்விகளுக்கு முழுமையான Gemini 2.0 AI அறிவைப் பெற, `.env`-ல் `GEMINI_API_KEY` சேர்த்துக் கொள்ளலாம்.*"
        )


ai_chat_service = AIChatService()
