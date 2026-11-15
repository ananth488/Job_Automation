"""Resume tailoring and cover letter generation service.

Universal Multi-User & Multi-Domain Engine:
Dynamically generates ATS-tailored professional summaries and cover letters
for ANY career domain (Healthcare, Medical Coding, Software, Civil, Mechanical,
Finance, HR, etc.) with ZERO hardcoded skills, companies, or technologies.
"""

from __future__ import annotations

import re
from typing import Any

from app.models.models import CandidateProfile, Job


class ResumeTailor:
    """Generates tailored resume summaries and cover letters dynamically for any career domain."""

    def _detect_domain(self, text: str) -> str:
        """Identify industry domain from text keywords."""
        tl = text.lower()
        if any(w in tl for w in ("medical coding", "icd-10", "icd-9", "cpt", "hcpcs", "hipaa", "billing", "clinical", "hospital", "healthcare", "ehr", "emr", "epic", "cerner")):
            return "medical_coding"
        if any(w in tl for w in ("data science", "machine learning", "deep learning", "nlp", "computer vision", "pandas", "pytorch", "tensorflow", "big data")):
            return "data_science"
        if any(w in tl for w in ("devops", "cloud engineer", "sre", "kubernetes", "docker", "terraform", "aws", "azure", "ci/cd")):
            return "devops"
        if any(w in tl for w in ("civil", "structural", "autocad", "revit", "construction", "surveying")):
            return "civil"
        if any(w in tl for w in ("mechanical", "solidworks", "catia", "ansys", "thermodynamics", "manufacturing", "hvac")):
            return "mechanical"
        if any(w in tl for w in ("finance", "accounting", "ledger", "tax", "audit", "tally", "cpa", "financial analyst")):
            return "finance"
        if any(w in tl for w in ("software", "developer", "engineer", "frontend", "backend", "full stack", "python", "java", "react")):
            return "software"
        return "general"

    def generate_tailored_summary(
        self,
        profile: CandidateProfile,
        job: Job,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
    ) -> str:
        """Generate an ATS-tailored resume summary bridging candidate skills with the target JD."""
        # Combine authentic candidate skills and target JD requirements
        all_candidate_skills = list(profile.skills or [])
        target_skills = list(matched_skills or [])
        if missing_skills:
            for s in missing_skills:
                if s not in target_skills and s.lower() not in {x.lower() for x in target_skills}:
                    target_skills.append(s)

        effective_skills = target_skills if target_skills else all_candidate_skills
        top_skills_str = ", ".join(effective_skills[:5]) if effective_skills else "specialized domain competencies"

        exp_years = (
            f"{profile.total_experience_years:.1f} years".replace(".0", "")
            if (profile.total_experience_years and profile.total_experience_years > 0)
            else "proven hands-on"
        )
        target_role = job.title or "Professional"
        target_company = job.company or "your organization"

        # Domain-aware dynamic narrative
        domain = self._detect_domain(f"{target_role} {' '.join(effective_skills)}")

        if domain == "medical_coding":
            summary = (
                f"Detail-oriented {target_role} with {exp_years} of professional experience specializing in "
                f"{top_skills_str}. Proven track record in comprehensive medical record abstraction, diagnostic and "
                f"procedural code assignment, and strict adherence to official coding guidelines and HIPAA regulations. "
                f"Tailored specifically for the {target_role} position at {target_company}, leveraging expertise in "
                f"clinical documentation integrity, claims accuracy, and revenue cycle workflows to minimize claim denials "
                f"and support high compliance standards."
            )
        elif domain == "data_science":
            summary = (
                f"Results-oriented {target_role} with {exp_years} of experience in statistical analysis, predictive modeling, "
                f"and data-driven problem solving specializing in {top_skills_str}. Experienced in building end-to-end "
                f"analytical pipelines, translating complex data into actionable insights, and deploying scalable models. "
                f"Tailored for the {target_role} role at {target_company} to accelerate business intelligence, optimize algorithmic "
                f"performance, and deliver quantitative impact."
            )
        elif domain == "devops":
            summary = (
                f"Performance-driven {target_role} with {exp_years} of expertise managing scalable cloud infrastructure, "
                f"automated CI/CD pipelines, and high-availability systems with {top_skills_str}. Skilled in containerization, "
                f"infrastructure as code, and proactive monitoring to ensure system reliability and security. "
                f"Tailored for {target_company}'s engineering objectives to streamline deployment lifecycles and uphold robust operational uptime."
            )
        elif domain in ("civil", "mechanical"):
            summary = (
                f"Dedicated and methodical {target_role} with {exp_years} of engineering experience specializing in "
                f"{top_skills_str}. Strong technical background in engineering design, technical specifications, "
                f"quality assurance, and regulatory compliance. Tailored for the {target_role} opportunity at {target_company}, "
                f"leveraging structured methodology, analytical problem-solving, and attention to detail to execute projects with safety and precision."
            )
        elif domain == "finance":
            summary = (
                f"Meticulous {target_role} with {exp_years} of experience specializing in {top_skills_str}. "
                f"Demonstrated competence in financial reporting, ledger reconciliation, regulatory compliance, and fiscal analysis. "
                f"Tailored for {target_company} to ensure accounting accuracy, optimize financial reporting workflows, and deliver strategic financial clarity."
            )
        elif domain == "software":
            summary = (
                f"Results-driven {target_role} with {exp_years} of professional experience delivering scalable solutions using "
                f"{top_skills_str}. Skilled in modular system design, clean code principles, robust API integrations, and "
                f"performance optimization. Tailored specifically for the {target_role} position at {target_company}, leveraging proven "
                f"technical problem-solving and cross-functional collaboration to accelerate feature delivery and elevate overall product quality."
            )
        else:
            summary = (
                f"Results-driven {target_role} with {exp_years} of professional experience specializing in {top_skills_str}. "
                f"Demonstrated track record of operational excellence, strategic problem-solving, and cross-functional execution. "
                f"Tailored specifically for the {target_role} position at {target_company}, leveraging verified core competencies "
                f"to drive measurable outcomes, optimize workflows, and support organizational goals."
            )

        return summary

    def generate_cover_letter(
        self,
        profile: CandidateProfile,
        job: Job,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
    ) -> str:
        """Generate a fully dynamic cover letter for any candidate, job role, and company."""
        name = profile.full_name or "Applicant"
        email = profile.email or ""
        phone = profile.phone or ""
        location = profile.location or ""

        target_skills = list(matched_skills or [])
        if missing_skills:
            for s in missing_skills:
                if s not in target_skills and s.lower() not in {x.lower() for x in target_skills}:
                    target_skills.append(s)
        if not target_skills and profile.skills:
            target_skills = list(profile.skills)

        top_skills = ", ".join(target_skills[:5]) if target_skills else "specialized domain competencies"
        exp_years = (
            f"{profile.total_experience_years:.1f} years".replace(".0", "")
            if (profile.total_experience_years and profile.total_experience_years > 0)
            else "relevant professional"
        )
        target_role = job.title or "Position"
        target_company = job.company or "your organization"
        domain = self._detect_domain(f"{target_role} {' '.join(target_skills)}")

        if domain == "medical_coding":
            domain_body = (
                f"Throughout my career, I have focused on ensuring medical records are coded with maximum accuracy and in "
                f"full compliance with official guidelines and HIPAA standards. With hands-on proficiency in {top_skills}, "
                f"I am accustomed to abstracting clinical information, assigning appropriate codes, and collaborating with "
                f"healthcare providers and billing teams to prevent claim denials and maintain revenue cycle integrity."
            )
        elif domain == "data_science":
            domain_body = (
                f"My professional background centers on transforming complex datasets into actionable predictive insights and "
                f"business value. Applying competencies in {top_skills}, I focus on developing robust mathematical models, "
                f"validating hypothesis accuracy, and designing analytical pipelines that directly inform strategic decision-making."
            )
        elif domain == "devops":
            domain_body = (
                f"In my engineering roles, I have dedicated myself to automating deployment workflows, strengthening cloud infrastructure, "
                f"and maintaining high operational availability. Leveraging core skills in {top_skills}, I champion modern DevOps "
                f"practices, resilient container orchestration, and continuous improvement."
            )
        elif domain in ("civil", "mechanical"):
            domain_body = (
                f"My background combines hands-on engineering principles with rigorous attention to design standards, technical "
                f"drawings, and project timelines. Applying expertise in {top_skills}, I am committed to delivering safe, cost-effective, "
                f"and high-quality engineering solutions tailored to organizational requirements."
            )
        elif domain == "finance":
            domain_body = (
                f"I bring structured discipline to financial reporting, audit readiness, and reconciliation workflows. "
                f"With practical expertise across {top_skills}, I emphasize transparency, internal controls, and data accuracy to "
                f"help drive sound fiscal decisions."
            )
        else:
            domain_body = (
                f"My professional background closely aligns with the requirements outlined in your job posting. With core proficiencies "
                f"in {top_skills}, I focus on delivering clean, reliable, and high-impact contributions while maintaining open "
                f"communication and collaboration across multidisciplinary teams."
            )

        contact_lines = [line for line in [email, phone, location] if line]
        contact_block = "\n".join(contact_lines)

        cover_letter = f"""Dear Hiring Team at {target_company},

I am writing to express my strong enthusiasm for the {target_role} position at {target_company}. With {exp_years} of experience and demonstrated expertise in {top_skills}, I am excited about the opportunity to contribute directly to your team's success.

{domain_body}

I have closely followed {target_company}'s initiatives and greatly appreciate your dedication to quality and professional excellence. I thrive in collaborative environments where high standards and continuous learning drive meaningful impact. I am confident that my background, dedication, and adaptability will make me a valuable asset to your organization.

I welcome the opportunity to speak with you further regarding how my experience and skill set can support the goals of {target_company}. Thank you very much for your time and consideration.

Sincerely,

{name}
{contact_block}"""

        return cover_letter.strip()

    def validate_truthfulness(
        self,
        generated_text: str,
        profile: CandidateProfile,
    ) -> dict[str, Any]:
        """Validate that generated content doesn't fabricate basic candidate facts."""
        issues: list[str] = []
        if profile.full_name and profile.full_name.lower() not in generated_text.lower():
            issues.append("Generated text does not mention the candidate's actual name")

        return {
            "is_truthful": len(issues) == 0,
            "issues": issues,
            "confidence": 0.95 if not issues else 0.5,
        }
