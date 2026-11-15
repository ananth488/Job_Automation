"""Applications and Approval Queue API endpoints."""

import os
import re
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import (
    User,
    Application,
    ApplicationStatusHistory,
    Job,
    JobMatch,
    CandidateProfile,
    GeneratedDocument,
    ScreeningAnswer,
    Resume,
    Preference,
)
from app.schemas.application import (
    ApplicationResponse,
    ApplicationDetailResponse,
    ApplicationStatusUpdate,
    ApplicationListResponse,
    BulkApplyRequest,
    BulkApproveRequest,
)
from app.services.tailoring.tailoring import ResumeTailor

router = APIRouter(prefix="/applications", tags=["applications"])
tailor = ResumeTailor()


@router.get("/", response_model=ApplicationListResponse)
def list_applications(
    status_filter: str | None = None,
    method: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List applications for current user with full job details and match scores."""
    query = select(Application).where(Application.user_id == current_user.id)
    if status_filter:
        query = query.where(Application.status == status_filter)
    if method:
        query = query.where(Application.method == method)

    query = query.order_by(desc(Application.created_at))
    apps = db.scalars(query).all()

    items: list[ApplicationResponse] = []
    for app in apps:
        job = db.scalar(select(Job).where(Job.id == app.job_id))
        match = db.scalar(select(JobMatch).where(JobMatch.id == app.match_id)) if app.match_id else None
        if not match and job:
            match = db.scalar(
                select(JobMatch).where(
                    (JobMatch.user_id == current_user.id) & (JobMatch.job_id == job.id)
                )
            )

        app_dict = {
            "id": app.id,
            "user_id": app.user_id,
            "job_id": app.job_id,
            "match_id": app.match_id,
            "status": app.status,
            "method": app.method,
            "tailored_resume_path": app.tailored_resume_path,
            "cover_letter_path": app.cover_letter_path,
            "submitted_at": app.submitted_at,
            "notes": app.notes,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
            "job_title": job.title if job else "Software Engineer Position",
            "company": job.company if job else "Company",
            "location": job.location if job else "",
            "platform": job.platform if job else "",
            "url": job.url if job else "",
            "work_mode": job.work_mode if job else "",
            "score": int(match.overall_score) if match and match.overall_score is not None else None,
        }
        items.append(ApplicationResponse(**app_dict))

    return ApplicationListResponse(
        items=items,
        total=len(items),
    )


@router.post("/bulk-apply", status_code=status.HTTP_200_OK)
def bulk_apply_jobs(
    bulk_in: BulkApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply to multiple jobs in one click, generating tailored documents automatically."""
    if not bulk_in.job_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No job IDs provided")

    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile or not profile.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verified candidate profile required before applying to jobs",
        )

    applied_count = 0
    now = datetime.now(timezone.utc)

    for job_id in bulk_in.job_ids:
        job = db.scalar(select(Job).where(Job.id == job_id))
        if not job:
            continue

        existing_app = db.scalar(
            select(Application).where(
                (Application.user_id == current_user.id) & (Application.job_id == job_id)
            )
        )

        match = db.scalar(
            select(JobMatch).where(
                (JobMatch.user_id == current_user.id) & (JobMatch.job_id == job_id)
            )
        )
        matched_skills = match.matched_skills if match else (profile.skills or [])

        target_status = "applied" if bulk_in.auto_approve else "pending_approval"

        if existing_app:
            if existing_app.status != "applied":
                old_status = existing_app.status
                existing_app.status = target_status
                if target_status == "applied":
                    existing_app.submitted_at = now
                existing_app.updated_at = now
                history = ApplicationStatusHistory(
                    application_id=existing_app.id,
                    old_status=old_status,
                    new_status=target_status,
                    notes="Applied via Bulk Apply",
                )
                db.add(history)
                applied_count += 1
            continue

        # Generate tailored materials
        cover_letter = tailor.generate_cover_letter(profile, job, matched_skills)
        tailored_summary = tailor.generate_tailored_summary(profile, job, matched_skills)

        new_app = Application(
            user_id=current_user.id,
            job_id=job_id,
            match_id=match.id if match else None,
            status=target_status,
            method="automated",
            submitted_at=now if target_status == "applied" else None,
            notes=f"Automated application tailored for {job.title} at {job.company}",
        )
        db.add(new_app)
        db.commit()
        db.refresh(new_app)

        # Save documents
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
            notes="Application submitted via Bulk Apply",
        )
        db.add_all([doc_resume, doc_cl, history])
        applied_count += 1

    db.commit()
    return {"message": f"Successfully applied to {applied_count} jobs", "applied_count": applied_count}


