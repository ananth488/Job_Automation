"""Resume upload and management API endpoints."""

import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, Resume, CandidateProfile
from app.schemas.resume import ResumeResponse, ResumeListResponse
from app.services.resume_parser.parser import ResumeParser

router = APIRouter(prefix="/resume", tags=["resume"])
parser = ResumeParser()


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload PDF or DOCX resume, extract data, and save record."""
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Only PDF and DOCX files are allowed.",
        )

    upload_dir = Path(settings.UPLOAD_DIR) / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / file.filename

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text & parsed structure
    raw_text = parser.extract_text(str(saved_path))
    parsed_struct = parser.parse(str(saved_path))
    parsed_data = parsed_struct.model_dump()

    # Determine version
    current_max_version = db.scalar(
        select(func.coalesce(func.max(Resume.version), 0)).where(Resume.user_id == current_user.id)
    )
    new_version = (current_max_version or 0) + 1

    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(saved_path),
        file_type=file_ext.replace(".", ""),
        raw_text=raw_text,
        parsed_data=parsed_data,
        is_verified=False,
        version=new_version,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Update candidate profile with parsed resume facts
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)
        db.add(profile)

    if parsed_data.get("full_name") and not profile.full_name:
        profile.full_name = parsed_data["full_name"]
    if parsed_data.get("email") and not profile.email:
        profile.email = parsed_data["email"]
    if parsed_data.get("phone") and not profile.phone:
        profile.phone = parsed_data["phone"]
    if parsed_data.get("location") and not profile.location:
        profile.location = parsed_data["location"]
    if parsed_data.get("summary") and (not profile.summary or len(profile.summary) < 20):
        profile.summary = parsed_data["summary"]
    if parsed_data.get("skills"):
        profile.skills = parsed_data["skills"]
    if parsed_data.get("experience"):
        profile.experience = parsed_data["experience"]
    if parsed_data.get("education"):
        profile.education = parsed_data["education"]
    if parsed_data.get("total_experience_years"):
        profile.total_experience_years = parsed_data["total_experience_years"]
    db.commit()

    return resume


@router.get("/", response_model=list[ResumeListResponse])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all resumes uploaded by the current user."""
    resumes = db.scalars(
        select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.version.desc())
    ).all()
    return resumes


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed parsed data of a specific resume."""
    resume = db.scalar(
        select(Resume).where((Resume.id == resume_id) & (Resume.user_id == current_user.id))
    )
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a resume."""
    resume = db.scalar(
        select(Resume).where((Resume.id == resume_id) & (Resume.user_id == current_user.id))
    )
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    
    if os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except OSError:
            pass

    db.delete(resume)
    db.commit()
    return None


@router.get("/{resume_id}/download")
def download_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the uploaded resume file with cloud-resilient auto-generation."""
    resume = db.scalar(
        select(Resume).where((Resume.id == resume_id) & (Resume.user_id == current_user.id))
    )
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # If physical file exists on disk, serve it directly
    if resume.file_path and os.path.exists(resume.file_path):
        media_type = "application/pdf" if (resume.file_type or "").lower() == "pdf" else "application/octet-stream"
        return FileResponse(
            path=resume.file_path,
            filename=resume.filename or "Master_Resume.pdf",
            media_type=media_type,
        )

    # Cloud Resilience: If physical file was wiped on container restart (ephemeral disk),
    # dynamically regenerate the Master Resume PDF from candidate profile facts so download NEVER fails
    profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
    if not profile:
        profile = CandidateProfile(user_id=current_user.id)

    from app.services.tailoring.resume_pdf_generator import tailored_pdf_generator
    safe_filename = resume.filename if (resume.filename and resume.filename.lower().endswith(".pdf")) else "Master_Resume.pdf"
    generated_path = tailored_pdf_generator.generate_master_resume_pdf(
        profile=profile,
        resume=resume,
        output_filename=safe_filename,
    )
    resume.file_path = str(generated_path)
    resume.file_type = "pdf"
    db.commit()

    return FileResponse(
        path=str(generated_path),
        filename=safe_filename,
        media_type="application/pdf",
    )


# Plural alias router to ensure /api/v1/resumes/{id}/download also works seamlessly
resumes_alias_router = APIRouter(prefix="/resumes", tags=["resumes-alias"])


@resumes_alias_router.get("/{resume_id}/download")
def download_resume_alias(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Plural endpoint alias for downloading resume."""
    return download_resume(resume_id=resume_id, current_user=current_user, db=db)


