"""ATS-Compliant Tailored Resume PDF Generator (Universal Engine).

Purely Dynamic Multi-User & Multi-Domain Engine:
Preserves any candidate's authentic resume structure, experience, education,
and certifications dynamically, while bridging the target Job Description (JD)
by incorporating matched and missing required skills into the ATS-optimized resume.
Zero hardcoded candidate names, companies, or technologies.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.models import CandidateProfile, Job, Resume


def safe_xml(text: str | None) -> str:
    """Safely escape text for ReportLab Paragraphs while preserving standard formatting."""
    if not text:
        return ""
    # Convert special XML characters to valid entities
    s = str(text)
    # First unescape to avoid double-escaping if already escaped
    s = html.unescape(s)
    # Escape &, <, >
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s


def extract_clean_bullets(desc: str) -> list[str]:
    """Extract clean bullet points from a description string without splitting on hyphens inside words."""
    if not desc:
        return []
    lines = []
    # Split on newlines, or explicit bullet characters (▸, •, *)
    # Do NOT split on bare hyphen unless it is at the start of a line or after a newline
    raw_chunks = re.split(r"[\n\r]+|(?:^|[\n\r\s]+)[▸•*]\s*|(?:^|[\n\r]+)\s*-\s*", desc)
    for raw in raw_chunks:
        cleaned = raw.strip().lstrip("▸•-* ").strip()
        if len(cleaned) > 8:
            lines.append(cleaned)
    return lines[:4]


class TailoredResumePdfGenerator:
    """Generates ATS-optimized, high-impact PDF resumes dynamically for any candidate and any JD."""

    def __init__(self, output_dir: str | Path | None = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent.parent.parent / "uploads" / "tailored"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_styles(self) -> dict[str, ParagraphStyle]:
        """Create isolated ReportLab paragraph styles without style sheet pollution."""
        styles = getSampleStyleSheet()

        return {
            "name": ParagraphStyle(
                "DynamicCandidateName",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=21,
                textColor=colors.HexColor("#0F172A"),
                alignment=TA_CENTER,
            ),
            "title_sub": ParagraphStyle(
                "DynamicTitleSub",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9.5,
                leading=12.5,
                textColor=colors.HexColor("#334155"),
                alignment=TA_CENTER,
            ),
            "contact": ParagraphStyle(
                "DynamicContactInfo",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.3,
                leading=11.5,
                textColor=colors.HexColor("#475569"),
                alignment=TA_CENTER,
            ),
            "section_heading": ParagraphStyle(
                "DynamicSectionHeading",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
                textColor=colors.HexColor("#0F172A"),
                spaceBefore=5,
                spaceAfter=2,
                leftIndent=0,
                alignment=TA_LEFT,
            ),
            "body": ParagraphStyle(
                "DynamicBodyText",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=12,
                textColor=colors.HexColor("#1E293B"),
                leftIndent=0,
                alignment=TA_LEFT,
            ),
            "skill": ParagraphStyle(
                "DynamicSkillLine",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=12,
                textColor=colors.HexColor("#1E293B"),
                leftIndent=0,
                spaceAfter=1.5,
                alignment=TA_LEFT,
            ),
            "job_title": ParagraphStyle(
                "DynamicJobTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#0F172A"),
                leftIndent=0,
                alignment=TA_LEFT,
            ),
            "job_meta": ParagraphStyle(
                "DynamicJobMeta",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8.2,
                leading=11.5,
                textColor=colors.HexColor("#475569"),
                alignment=TA_RIGHT,
            ),
            "bullet": ParagraphStyle(
                "DynamicBulletPoint",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.4,
                leading=11.8,
                textColor=colors.HexColor("#334155"),
                leftIndent=11,
                firstLineIndent=-7,
                spaceAfter=1.5,
                alignment=TA_LEFT,
            ),
            "project_tech": ParagraphStyle(
                "DynamicProjectTech",
                parent=styles["Normal"],
                fontName="Helvetica-Oblique",
                fontSize=8.2,
                leading=11,
                textColor=colors.HexColor("#475569"),
                leftIndent=0,
                spaceAfter=1.5,
                alignment=TA_LEFT,
            ),
        }

    def _make_hr(self) -> HRFlowable:
        return HRFlowable(
            width="100%",
            thickness=0.75,
            color=colors.HexColor("#94A3B8"),
            spaceBefore=1,
            spaceAfter=3.5,
            hAlign="LEFT",
        )

    def _group_skills_dynamically(self, skills: list[str]) -> list[tuple[str, list[str]]]:
        """Organize any list of candidate/job skills into clean, domain-appropriate categories."""
        if not skills:
            return []

        # Deduplicate while preserving order & casing
        seen = set()
        deduped = []
        for s in skills:
            if not s or not isinstance(s, str):
                continue
            clean = s.strip()
            if len(clean) < 2:
                continue
            k = clean.lower()
            if k not in seen:
                seen.add(k)
                deduped.append(clean)

        # Detect domain flavor
        combined_text = " ".join(deduped).lower()

        # 1. Medical Coding / Healthcare
        if any(w in combined_text for w in ("icd-10", "icd-9", "cpt", "hcpcs", "medical coding", "hipaa", "billing", "cpc", "ccs", "ehr", "emr", "epic", "cerner", "rcm")):
            cat_coding = []
            cat_clinical = []
            cat_systems = []
            cat_compliance = []

            for s in deduped:
                sl = s.lower()
                if any(w in sl for w in ("icd", "cpt", "hcpcs", "drg", "coding", "classification")):
                    cat_coding.append(s)
                elif any(w in sl for w in ("epic", "cerner", "meditech", "ehr", "emr", "3m", "software", "tool")):
                    cat_systems.append(s)
                elif any(w in sl for w in ("hipaa", "compliance", "audit", "rcm", "billing", "revenue", "denial", "guideline")):
                    cat_compliance.append(s)
                else:
                    cat_clinical.append(s)

            results = []
            if cat_coding:
                results.append(("Coding Classifications & Nomenclature", cat_coding))
            if cat_clinical:
                results.append(("Clinical Knowledge & Specialties", cat_clinical))
            if cat_systems:
                results.append(("Healthcare Systems & EHR Platforms", cat_systems))
            if cat_compliance:
                results.append(("Compliance, RCM & Industry Standards", cat_compliance))
            if results:
                return results

        # 2. Software / IT
        if any(w in combined_text for w in ("python", "javascript", "react", "sql", "java", "html", "css", "docker", "aws", "git", "api")):
            cat_languages = []
            cat_frameworks = []
            cat_data_cloud = []
            cat_tools = []

            for s in deduped:
                sl = s.lower()
                if any(w in sl for w in ("javascript", "typescript", "python", "java", "c++", "c#", "html", "css", "sql", "bash")):
                    cat_languages.append(s)
                elif any(w in sl for w in ("react", "next", "node", "express", "django", "fastapi", "spring", "vue", "angular", "redux")):
                    cat_frameworks.append(s)
                elif any(w in sl for w in ("postgres", "mysql", "mongodb", "aws", "azure", "gcp", "docker", "kubernetes", "cloud")):
                    cat_data_cloud.append(s)
                else:
                    cat_tools.append(s)

            results = []
            if cat_languages:
                results.append(("Languages & Core", cat_languages))
            if cat_frameworks:
                results.append(("Frameworks & Architecture", cat_frameworks))
            if cat_data_cloud:
                results.append(("Databases, Cloud & Infrastructure", cat_data_cloud))
            if cat_tools:
                results.append(("Tools, Practices & Methodologies", cat_tools))
            if results:
                return results

        # 3. Universal / General Domain Grouping (Dynamic Chunking)
        # Group evenly without inventing fake categories
        if len(deduped) <= 8:
            return [("Core Competencies & Domain Expertise", deduped)]
        elif len(deduped) <= 16:
            mid = (len(deduped) + 1) // 2
            return [
                ("Core Competencies & Methodologies", deduped[:mid]),
                ("Technical Skills & Tools", deduped[mid:]),
            ]
        else:
            third = (len(deduped) + 2) // 3
            return [
                ("Core Competencies & Domain Expertise", deduped[:third]),
                ("Specialized Technical Skills", deduped[third : 2 * third]),
                ("Tools, Software & Standards", deduped[2 * third :]),
            ]

    def generate_pdf(
        self,
        profile: CandidateProfile,
        job: Job,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
        tailored_summary: str | None = None,
        output_filename: str | None = None,
        original_resume: Resume | None = None,
    ) -> Path:
        """Generate and save the tailored resume PDF dynamically for ANY user and domain."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not output_filename:
            sanitized_comp = "".join(c for c in (job.company or "job") if c.isalnum() or c in ("-", "_")).lower()
            output_filename = f"tailored_resume_u{profile.user_id}_j{job.id}_{sanitized_comp}.pdf"

        file_path = self.output_dir / output_filename

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=32,
            bottomMargin=32,
        )

        styles = self._build_styles()
        elements = []

        # 1. Candidate Name (100% Dynamic from profile)
        full_name = profile.full_name or (profile.email.split("@")[0].replace(".", " ").title() if profile.email else "Candidate")
        elements.append(Paragraph(safe_xml(full_name).upper(), styles["name"]))
        elements.append(Spacer(1, 1.5))

        # Dynamic Subtitle: Adapt to target domain and candidate's experience
        candidate_primary_title = None
        if profile.experience and isinstance(profile.experience, list) and len(profile.experience) > 0:
            candidate_primary_title = profile.experience[0].get("title")
        if not candidate_primary_title and original_resume and original_resume.parsed_data:
            orig_exp = original_resume.parsed_data.get("experience")
            if orig_exp and isinstance(orig_exp, list) and len(orig_exp) > 0:
                candidate_primary_title = orig_exp[0].get("title")
        if not candidate_primary_title:
            candidate_primary_title = job.title or "Professional"

        elements.append(Paragraph(safe_xml(candidate_primary_title), styles["title_sub"]))
        elements.append(Spacer(1, 2))

        # Dynamic Contact Line (Only include actual data; no hardcoded defaults)
        contact_parts = []
        if profile.location:
            contact_parts.append(profile.location.strip())
        if profile.email:
            contact_parts.append(profile.email.strip())
        if profile.phone:
            contact_parts.append(profile.phone.strip())

        if contact_parts:
            contact_line_1 = " &nbsp;|&nbsp; ".join([safe_xml(cp) for cp in contact_parts])
            elements.append(Paragraph(contact_line_1, styles["contact"]))
            elements.append(Spacer(1, 1))

        # Optional Profile Links (Only if present)
        links = []
        if profile.linkedin_url:
            links.append(f"<a href='{safe_xml(profile.linkedin_url)}'>LinkedIn</a>")
        if profile.github_url:
            links.append(f"<a href='{safe_xml(profile.github_url)}'>GitHub</a>")
        if profile.portfolio_url:
            links.append(f"<a href='{safe_xml(profile.portfolio_url)}'>Portfolio</a>")

        if links:
            elements.append(Paragraph(" &nbsp;|&nbsp; ".join(links), styles["contact"]))
            elements.append(Spacer(1, 3))
        else:
            elements.append(Spacer(1, 2))

        # 2. Professional Summary (Dynamic for candidate domain & target job)
        elements.append(Paragraph("PROFESSIONAL SUMMARY", styles["section_heading"]))
        elements.append(self._make_hr())

        from app.services.tailoring.tailoring import ResumeTailor
        tailor = ResumeTailor()

        if not tailored_summary:
            tailored_summary = tailor.generate_tailored_summary(
                profile=profile,
                job=job,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
            )

        elements.append(Paragraph(safe_xml(tailored_summary), styles["body"]))
        elements.append(Spacer(1, 4))

        # 3. Dynamic Technical & Domain Skills (ATS Bridging: Candidate Skills + Target Missing Skills)
        all_tailored_skills = []
        # Candidate's authentic skills
        if profile.skills:
            all_tailored_skills.extend(profile.skills)
        elif original_resume and original_resume.parsed_data and original_resume.parsed_data.get("skills"):
            all_tailored_skills.extend(original_resume.parsed_data.get("skills"))

        # Job required skills & matched skills
        if matched_skills:
            all_tailored_skills.extend(matched_skills)
        if missing_skills:
            all_tailored_skills.extend(missing_skills)
        if job.skills_required:
            all_tailored_skills.extend(job.skills_required)

        grouped_skills = self._group_skills_dynamically(all_tailored_skills)
        if grouped_skills:
            elements.append(Paragraph("SKILLS &amp; EXPERTISE", styles["section_heading"]))
            elements.append(self._make_hr())
            for cat_title, skill_list in grouped_skills:
                skills_str = ", ".join(skill_list)
                elements.append(
                    Paragraph(f"<b>{safe_xml(cat_title)}:</b> {safe_xml(skills_str)}", styles["skill"])
                )
            elements.append(Spacer(1, 4))

        # 4. Professional Experience (Authentic candidate experience; NO fake companies)
        experiences = None
        if profile.experience and isinstance(profile.experience, list) and len(profile.experience) > 0:
            experiences = profile.experience
        elif original_resume and original_resume.parsed_data and original_resume.parsed_data.get("experience"):
            experiences = original_resume.parsed_data.get("experience")

        if experiences:
            elements.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["section_heading"]))
            elements.append(self._make_hr())

            for exp in experiences:
                exp_title = exp.get("title") or "Professional"
                exp_company = exp.get("company") or exp.get("organization") or ""
                exp_location = exp.get("location") or profile.location or ""
                exp_dates = exp.get("dates") or f"{exp.get('start', '')} – {exp.get('end', '')}".strip(" –")

                title_comp = f"<b>{safe_xml(exp_title)}</b>"
                if exp_company:
                    title_comp += f" &mdash; <i>{safe_xml(exp_company)}</i>"

                date_loc_parts = [safe_xml(p) for p in [exp_dates, exp_location] if p]
                date_loc_str = " | ".join(date_loc_parts)

                header_table = Table(
                    [[
                        Paragraph(title_comp, styles["job_title"]),
                        Paragraph(date_loc_str, styles["job_meta"]),
                    ]],
                    colWidths=[370, 170],
                    hAlign="LEFT",
                )
                header_table.setStyle(
                    TableStyle([
                        ("PADDING", (0, 0), (-1, -1), 0),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ])
                )
                elements.append(header_table)
                elements.append(Spacer(1, 1.5))

                bullets = exp.get("bullets")
                if not bullets and exp.get("description"):
                    bullets = extract_clean_bullets(exp.get("description"))

                if bullets and isinstance(bullets, list):
                    for b in bullets[:4]:
                        elements.append(Paragraph(f"• {safe_xml(b)}", styles["bullet"]))
                elif exp.get("description"):
                    elements.append(Paragraph(safe_xml(exp.get("description")), styles["body"]))

                elements.append(Spacer(1, 2.5))

        # 5. Key Projects (Authentic candidate projects; omitted if none)
        projects = None
        if profile.projects and isinstance(profile.projects, list) and len(profile.projects) > 0:
            projects = profile.projects
        elif original_resume and original_resume.parsed_data and original_resume.parsed_data.get("projects"):
            projects = original_resume.parsed_data.get("projects")

        if projects:
            elements.append(Paragraph("KEY PROJECTS", styles["section_heading"]))
            elements.append(self._make_hr())

            for p in projects[:3]:
                p_name = p.get("name") or "Project"
                p_tech = p.get("tech") or p.get("technologies") or ""
                elements.append(Paragraph(f"<b>{safe_xml(p_name)}</b>", styles["job_title"]))
                if p_tech:
                    elements.append(Paragraph(f"Technologies / Tools: {safe_xml(p_tech)}", styles["project_tech"]))

                p_bullets = p.get("bullets")
                if not p_bullets and p.get("description"):
                    p_bullets = extract_clean_bullets(p.get("description"))

                if p_bullets and isinstance(p_bullets, list):
                    for b in p_bullets[:3]:
                        elements.append(Paragraph(f"• {safe_xml(b)}", styles["bullet"]))
                elif p.get("description"):
                    elements.append(Paragraph(safe_xml(p.get("description")), styles["body"]))

                elements.append(Spacer(1, 2.5))

        # 6. Certifications & Licenses (Essential for Healthcare, Medical Coding, Engineering)
        certs = None
        if profile.certifications and isinstance(profile.certifications, list) and len(profile.certifications) > 0:
            certs = profile.certifications
        elif original_resume and original_resume.parsed_data and original_resume.parsed_data.get("certifications"):
            certs = original_resume.parsed_data.get("certifications")

        if certs:
            elements.append(Paragraph("CERTIFICATIONS &amp; CREDENTIALS", styles["section_heading"]))
            elements.append(self._make_hr())
            for c in certs:
                elements.append(Paragraph(f"• {safe_xml(str(c))}", styles["bullet"]))
            elements.append(Spacer(1, 3))

        # 7. Education (Authentic candidate education)
        education_items = None
        if profile.education and isinstance(profile.education, list) and len(profile.education) > 0:
            education_items = profile.education
        elif original_resume and original_resume.parsed_data and original_resume.parsed_data.get("education"):
            education_items = original_resume.parsed_data.get("education")

        if education_items:
            elements.append(Paragraph("EDUCATION", styles["section_heading"]))
            elements.append(self._make_hr())

            for edu in education_items:
                deg = edu.get("degree") or "Degree"
                inst = edu.get("institution") or edu.get("university") or ""
                yr = edu.get("year") or edu.get("dates") or ""
                parts = [p for p in [f"<b>{safe_xml(deg)}</b>", safe_xml(inst), safe_xml(yr)] if p and p != "<b></b>"]
                elements.append(Paragraph(" &nbsp;|&nbsp; ".join(parts), styles["body"]))

        # Build document
        doc.build(elements)
        return file_path

    def generate_master_resume_pdf(
        self,
        profile: CandidateProfile,
        resume: Resume | None = None,
        output_filename: str | None = None,
    ) -> Path:
        """Generate a clean ATS Master Resume PDF from candidate profile/parsed facts when original file is missing."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not output_filename:
            user_clean = re.sub(r"[^a-zA-Z0-9]", "_", profile.full_name or "Resume").strip("_")
            output_filename = f"Master_Resume_{user_clean}_u{profile.user_id}.pdf"

        file_path = self.output_dir / output_filename

        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=32,
            bottomMargin=32,
        )

        styles = self._build_styles()
        elements = []

        # Name
        full_name = profile.full_name or (profile.email.split("@")[0].replace(".", " ").title() if profile.email else "Candidate")
        elements.append(Paragraph(safe_xml(full_name).upper(), styles["name"]))
        elements.append(Spacer(1, 1.5))

        # Title
        primary_title = "Professional"
        if profile.experience and isinstance(profile.experience, list) and len(profile.experience) > 0:
            primary_title = profile.experience[0].get("title", primary_title)
        elements.append(Paragraph(safe_xml(primary_title), styles["title_sub"]))
        elements.append(Spacer(1, 2))

        # Contact
        contact_parts = []
        if profile.location:
            contact_parts.append(profile.location.strip())
        if profile.email:
            contact_parts.append(profile.email.strip())
        if profile.phone:
            contact_parts.append(profile.phone.strip())

        if contact_parts:
            elements.append(Paragraph(" &nbsp;|&nbsp; ".join([safe_xml(cp) for cp in contact_parts]), styles["contact"]))
            elements.append(Spacer(1, 2))

        # Summary
        summary = profile.summary or (resume.parsed_data.get("summary") if resume and resume.parsed_data else None)
        if summary:
            elements.append(Paragraph("PROFESSIONAL SUMMARY", styles["section_heading"]))
            elements.append(self._make_hr())
            elements.append(Paragraph(safe_xml(summary), styles["body"]))
            elements.append(Spacer(1, 4))

        # Skills
        skills = profile.skills or (resume.parsed_data.get("skills") if resume and resume.parsed_data else None)
        if skills:
            grouped = self._group_skills_dynamically(skills)
            if grouped:
                elements.append(Paragraph("SKILLS &amp; EXPERTISE", styles["section_heading"]))
                elements.append(self._make_hr())
                for cat_title, skill_list in grouped:
                    elements.append(Paragraph(f"<b>{safe_xml(cat_title)}:</b> {safe_xml(', '.join(skill_list))}", styles["skill"]))
                elements.append(Spacer(1, 4))

        # Experience
        experiences = profile.experience or (resume.parsed_data.get("experience") if resume and resume.parsed_data else None)
        if experiences:
            elements.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["section_heading"]))
            elements.append(self._make_hr())
            for exp in experiences:
                exp_title = exp.get("title") or "Professional"
                exp_company = exp.get("company") or ""
                exp_location = exp.get("location") or ""
                exp_dates = exp.get("dates") or f"{exp.get('start', '')} – {exp.get('end', '')}".strip(" –")

                title_comp = f"<b>{safe_xml(exp_title)}</b>"
                if exp_company:
                    title_comp += f" &mdash; <i>{safe_xml(exp_company)}</i>"
                date_loc = " | ".join([safe_xml(p) for p in [exp_dates, exp_location] if p])

                header_table = Table(
                    [[Paragraph(title_comp, styles["job_title"]), Paragraph(date_loc, styles["job_meta"])]],
                    colWidths=[370, 170],
                    hAlign="LEFT",
                )
                header_table.setStyle(
                    TableStyle([
                        ("PADDING", (0, 0), (-1, -1), 0),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ])
                )
                elements.append(header_table)
                elements.append(Spacer(1, 1.5))

                bullets = exp.get("bullets") or (extract_clean_bullets(exp.get("description")) if exp.get("description") else None)
                if bullets and isinstance(bullets, list):
                    for b in bullets[:4]:
                        elements.append(Paragraph(f"• {safe_xml(b)}", styles["bullet"]))
                elif exp.get("description"):
                    elements.append(Paragraph(safe_xml(exp.get("description")), styles["body"]))
                elements.append(Spacer(1, 2.5))

        # Education
        education = profile.education or (resume.parsed_data.get("education") if resume and resume.parsed_data else None)
        if education:
            elements.append(Paragraph("EDUCATION", styles["section_heading"]))
            elements.append(self._make_hr())
            for edu in education:
                deg = edu.get("degree") or "Degree"
                inst = edu.get("institution") or ""
                yr = edu.get("year") or ""
                parts = [p for p in [f"<b>{safe_xml(deg)}</b>", safe_xml(inst), safe_xml(yr)] if p and p != "<b></b>"]
                elements.append(Paragraph(" &nbsp;|&nbsp; ".join(parts), styles["body"]))

        doc.build(elements)
        return file_path


tailored_pdf_generator = TailoredResumePdfGenerator()