@router.post("/bulk-approve", status_code=status.HTTP_200_OK)
def bulk_approve_applications(
    bulk_in: BulkApproveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve multiple queued applications in one click."""
    if not bulk_in.application_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No application IDs provided")

    now = datetime.now(timezone.utc)
    approved_count = 0

    for app_id in bulk_in.application_ids:
        app = db.scalar(
            select(Application).where(
                (Application.id == app_id) & (Application.user_id == current_user.id)
            )
        )
        if app and app.status == "pending_approval":
            old_status = app.status
            app.status = "applied"
            app.submitted_at = now
            app.updated_at = now
            history = ApplicationStatusHistory(
                application_id=app.id,
                old_status=old_status,
                new_status="applied",
                notes="Candidate bulk approved application",
            )
            db.add(history)
            approved_count += 1

    db.commit()
    return {"message": f"Successfully approved {approved_count} applications", "approved_count": approved_count}


class SelectResumeRequest(BaseModel):
    resume_type: str = Field(..., description="'tailored' or 'original'")


@router.get("/approval-queue", response_model=list[dict])
def get_approval_queue(
    posted_within_days: int | None = Query(default=None, ge=0, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List applications waiting for candidate review and approval with dual-resume options and freshness filter."""
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    master_resume = db.scalar(
        select(Resume).where(Resume.user_id == current_user.id).order_by(desc(Resume.created_at))
    )

    # Only filter by days if explicitly specified by user filter query param;
    # otherwise show all queued items so count matches pending_approval stat exactly.
    effective_days = posted_within_days

    apps = db.scalars(
        select(Application)
        .where(
            (Application.user_id == current_user.id)
            & (Application.status == "pending_approval")
        )
        .order_by(desc(Application.created_at))
    ).all()

    results = []
    for app in apps:
        job = db.scalar(select(Job).where(Job.id == app.job_id))
        if not job:
            continue

        if effective_days is not None and effective_days > 0 and job.posted_date:
            cutoff = datetime.now(timezone.utc) - timedelta(days=int(effective_days))
            p_date = job.posted_date if job.posted_date.tzinfo else job.posted_date.replace(tzinfo=timezone.utc)
            if p_date < cutoff:
                continue

        match = db.scalar(select(JobMatch).where(JobMatch.id == app.match_id)) if app.match_id else None
        if not match and job:
            match = db.scalar(
                select(JobMatch).where(
                    (JobMatch.user_id == current_user.id) & (JobMatch.job_id == job.id)
                )
            )

        matched_skills = match.matched_skills if match and match.matched_skills else (profile.skills if profile and profile.skills else [])
        missing_skills = match.missing_skills if match and match.missing_skills else []

        doc_resume = db.scalar(
            select(GeneratedDocument).where(
                (GeneratedDocument.application_id == app.id) & (GeneratedDocument.doc_type == "resume")
            )
        )
        doc_cl = db.scalar(
            select(GeneratedDocument).where(
                (GeneratedDocument.application_id == app.id) & (GeneratedDocument.doc_type == "cover_letter")
            )
        )

        tailored_summary = doc_resume.content_text if doc_resume else None
        if not tailored_summary and profile and job:
            tailored_summary = tailor.generate_tailored_summary(profile, job, matched_skills)

        cover_letter = doc_cl.content_text if doc_cl else None
        if not cover_letter and profile and job:
            cover_letter = tailor.generate_cover_letter(profile, job, matched_skills)

        # Selected resume preference: 'tailored' (default, ATS optimized) or 'original' (master PDF)
        selected_type = "original" if (app.notes and "Selected Resume: original" in app.notes) else "tailored"

        results.append({
            "application_id": app.id,
            "job_id": app.job_id,
            "status": app.status,
            "method": app.method,
            "job_title": job.title if job else "",
            "company": job.company if job else "",
            "location": job.location if job else "",
            "platform": job.platform if job else "",
            "url": job.url if job else "",
            "apply_type": getattr(job, "apply_type", None) or ("company_portal" if any(c in (job.company or "").lower() for c in ["zoho", "tcs", "infosys", "tech mahindra"]) else "direct_1click"),
            "company_type": getattr(job, "company_type", None) or "startup",
            "company_url": getattr(job, "company_url", None),
            "posted_date": job.posted_date.isoformat() if job and job.posted_date else None,
            "overall_score": match.overall_score if match else 0.0,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "tailored_summary": tailored_summary,
            "cover_letter": cover_letter,
            "selected_resume_type": selected_type,
            "master_resume_id": master_resume.id if master_resume else None,
            "master_resume_filename": master_resume.filename if master_resume else "Master_Resume.pdf",
            "tailored_pdf_url": f"/api/v1/applications/{app.id}/tailored-pdf",
            "tailored_resume_path": app.tailored_resume_path,
            "cover_letter_path": app.cover_letter_path,
            "created_at": app.created_at.isoformat() if app.created_at else None,
        })
    return results


@router.get("/{application_id}/tailored-pdf")
def get_tailored_resume_pdf(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate or retrieve the ATS-optimized tailored resume PDF specifically for this job."""
    app = db.scalar(
        select(Application).where(
            (Application.id == application_id) & (Application.user_id == current_user.id)
        )
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    job = db.scalar(select(Job).where(Job.id == app.job_id))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")

    match = db.scalar(select(JobMatch).where(JobMatch.id == app.match_id)) if app.match_id else None
    if not match:
        match = db.scalar(
            select(JobMatch).where(
                (JobMatch.user_id == current_user.id) & (JobMatch.job_id == job.id)
            )
        )

    # In Tailored Neo Resume, bridge JD gap dynamically by combining matched skills + missing required skills
    matched_skills = list(match.matched_skills) if match and match.matched_skills else []
    missing_skills = list(match.missing_skills) if match and match.missing_skills else []

    candidate_skills = profile.skills or []
    cand_lower = {s.lower() for s in candidate_skills}
    if job.skills_required:
        for js in job.skills_required:
            if js.lower() not in cand_lower and js not in missing_skills:
                missing_skills.append(js)
            elif js.lower() in cand_lower and js not in matched_skills:
                matched_skills.append(js)

    doc_resume = db.scalar(
        select(GeneratedDocument).where(
            (GeneratedDocument.application_id == app.id) & (GeneratedDocument.doc_type == "resume")
        )
    )
    tailored_summary = (
        doc_resume.content_text
        if (doc_resume and doc_resume.content_text and len(doc_resume.content_text) > 30)
        else tailor.generate_tailored_summary(profile, job, matched_skills=matched_skills, missing_skills=missing_skills)
    )

    original_resume = db.scalar(
        select(Resume).where(Resume.user_id == current_user.id).order_by(desc(Resume.created_at))
    )

    try:
        from app.services.tailoring.resume_pdf_generator import tailored_pdf_generator
        pdf_path = tailored_pdf_generator.generate_pdf(
            profile=profile,
            job=job,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            tailored_summary=tailored_summary,
            original_resume=original_resume,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tailored resume PDF: {str(e)}",
        )

    app.tailored_resume_path = str(pdf_path)
    db.commit()

    sanitized_comp = "".join(c for c in (job.company or "Job") if c.isalnum() or c in ("-", "_"))
    candidate_clean = re.sub(r"[^a-zA-Z0-9]", "_", profile.full_name or "Candidate").strip("_")
    filename = f"Tailored_Resume_{candidate_clean}_{sanitized_comp}.pdf"

    return FileResponse(
        path=str(pdf_path),
        filename=filename,
        media_type="application/pdf",
    )


@router.post("/{application_id}/select-resume")
def select_application_resume(
    application_id: int,
    request: SelectResumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set candidate's preferred resume type ('tailored' or 'original') for this application."""
    if request.resume_type not in ["tailored", "original"]:
        raise HTTPException(status_code=400, detail="Invalid resume type. Must be 'tailored' or 'original'")

    app = db.scalar(
        select(Application).where(
            (Application.id == application_id) & (Application.user_id == current_user.id)
        )
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    notes = app.notes or ""
    if "Selected Resume:" in notes:
        notes = re.sub(r"Selected Resume: \w+", f"Selected Resume: {request.resume_type}", notes)
    else:
        notes = f"{notes} | Selected Resume: {request.resume_type}".strip(" |")

    app.notes = notes
    db.commit()
    return {"success": True, "selected_resume_type": request.resume_type, "application_id": application_id}


@router.post("/prepare/{job_id}", response_model=ApplicationResponse)
def prepare_application_for_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate tailored documents and add job to approval queue or applications."""
    job = db.scalar(select(Job).where(Job.id == job_id))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Candidate profile required")

    existing_app = db.scalar(
        select(Application).where(
            (Application.user_id == current_user.id) & (Application.job_id == job_id)
        )
    )
    if existing_app:
        return existing_app

    match = db.scalar(
        select(JobMatch).where(
            (JobMatch.user_id == current_user.id) & (JobMatch.job_id == job_id)
        )
    )

    # In Tailored Neo Resume, bridge JD gap by combining matched skills + missing required skills
    matched_skills = list(match.matched_skills) if match and match.matched_skills else []
    missing_skills = list(match.missing_skills) if match and match.missing_skills else []
    candidate_skills = profile.skills or []
    cand_lower = {s.lower() for s in candidate_skills}
    if job.skills_required:
        for js in job.skills_required:
            if js.lower() not in cand_lower and js not in missing_skills:
                missing_skills.append(js)
            elif js.lower() in cand_lower and js not in matched_skills:
                matched_skills.append(js)

    cover_letter = tailor.generate_cover_letter(profile, job, matched_skills=matched_skills, missing_skills=missing_skills)
    tailored_summary = tailor.generate_tailored_summary(profile, job, matched_skills=matched_skills, missing_skills=missing_skills)

    app = Application(
        user_id=current_user.id,
        job_id=job_id,
        match_id=match.id if match else None,
        status="pending_approval",
        method="manual",
        notes=f"Tailored for {job.title} at {job.company}",
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    # Save generated documents
    doc_resume = GeneratedDocument(
        application_id=app.id,
        doc_type="resume",
        content_text=tailored_summary,
    )
    doc_cl = GeneratedDocument(
        application_id=app.id,
        doc_type="cover_letter",
        content_text=cover_letter,
    )
    db.add_all([doc_resume, doc_cl])

    # Initial history
    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status=None,
        new_status="pending_approval",
        notes="Application prepared for candidate review",
    )
    db.add(history)
    db.commit()
    db.refresh(app)

    return app


@router.post("/{application_id}/approve", response_model=ApplicationResponse)
def approve_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Candidate approves application; transitions to applied/ready for submission."""
    app = db.scalar(
        select(Application).where(
            (Application.id == application_id) & (Application.user_id == current_user.id)
        )
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    old_status = app.status
    app.status = "applied"
    app.submitted_at = datetime.now(timezone.utc)
    app.updated_at = datetime.now(timezone.utc)

    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status=old_status,
        new_status="applied",
        notes="Candidate approved and applied",
    )
    db.add(history)
    db.commit()
    db.refresh(app)
    return app


@router.post("/{application_id}/reject", response_model=ApplicationResponse)
def reject_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Candidate rejects/skips application."""
    app = db.scalar(
        select(Application).where(
            (Application.id == application_id) & (Application.user_id == current_user.id)
        )
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    old_status = app.status
    app.status = "withdrawn"
    app.updated_at = datetime.now(timezone.utc)

    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status=old_status,
        new_status="withdrawn",
        notes="Candidate skipped this application",
    )
    db.add(history)
    db.commit()
    db.refresh(app)
    return app


@router.put("/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    application_id: int,
    status_in: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually update application tracking status (interview, offer, rejected, etc.)."""
    app = db.scalar(
        select(Application).where(
            (Application.id == application_id) & (Application.user_id == current_user.id)
        )
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    old_status = app.status
    app.status = status_in.status
    if status_in.notes:
        app.notes = status_in.notes
    app.updated_at = datetime.now(timezone.utc)

    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status=old_status,
        new_status=status_in.status,
        notes=status_in.notes or f"Status changed to {status_in.status}",
    )
    db.add(history)
    db.commit()
    db.refresh(app)
    return app


@router.get("/{application_id}", response_model=ApplicationDetailResponse)
def get_application_detail(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full application record, documents, screening questions and history."""
    app = db.scalar(
        select(Application).where(
            (Application.id == application_id) & (Application.user_id == current_user.id)
        )
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    job = db.scalar(select(Job).where(Job.id == app.job_id))
    match = db.scalar(select(JobMatch).where(JobMatch.id == app.match_id)) if app.match_id else None

    docs = db.scalars(
        select(GeneratedDocument).where(GeneratedDocument.application_id == app.id)
    ).all()

    screening = db.scalars(
        select(ScreeningAnswer).where(ScreeningAnswer.application_id == app.id)
    ).all()

    history = db.scalars(
        select(ApplicationStatusHistory)
        .where(ApplicationStatusHistory.application_id == app.id)
        .order_by(desc(ApplicationStatusHistory.changed_at))
    ).all()

    return ApplicationDetailResponse(
        application=ApplicationResponse.model_validate(app),
        job={
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "platform": job.platform,
            "url": job.url,
            "description": job.description,
            "skills_required": job.skills_required,
            "work_mode": job.work_mode,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
        } if job else None,
        match={
            "overall_score": match.overall_score,
            "matched_skills": match.matched_skills,
            "missing_skills": match.missing_skills,
            "explanation": match.explanation,
        } if match else None,
        documents=[
            {"id": d.id, "doc_type": d.doc_type, "content": d.content_text}
            for d in docs
        ],
        screening_answers=[
            {"id": s.id, "question": s.question, "answer": s.answer, "confidence": s.confidence_score}
            for s in screening
        ],
        status_history=[
            {
                "id": h.id,
                "old_status": h.old_status,
                "new_status": h.new_status,
                "changed_at": h.changed_at.isoformat(),
                "notes": h.notes,
            }
            for h in history
        ],
    )

