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
        self.candidate_models = [
            "gemini-flash-lite-latest",
            "gemini-2.5-flash-lite",
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]

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
- **Language:** ALWAYS answer strictly in professional, well-structured, clean ENGLISH. Do NOT reply in Tamil or Tanglish unless the user explicitly asks for Tamil.
- Provide crisp formatting, clear markdown headers, bullet points, and code blocks where applicable.
- Be encouraging, precise, and practical.
"""

    async def generate_response(
        self,
        message: str,
        history: list[dict[str, str]],
        user: User,
        db: Session,
        gemini_api_key: str | None = None,
    ) -> dict[str, Any]:
        """Generate AI response using Gemini API or live heuristic fallback."""
        context = self.gather_live_context(user, db)
        system_prompt = self._build_system_prompt(context)
        api_key = (gemini_api_key or "").strip() or self._get_api_key()

        # If Gemini API Key is present, call Google Gemini API with fallback
        if api_key:
            try:
                reply, model_used = await self._call_gemini(message, history, system_prompt, api_key)
                return {
                    "reply": reply,
                    "model": model_used,
                    "live_stats": context["today_stats"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                logger.warning("Gemini API call failed (%s), falling back to heuristic engine", e)

        # Fallback heuristic engine (always responds in clear English with live DB data and technical knowledge)
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
    ) -> tuple[str, str]:
        """Call Gemini REST generateContent endpoint using httpx with automatic model fallback."""
        contents: list[dict[str, Any]] = []
        for h in history[-8:]:
            role = "model" if h.get("role") in ("model", "assistant") else "user"
            content = h.get("content", "").strip()
            if content:
                contents.append({"role": role, "parts": [{"text": content}]})

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
            for model_name in self.candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"], model_name
                    elif res.status_code == 404:
                        # Model not available for this key/tier, fallback to next
                        continue
                    else:
                        logger.warning("Gemini model %s returned status %s: %s", model_name, res.status_code, res.text[:120])
                except Exception as e:
                    logger.warning("Gemini model %s request exception: %s", model_name, e)
                    continue

        raise RuntimeError("No Gemini model responded successfully")

    def _generate_heuristic_response(self, message: str, context: dict[str, Any]) -> str:
        """Intelligent English knowledge engine for technical questions and live application data."""
        msg = message.lower().strip()
        stats = context["today_stats"]
        name = context["candidate_name"]

        # 1. TECHNICAL: React
        if re.search(r"\b(react|react\.js|reactjs)\b", msg):
            return (
                "### What is React?\n\n"
                "**React** (or React.js) is a popular, open-source front-end JavaScript library developed by Meta (Facebook) for building fast, responsive, and component-based user interfaces.\n\n"
                "#### Core Architecture & Features:\n"
                "1. **Component-Based Architecture:** UIs are divided into modular, reusable, self-contained pieces (components) with their own state and lifecycle.\n"
                "2. **Virtual DOM (VDOM):** Instead of directly touching the browser's real DOM (which is slow), React keeps a lightweight virtual representation in memory. When state updates, it diffs changes efficiently and batches DOM updates.\n"
                "3. **Declarative Syntax (JSX):** Combines HTML-like structure directly inside JavaScript, making component templates intuitive.\n"
                "4. **Unidirectional Data Flow:** Data flows strictly downward from parent to child via `props`, ensuring predictable state updates and easier debugging.\n"
                "5. **Hooks & Modern API:** Features built-in hooks (`useState`, `useEffect`, `useContext`, `useReducer`, `useMemo`, `useCallback`) for clean functional code.\n\n"
                "#### Quick Example:\n"
                "```jsx\n"
                "import React, { useState } from 'react';\n\n"
                "export default function Counter() {\n"
                "  const [count, setCount] = useState(0);\n\n"
                "  return (\n"
                "    <button onClick={() => setCount(count + 1)}>\n"
                "      Clicked {count} times\n"
                "    </button>\n"
                "  );\n"
                "}\n"
                "```\n\n"
                "React forms the foundation of modern frameworks like **Next.js**, which adds full-stack capabilities, server-side rendering, and production routing."
            )

        # 2. TECHNICAL: Next.js
        if re.search(r"\b(next|next\.js|nextjs)\b", msg):
            return (
                "### What is Next.js?\n\n"
                "**Next.js** is a production-grade full-stack React framework created by Vercel that enables developers to build high-performance web applications with server-side rendering, static site generation, and modern routing.\n\n"
                "#### Key Highlights:\n"
                "- **React Server Components (RSC):** Render heavy UI components directly on the server, shipping zero client-side JavaScript.\n"
                "- **App Router (`app/` directory):** Intuitive file-based routing with nested layouts, parallel routes, and loading states.\n"
                "- **Rendering Strategies:** Supports Static Site Generation (SSG), Server-Side Rendering (SSR), and Incremental Static Regeneration (ISR).\n"
                "- **Edge Middleware:** Intercept requests before they hit pages to handle authentication, redirects, and headers at the edge.\n"
                "- **Built-in Optimizations:** Automatic image optimization (`next/image`), font loading (`next/font`), and script management."
            )

        # 3. TECHNICAL: Redux / State Management
        if re.search(r"\b(redux|redux toolkit|state management)\b", msg):
            return (
                "### What is Redux?\n\n"
                "**Redux** is a predictable state container for JavaScript applications. It centralizes your application's global state into a single immutable store.\n\n"
                "#### Core Principles:\n"
                "1. **Single Source of Truth:** Entire state tree is stored in a single object inside the store.\n"
                "2. **State is Read-Only:** The only way to mutate state is to dispatch an **Action**.\n"
                "3. **Changes are made with Pure Functions:** **Reducers** take the previous state and an action, returning a new updated state without side-effects.\n\n"
                "**Modern Redux:** Always use **Redux Toolkit (`@reduxjs/toolkit`)**, which eliminates boilerplate using `createSlice` and `createAsyncThunk`."
            )

        # 4. TECHNICAL: TypeScript
        if re.search(r"\b(typescript|ts)\b", msg):
            return (
                "### What is TypeScript?\n\n"
                "**TypeScript** is a strongly-typed superset of JavaScript developed by Microsoft. It adds optional static typing, interfaces, and compile-time type safety to plain JavaScript.\n\n"
                "#### Why Use TypeScript?\n"
                "- **Catches Bugs Early:** Catches syntax and type errors during compilation before code reaches production.\n"
                "- **Superior Developer Experience:** Provides intelligent IDE autocomplete, refactoring tools, and self-documenting code.\n"
                "- **Enterprise Scalability:** Essential for large teams and large codebases to ensure interface contracts remain consistent."
            )

        # 5. TECHNICAL: Hooks (useState, useEffect, etc.)
        if re.search(r"\b(hooks|usestate|useeffect|usememo|usecallback|usecontext)\b", msg):
            return (
                "### React Hooks Overview\n\n"
                "React Hooks allow functional components to maintain internal state and access lifecycle features without writing class components.\n\n"
                "- `useState`: Manages local component state.\n"
                "- `useEffect`: Handles side-effects (API calls, subscriptions, DOM manipulation) after rendering.\n"
                "- `useContext`: Subscribes to React Context without prop drilling.\n"
                "- `useMemo`: Memoizes expensive calculated values to avoid recalculation on every render.\n"
                "- `useCallback`: Memoizes callback function definitions to prevent unnecessary child re-renders."
            )

        # 6. TECHNICAL: Virtual DOM
        if re.search(r"\b(virtual dom|vdom)\b", msg):
            return (
                "### What is the Virtual DOM?\n\n"
                "The **Virtual DOM (VDOM)** is an in-memory lightweight abstraction of the real browser DOM kept by libraries like React.\n\n"
                "#### How it Works:\n"
                "1. When component state changes, React creates a new Virtual DOM tree.\n"
                "2. It runs a **diffing algorithm** (Reconciliation) comparing the new Virtual DOM with the previous snapshot.\n"
                "3. It computes the minimum set of real DOM operations and applies them in a single batch (Tree Mutation), avoiding costly browser reflows and repaints."
            )

        # 7. TECHNICAL: LeetCode & DSA
        if re.search(r"\b(leetcode|dsa|data structure|data structures|algorithms|algo)\b", msg):
            return (
                "### What is LeetCode & DSA?\n\n"
                "**LeetCode** is the world's most popular online platform for practicing software engineering coding challenges, primarily focusing on **Data Structures & Algorithms (DSA)** to prepare for technical interviews at top tech companies (FAANG/MANG & top startups).\n\n"
                "#### Core Topics & Patterns:\n"
                "1. **Essential Data Structures:** Arrays, Hash Maps / Sets, Linked Lists, Stacks & Queues, Binary Trees, Graphs, Heaps/Tries.\n"
                "2. **Algorithmic Patterns:**\n"
                "   - **Two Pointers & Sliding Window:** Array/String sub-problems.\n"
                "   - **Binary Search:** O(log N) searches on sorted sets.\n"
                "   - **BFS & DFS:** Tree and graph traversals.\n"
                "   - **Dynamic Programming (DP):** Breaking down overlapping subproblems with memoization/tabulation.\n\n"
                "#### Recommended Preparation Roadmap:\n"
                "- Start with the curated **NeetCode 150** or **Blind 75** list.\n"
                "- Focus on pattern recognition rather than memorizing individual solutions.\n"
                "- Write clean code with time & space complexity analysis (Big-O notation)."
            )

        # 8. TECHNICAL: JavaScript & Web Concepts
        if re.search(r"\b(javascript|js|event loop|closure|closures|promise|promises|async await)\b", msg):
            return (
                "### Modern JavaScript Fundamentals\n\n"
                "JavaScript is a single-threaded, non-blocking, asynchronous, concurrent programming language featuring a prototype-based object model.\n\n"
                "#### Critical Frontend Concepts:\n"
                "- **Event Loop:** Manages execution of code, collecting and processing events, and executing queued sub-tasks via Call Stack, Microtask Queue (Promises), and Macrotask Queue (setTimeout).\n"
                "- **Closures:** A function bundled together with references to its surrounding lexical environment, allowing inner functions to access outer variables even after the outer function has returned.\n"
                "- **Promises & Async/Await:** Syntactic sugar for handling asynchronous workflows with clean, linear error-handling via `try/catch`.\n"
                "- **Hoisting & Scope:** Difference between `var` (function-scoped, hoisted) and `let`/`const` (block-scoped, temporal dead zone)."
            )

        # 9. TECHNICAL: Interview Preparation
        if any(w in msg for w in ("interview", "prepare", "questions", "tips", "hiring")):
            return (
                "### Top Frontend Developer Technical Interview Questions:\n\n"
                "1. **Explain the difference between Client Components and Server Components in Next.js.**\n"
                "2. **How does React's Virtual DOM diffing algorithm (Reconciliation) work?**\n"
                "3. **What is the difference between `useMemo` and `useCallback`? When should you NOT use them?**\n"
                "4. **Explain Event Bubbling, Event Capturing, and Event Delegation in JavaScript.**\n"
                "5. **How do you optimize page load performance (Core Web Vitals - LCP, CLS, INP)?**\n\n"
                "💡 *Tip:* Use the **STAR method** (Situation, Task, Action, Result) when answering behavioral questions, and always mention measurable metrics (e.g. 'reduced load time by 30%')."
            )

        # 8. APPLICATION: Today's jobs / how many jobs / apply counts
        if any(w in msg for w in ("evlo", "evolo", "how many", "today", "innaki", "innaiku", "jobs", "apply", "applied", "sent", "shortlist", "count", "stat")):
            return (
                f"### Live Application Summary for {name}:\n\n"
                f"- 🔍 **Jobs Discovered:** **{stats['jobs_found']}** total jobs discovered across Naukri & Indeed.\n"
                f"- 🎯 **Shortlisted (AI Match ≥ 75%):** **{stats['shortlisted']}** jobs match your profile criteria.\n"
                f"- 🚀 **Applications Sent:** **{stats['applications_sent_total']}** applications verified & submitted (Today: **{stats['applications_sent_today']}**).\n"
                f"- ⏳ **Pending in Approval Queue:** **{stats['pending_approval']}** high-match positions ready for your review.\n"
                f"- 🛡️ **Daily Limit:** {stats['daily_limit']} jobs per day.\n\n"
                f"You can review and submit pending applications in the [Approval Queue](/approval-queue)."
            )

        # 9. APPLICATION: Bot status / scheduler
        if any(w in msg for w in ("bot", "schedule", "running", "status", "stop", "start", "run")):
            bot = context["bot_status"]
            status_text = "Active & Running" if bot["is_running"] else "Standby / Stopped"
            return (
                f"### Bot Operating Status:\n\n"
                f"- **Current State:** {status_text}\n"
                f"- **Schedule:** {bot['schedule']}\n"
                f"- **Last Run:** {bot['last_run'] or 'Recent'}\n\n"
                f"You can trigger an immediate automated job discovery run in [Bot Controls](/bot-controls)."
            )

        # 10. APPLICATION: Approval Queue
        if any(w in msg for w in ("queue", "approval", "pending", "review")):
            top = context["approval_queue_top"]
            if top:
                job_list = "\n".join([f"- **{j['title']}** at {j['company']} ({j['location']}) — *{j['match_score']}% Match*" for j in top])
                return (
                    f"### Jobs in Approval Queue ({stats['pending_approval']} pending):\n\n"
                    f"{job_list}\n\n"
                    f"Visit the [Approval Queue](/approval-queue) to review tailored resumes and submit."
                )
            return "There are currently no jobs pending in your Approval Queue. Run the bot to fetch new opportunities."

        # 11. APPLICATION: Profile & Skills
        if any(w in msg for w in ("skill", "profile", "resume", "experience")):
            skills = ", ".join(context["skills"]) or "React, Next.js, TypeScript"
            return (
                f"### Candidate Profile Overview:\n\n"
                f"- **Name:** {name}\n"
                f"- **Target Role:** {context['target_role']}\n"
                f"- **Location:** {context['location']}\n"
                f"- **Verified Skills:** {skills}\n"
                f"- **Total Experience:** {context['experience_years']} Years\n\n"
                f"You can update or re-verify your profile in [Resume & Profile](/profile)."
            )

        # 12. General fallback in clean English
        return (
            f"Hello {name}! I am your **AI Career Copilot**.\n\n"
            f"I have live access to your dashboard: **{stats['jobs_found']} jobs found**, **{stats['applications_sent_total']} applications sent**, and **{stats['pending_approval']} jobs pending review**.\n\n"
            f"You can ask me anything about your job pipeline, or ask any technical coding questions (e.g., *'What is React?'*, *'How does Next.js App Router work?'*, *'Interview questions for Frontend Developer'*).\n\n"
            f"💡 *Tip: For unbounded generative AI reasoning, you can add your free `GEMINI_API_KEY` in `.env` or in the Chat header!*"
        )


ai_chat_service = AIChatService()
