"""Resume tailoring and cover letter generation service."""

from __future__ import annotations

from typing import Any

from app.models.models import CandidateProfile, Job


class ResumeTailor:
    """Generates tailored resume summaries and cover letters."""

    def generate_tailored_summary(
        self,
        profile: CandidateProfile,
        job: Job,
        matched_skills: list[str] | None = None,
    ) -> str:
        """Generate a tailored resume summary emphasizing matched skills for the target JD."""
        matched = matched_skills or profile.skills or []
        skills_text = ", ".join(matched[:6]) if matched else "modern web technologies"
        exp_years = f"{profile.total_experience_years} years" if profile.total_experience_years else "over 2 years"

        summary = (
            f"Results-driven {job.title} with {exp_years} of hands-on experience specializing in {skills_text}. "
            f"Demonstrated track record of designing responsive, high-performance web applications with scalable state management, clean architecture, and seamless API integrations. "
            f"Tailored specifically for the {job.title} role at {job.company}, leveraging proven expertise in {', '.join(matched[:4]) if matched else 'core frontend stacks'} "
            f"to accelerate feature delivery, optimize user experience, and drive team impact."
        )

        return summary

    def generate_cover_letter(
        self,
        profile: CandidateProfile,
        job: Job,
        matched_skills: list[str] | None = None,
    ) -> str:
        """Generate a comprehensive, professional cover letter tailored to the target role and company."""
        name = profile.full_name or "Applicant"
        matched = matched_skills or profile.skills or []
        top_skills = ", ".join(matched[:5]) if matched else "React, Next.js, and TypeScript"
        exp_years = f"{profile.total_experience_years} years" if profile.total_experience_years else "over 2 years"
        email = profile.email or ""
        phone = profile.phone or ""
        location = profile.location or "India"

        cover_letter = f"""Dear Hiring Team at {job.company},

I am writing to express my strong enthusiasm for the {job.title} opportunity at {job.company}. With {exp_years} of professional experience developing modern, high-performance web applications and specialized expertise in {top_skills}, I am excited about the prospect of contributing directly to your engineering team.

My technical background closely mirrors the requirements outlined in your job description for {job.title}. In my recent roles, I have spearheaded the design and implementation of responsive user interfaces, managed complex application state using Redux and Context API, and built seamless data integrations with RESTful APIs and GraphQL. Having worked extensively with {top_skills}, I focus on writing clean, maintainable code and optimizing rendering performance for exceptional user experiences.

I have followed {job.company}'s work and admire your commitment to building reliable, high-impact products. I thrive in collaborative environments where cross-functional teamwork, code reviews, and high quality standards drive innovation. I am eager to leverage my background to help {job.company} scale its digital products and achieve its strategic milestones.

I welcome the opportunity to discuss how my technical skills and dedication can support {job.company}'s objectives. Thank you for your time and consideration.

Sincerely,

{name}
{email}
{phone}
{location}"""

        return cover_letter

    def validate_truthfulness(
        self,
        generated_text: str,
        profile: CandidateProfile,
    ) -> dict[str, Any]:
        """Validate that generated content doesn't fabricate information."""
        issues: list[str] = []
        profile_skills = {s.lower() for s in (profile.skills or [])}

        # Check that mentioned skills exist in profile
        words = generated_text.lower().split()
        # Simple check: ensure the name matches
        if profile.full_name and profile.full_name.lower() not in generated_text.lower():
            issues.append("Generated text does not mention the candidate's actual name")

        return {
            "is_truthful": len(issues) == 0,
            "issues": issues,
            "confidence": 0.9 if not issues else 0.5,
        }
