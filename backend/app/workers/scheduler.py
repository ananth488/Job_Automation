"""Background job scheduler and automated search/match workers."""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.models import (
    BotRun,
    BotSettings,
    Job,
    JobMatch,
    Preference,
    CandidateProfile,
    Notification,
    Application,
    ApplicationStatusHistory,
    GeneratedDocument,
)
from app.platforms.naukri import NaukriAdapter
from app.platforms.indeed import IndeedAdapter
from app.services.matcher.matcher import match_job_to_profile
from app.services.tailoring.tailoring import ResumeTailor

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
naukri_adapter = NaukriAdapter()
indeed_adapter = IndeedAdapter()
tailor = ResumeTailor()


async def run_job_search_cycle(user_id: int = 1) -> dict[str, Any]:
    """Execute a single job search, match, and filter cycle."""
    db: Session = SessionLocal()
    bot_run = BotRun(
        user_id=user_id,
        started_at=datetime.now(timezone.utc),
        status="running",
        jobs_found=0,
        jobs_matched=0,
        applications_submitted=0,
        errors=[],
    )
    db.add(bot_run)
    db.commit()
    db.refresh(bot_run)

    try:
        # 1. Fetch user preferences & verified profile
        pref = db.scalar(select(Preference).where(Preference.user_id == user_id))
        profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user_id))

        candidate_skills = profile.skills if profile and profile.skills else []
        locations = (
            pref.locations if pref and pref.locations
            else (profile.preferred_locations if profile and profile.preferred_locations
            else ([profile.location] if profile and profile.location
            else ["Chennai", "Bengaluru", "Hyderabad", "Remote"]))
        )
        roles = pref.desired_roles if pref and pref.desired_roles else []
        pref_keywords = pref.keywords if pref and pref.keywords else []

        # Combine desired roles, keywords and candidate's top verified skills
        search_keywords = list(dict.fromkeys(roles + pref_keywords + candidate_skills[:5]))
        if not search_keywords:
            search_keywords = ["Frontend Developer", "React", "TypeScript", "Next.js"]

        threshold = pref.match_threshold if pref and pref.match_threshold else 75
        candidate_exp = int(profile.total_experience_years or 2) if profile else 2

        # 2. Fetch jobs from platforms using candidate's skills and locations
        found_jobs: list[dict[str, Any]] = []
        naukri_jobs = await naukri_adapter.search_jobs(
            keywords=search_keywords,
            locations=locations,
            experience_min=candidate_exp,
            candidate_skills=candidate_skills,
            limit=25,
        )
        indeed_jobs = await indeed_adapter.search_jobs(
            keywords=search_keywords,
            locations=locations,
            experience_min=candidate_exp,
            candidate_skills=candidate_skills,
            limit=25,
        )
        found_jobs.extend(naukri_jobs)
        found_jobs.extend(indeed_jobs)

        bot_run.jobs_found = len(found_jobs)
        matched_count = 0
        applications_processed_this_cycle = 0
        daily_limit = int(pref.daily_limit or 20) if pref else 20
        approval_mode = pref.approval_mode if pref and pref.approval_mode else "below_threshold"

        # 3. Deduplicate and insert jobs, then compute / refresh match against candidate profile
        for item in found_jobs:
            existing = db.scalar(
                select(Job).where(
                    (Job.platform == item["platform"]) & (Job.external_job_id == item["external_job_id"])
                )
            )
            if not existing:
                job_obj = Job(**item)
                db.add(job_obj)
                db.commit()
                db.refresh(job_obj)
            else:
                job_obj = existing

            # Check if match already computed; update or insert with latest profile scoring
            existing_match = db.scalar(
                select(JobMatch).where(
                    (JobMatch.user_id == user_id) & (JobMatch.job_id == job_obj.id)
                )
            )
            if profile:
                match_result = match_job_to_profile(job_obj, profile, pref)
                active_match_id = None
                if existing_match:
                    existing_match.overall_score = match_result.overall_score
                    existing_match.skills_score = match_result.skills_score
                    existing_match.experience_score = match_result.experience_score
                    existing_match.location_score = match_result.location_score
                    existing_match.salary_score = match_result.salary_score
                    existing_match.role_fit_score = match_result.role_fit_score
                    existing_match.matched_skills = match_result.matched_skills
                    existing_match.missing_skills = match_result.missing_skills
                    existing_match.explanation = match_result.explanation
                    existing_match.status = "shortlisted" if match_result.overall_score >= threshold else "rejected"
                    db.commit()
                    active_match_id = existing_match.id
                else:
                    match_record = JobMatch(
                        user_id=user_id,
                        job_id=job_obj.id,
                        overall_score=match_result.overall_score,
                        skills_score=match_result.skills_score,
                        experience_score=match_result.experience_score,
                        location_score=match_result.location_score,
                        salary_score=match_result.salary_score,
                        role_fit_score=match_result.role_fit_score,
                        matched_skills=match_result.matched_skills,
                        missing_skills=match_result.missing_skills,
                        explanation=match_result.explanation,
                        status="shortlisted" if match_result.overall_score >= threshold else "rejected",
                    )
                    db.add(match_record)
                    db.commit()
                    db.refresh(match_record)
                    active_match_id = match_record.id

                if match_result.overall_score >= threshold:
                    matched_count += 1

                    # Check if application already exists for this job
                    existing_app = db.scalar(
                        select(Application).where(
                            (Application.user_id == user_id) & (Application.job_id == job_obj.id)
                        )
                    )

                    # Create application if under daily limit
                    if not existing_app and applications_processed_this_cycle < daily_limit:
                        target_status = "applied" if approval_mode == "auto" else "pending_approval"
                        now_time = datetime.now(timezone.utc)

                        matched_skills = match_result.matched_skills or profile.skills or []
                        tailored_summary = tailor.generate_tailored_summary(profile, job_obj, matched_skills)
                        cover_letter = tailor.generate_cover_letter(profile, job_obj, matched_skills)

                        new_app = Application(
                            user_id=user_id,
                            job_id=job_obj.id,
                            match_id=active_match_id,
                            status=target_status,
                            method="automated",
                            submitted_at=now_time if target_status == "applied" else None,
                            notes=f"Automated pipeline ({'Auto Applied' if target_status == 'applied' else 'Queued for Approval'}) for {job_obj.title} at {job_obj.company}",
                        )
                        db.add(new_app)
                        db.commit()
                        db.refresh(new_app)

                        doc_resume = GeneratedDocument(
                            application_id=new_app.id,
                            doc_type="resume",
                            content_text=tailored_summary,
                        )
                        doc_cl = GeneratedDocument(
                            application_id=new_app.id,
                            doc_type="cover_letter",
                            content_text=cover_letter,
                        )
                        history = ApplicationStatusHistory(
                            application_id=new_app.id,
                            old_status=None,
                            new_status=target_status,
                            notes=f"Automated run: {target_status}",
                        )
                        db.add_all([doc_resume, doc_cl, history])
                        db.commit()

                        applications_processed_this_cycle += 1
                        if target_status == "applied":
                            bot_run.applications_submitted += 1

        bot_run.jobs_matched = matched_count
        bot_run.status = "completed"
        bot_run.ended_at = datetime.now(timezone.utc)
        bot_run.log = f"Cycle completed successfully. Found {len(found_jobs)} opportunities, {matched_count} shortlisted above {threshold}% threshold."

        # Notification
        notif = Notification(
            user_id=user_id,
            type="daily_summary",
            title="Job Bot Cycle Completed",
            message=f"Discovered {len(found_jobs)} jobs. {matched_count} match your profile above {threshold}%.",
            is_read=False,
        )
        db.add(notif)
        db.commit()

        return {
            "status": "completed",
            "jobs_found": len(found_jobs),
            "jobs_matched": matched_count,
        }

    except Exception as exc:
        logger.exception("Error in job search cycle: %s", exc)
        bot_run.status = "failed"
        bot_run.ended_at = datetime.now(timezone.utc)
        bot_run.errors = [str(exc)]
        bot_run.log = f"Execution failed: {exc}"
        db.commit()
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


def start_scheduler():
    """Start the APScheduler background runner."""
    if not scheduler.running:
        try:
            # Default periodic job every 6 hours
            scheduler.add_job(
                run_job_search_cycle,
                trigger="interval",
                hours=6,
                id="default_job_cycle",
                replace_existing=True,
            )
            scheduler.start()
            logger.info("APScheduler initialized and running.")
        except Exception as e:
            logger.warning("Scheduler startup warning: %s", e)


def stop_scheduler():
    """Stop the scheduler safely."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
