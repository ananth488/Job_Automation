"""Job matching service — scores jobs against candidate profiles."""

from __future__ import annotations

import re
from typing import Any

from app.models.models import CandidateProfile, Job, Preference


class MatchResult:
    """Result of matching a job against a candidate profile."""

    def __init__(
        self,
        overall_score: float = 0.0,
        skills_score: float = 0.0,
        experience_score: float = 0.0,
        location_score: float = 0.0,
        salary_score: float = 0.0,
        role_fit_score: float = 0.0,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
        explanation: str = "",
    ):
        self.overall_score = overall_score
        self.skills_score = skills_score
        self.experience_score = experience_score
        self.location_score = location_score
        self.salary_score = salary_score
        self.role_fit_score = role_fit_score
        self.matched_skills = matched_skills or []
        self.missing_skills = missing_skills or []
        self.explanation = explanation


class JobMatcher:
    """Matches jobs against candidate profiles using keyword / heuristic scoring."""

    # Weights for each scoring dimension
    WEIGHTS = {
        "skills": 0.35,
        "experience": 0.20,
        "location": 0.15,
        "salary": 0.10,
        "role_fit": 0.20,
    }

    def match(
        self,
        job: Job,
        profile: CandidateProfile,
        preferences: Preference | None = None,
    ) -> MatchResult:
        """Score a job against the candidate profile and preferences."""
        skills_score, matched, missing = self._score_skills(job, profile)
        experience_score = self._score_experience(job, profile)
        location_score = self._score_location(job, profile, preferences)
        salary_score = self._score_salary(job, preferences)
        role_fit_score = self._score_role_fit(job, preferences, profile)

        overall = (
            self.WEIGHTS["skills"] * skills_score
            + self.WEIGHTS["experience"] * experience_score
            + self.WEIGHTS["location"] * location_score
            + self.WEIGHTS["salary"] * salary_score
            + self.WEIGHTS["role_fit"] * role_fit_score
        )

        explanation_parts: list[str] = []
        if matched:
            explanation_parts.append(f"Matched skills: {', '.join(matched[:10])}")
        if missing:
            explanation_parts.append(f"Missing skills: {', '.join(missing[:5])}")
        explanation_parts.append(f"Overall fit: {overall:.0f}%")

        return MatchResult(
            overall_score=round(overall, 1),
            skills_score=round(skills_score, 1),
            experience_score=round(experience_score, 1),
            location_score=round(location_score, 1),
            salary_score=round(salary_score, 1),
            role_fit_score=round(role_fit_score, 1),
            matched_skills=matched,
            missing_skills=missing,
            explanation=". ".join(explanation_parts),
        )

    def _normalize(self, s: str) -> str:
        cleaned = s.lower().strip()
        cleaned = re.sub(r'[\s\-_.]+', '', cleaned)
        synonyms = {
            # Tech
            "reactjs": "react",
            "react": "react",
            "nextjs": "nextjs",
            "next": "nextjs",
            "typescript": "typescript",
            "ts": "typescript",
            "javascript": "javascript",
            "js": "javascript",
            "tailwindcss": "tailwind",
            "tailwind": "tailwind",
            "restapi": "restapi",
            "restfulapi": "restapi",
            "rest": "restapi",
            "html5": "html",
            "html": "html",
            "css3": "css",
            "css": "css",
            "fastapi": "fastapi",
            "postgresql": "postgres",
            "postgres": "postgres",
            # Medical Coding
            "icd10cm": "icd10",
            "icd10pcs": "icd10",
            "icd10": "icd10",
            "cpt4": "cpt",
            "cpt": "cpt",
            "hcpcslevelii": "hcpcs",
            "hcpcs": "hcpcs",
            "cpcaapc": "cpc",
            "cpc": "cpc",
            "ccsahima": "ccs",
            "ccs": "ccs",
            "revenuecyclemanagementrcm": "rcm",
            "revenuecyclemanagement": "rcm",
            "rcm": "rcm",
            "medicalcoding": "medicalcoding",
            "medicalbilling": "medicalbilling",
            "epicsystems": "epic",
            "epic": "epic",
            "cerneremr": "cerner",
            "cerner": "cerner",
            "hipaa": "hipaa",
            "hipaaguidelines": "hipaa",
            # Finance
            "tallyprime": "tally",
            "tallyerp9": "tally",
            "tallyerp": "tally",
            "tally": "tally",
            "gstfiling": "gst",
            "gst": "gst",
            "tdsreturn": "tds",
            "tds": "tds",
            "sapfico": "sapfico",
            "sap": "sap",
            "financialaccounting": "accounting",
            "auditing": "audit",
            "internalaudit": "audit",
            # HR
            "talentacquisition": "recruitment",
            "technicalrecruitment": "recruitment",
            "hrms": "hrms",
            "hris": "hrms",
        }
        return synonyms.get(cleaned, cleaned)

    def _score_skills(
        self, job: Job, profile: CandidateProfile
    ) -> tuple[float, list[str], list[str]]:
        """Score based on skills overlap with synonym matching."""
        job_raw = job.skills_required or []
        candidate_raw = profile.skills or []

        candidate_norm_map = {self._normalize(s): s for s in candidate_raw}

        if not job_raw:
            desc_lower = (job.description or "").lower()
            matched = [s for s in candidate_raw if self._normalize(s) in desc_lower]
            return (75.0, matched, []) if matched else (50.0, [], [])

        matched = []
        missing = []

        for req in job_raw:
            norm_req = self._normalize(req)
            if norm_req in candidate_norm_map:
                matched.append(req)
            else:
                missing.append(req)

        score = (len(matched) / max(len(job_raw), 1)) * 100
        return score, matched, missing

    def _score_experience(self, job: Job, profile: CandidateProfile) -> float:
        """Score based on experience years fit."""
        candidate_exp = profile.total_experience_years
        if candidate_exp is None:
            return 60.0  # neutral score if unknown

        job_min = job.experience_min or 0
        job_max = job.experience_max

        if job_max is None:
            job_max = job_min + 5

        if job_min <= candidate_exp <= job_max:
            return 100.0
        elif candidate_exp < job_min:
            gap = job_min - candidate_exp
            return max(0, 100 - gap * 20)
        else:
            gap = candidate_exp - job_max
            return max(40, 100 - gap * 10)  # overqualified is less bad

    def _score_location(
        self, job: Job, profile: CandidateProfile, preferences: Preference | None
    ) -> float:
        """Score based on location match against preferences and profile locations."""
        if job.work_mode and job.work_mode.lower() == "remote":
            return 100.0

        pref_locations = [loc.lower().strip() for loc in (preferences.locations if preferences and preferences.locations else [])]
        if not pref_locations and profile.preferred_locations:
            pref_locations = [loc.lower().strip() for loc in profile.preferred_locations]

        candidate_location = (profile.location or "").lower().strip()
        job_location = (job.location or "").lower().strip()

        if not job_location:
            return 75.0

        # Check if job location matches any preferred location
        for loc in pref_locations:
            if loc in job_location or job_location in loc:
                return 100.0

        # Check if candidate location matches
        if candidate_location and (
            candidate_location in job_location or job_location in candidate_location
        ):
            return 90.0

        return 45.0

    def _score_salary(self, job: Job, preferences: Preference | None) -> float:
        """Score based on salary range compatibility."""
        if not preferences or (not preferences.min_salary and not preferences.max_salary):
            return 70.0  # neutral

        if not job.salary_min and not job.salary_max:
            return 60.0  # unknown salary

        job_max = job.salary_max or job.salary_min or 0
        job_min = job.salary_min or 0
        pref_min = preferences.min_salary or 0
        pref_max = preferences.max_salary or float("inf")

        if job_max >= pref_min:
            return 100.0
        else:
            gap_pct = (pref_min - job_max) / max(pref_min, 1) * 100
            return max(0, 100 - gap_pct * 2)

    def _score_role_fit(self, job: Job, preferences: Preference | None, profile: CandidateProfile | None = None) -> float:
        """Score based on how well the job title matches desired roles, past experience titles, or profile summary."""
        target_roles: list[str] = []
        if preferences and preferences.desired_roles:
            target_roles.extend(preferences.desired_roles)
        elif preferences and preferences.keywords:
            target_roles.extend(preferences.keywords)

        if profile:
            # Also extract target roles from candidate's past work experience titles
            if profile.experience and isinstance(profile.experience, list):
                for exp in profile.experience:
                    if isinstance(exp, dict) and exp.get("title"):
                        target_roles.append(exp["title"])

            summary = (profile.summary or "").lower()
            skills_blob = " ".join(profile.skills or []).lower()

            if any(k in summary or k in skills_blob for k in ["medical cod", "cpc", "icd-10", "cpt", "inpatient", "outpatient", "rcm"]):
                target_roles.extend([
                    "Medical Coder", "Senior Medical Coder", "Certified Professional Coder",
                    "Inpatient Medical Coder", "Outpatient Coder", "CPC Coder", "Medical Billing Specialist"
                ])
            elif any(k in summary or k in skills_blob for k in ["accountant", "tally", "gst", "auditing", "taxation"]):
                target_roles.extend(["Accountant", "Senior Accountant", "Financial Analyst", "Tax Associate", "Accounts Executive"])
            elif any(k in summary or k in skills_blob for k in ["talent acquisition", "recruiter", "recruitment", "hr operations"]):
                target_roles.extend(["Talent Acquisition Specialist", "Technical Recruiter", "HR Operations", "HR Generalist"])
            elif "frontend" in summary or "react" in summary or "next.js" in summary:
                target_roles.extend(["Frontend Developer", "React Developer", "Software Engineer", "Web Developer"])
            elif "full stack" in summary:
                target_roles.extend(["Full Stack Developer", "Software Engineer"])

        if not target_roles:
            return 70.0

        job_title = (job.title or "").lower().strip()

        best_score = 0.0
        for role in target_roles:
            role_lower = role.lower().strip()
            role_words = role_lower.split()
            title_words = job_title.split()
            matching_words = sum(1 for w in role_words if w in title_words or any(w in tw for tw in title_words))
            if role_words:
                score = (matching_words / len(role_words)) * 100
                best_score = max(best_score, score)

            if role_lower in job_title or job_title in role_lower:
                best_score = max(best_score, 95.0)

        return best_score if best_score > 0 else 40.0


def match_job_to_profile(
    job: Job,
    profile: Any,
    preferences: Preference | None = None,
) -> MatchResult:
    """Helper function to match a job to candidate profile."""
    matcher = JobMatcher()
    return matcher.match(job, profile, preferences)

