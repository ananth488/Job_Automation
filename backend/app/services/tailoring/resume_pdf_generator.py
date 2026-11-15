"""ATS-Compliant Tailored Resume PDF Generator (Naukri Neo Style).

Universal Multi-User & Multi-Domain Engine:
Preserves any candidate's authentic resume structure, experience, and projects dynamically,
while optimizing the Professional Summary and Technical Skills specifically to bridge
the target Job Description (JD) requirements with zero duplicates.
"""

from __future__ import annotations

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


def extract_clean_bullets(desc: str) -> list[str]:
    """Extract clean, complete bullet points from a description string without splitting on dots."""
    if not desc:
        return []
    lines = []
    # Split on newlines or bullet markers (▸, •, -)
    for raw in re.split(r"[\n\r]+|[▸•]\s*", desc):
        cleaned = raw.strip().lstrip("▸•-* ").strip()
        if len(cleaned) > 10:
            lines.append(cleaned)
    return lines[:4]


class TailoredResumePdfGenerator:
    """Generates an ATS-optimized, high-impact PDF resume tailored to any candidate and any Job Description."""

    def __init__(self, output_dir: str | Path | None = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent.parent.parent / "uploads" / "tailored"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_pdf(
        self,
        profile: CandidateProfile,
        job: Job,
        matched_skills: list[str] | None = None,
        tailored_summary: str | None = None,
        output_filename: str | None = None,
        original_resume: Resume | None = None,
    ) -> Path:
        """Generate and save the tailored resume PDF dynamically for any user and domain."""
        if not output_filename:
            sanitized_comp = "".join(c for c in job.company if c.isalnum() or c in ("-", "_")).lower()
            output_filename = f"tailored_resume_u{profile.user_id}_j{job.id}_{sanitized_comp}.pdf"

        file_path = self.output_dir / output_filename

        # Standard 0.5-inch margins for clean single-page ATS layout (Printable width = 540 pt)
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=32,
            bottomMargin=32,
        )

        styles = getSampleStyleSheet()

        name_style = ParagraphStyle(
            "CandidateName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=21,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_CENTER,
        )

        title_sub_style = ParagraphStyle(
            "TitleSub",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12.5,
            textColor=colors.HexColor("#334155"),
            alignment=TA_CENTER,
        )

        contact_style = ParagraphStyle(
            "ContactInfo",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.3,
            leading=11.5,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
        )

        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=5,
            spaceAfter=2,
            leftIndent=0,
            alignment=TA_LEFT,
        )

        body_style = ParagraphStyle(
            "BodyText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1E293B"),
            leftIndent=0,
            alignment=TA_LEFT,
        )

        skill_style = ParagraphStyle(
            "SkillLine",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1E293B"),
            leftIndent=0,
            spaceAfter=1.5,
            alignment=TA_LEFT,
        )

        job_title_style = ParagraphStyle(
            "JobTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0F172A"),
            leftIndent=0,
            alignment=TA_LEFT,
        )

        job_meta_style = ParagraphStyle(
            "JobMeta",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=11.5,
            textColor=colors.HexColor("#475569"),
            alignment=TA_RIGHT,
        )

        bullet_style = ParagraphStyle(
            "BulletPoint",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.4,
            leading=11.8,
            textColor=colors.HexColor("#334155"),
            leftIndent=11,
            firstLineIndent=-7,
            spaceAfter=1.5,
            alignment=TA_LEFT,
        )

        project_tech_style = ParagraphStyle(
            "ProjectTech",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.2,
            leading=11,
            textColor=colors.HexColor("#475569"),
            leftIndent=0,
            spaceAfter=1.5,
            alignment=TA_LEFT,
        )

        def make_hr():
            return HRFlowable(
                width="100%",
                thickness=0.75,
                color=colors.HexColor("#94A3B8"),
                spaceBefore=1,
                spaceAfter=3.5,
                hAlign="LEFT",
            )

        elements = []

        # 1. Header: Candidate Name, Title, and Contact Info
        full_name = profile.full_name or "ANANTH P"
        elements.append(Paragraph(full_name.upper(), name_style))
        elements.append(Spacer(1, 1.5))

        # Dynamic Subtitle: Candidate's role adapted to target domain
        candidate_primary_title = None
        if profile.experience and isinstance(profile.experience, list) and len(profile.experience) > 0:
            candidate_primary_title = profile.experience[0].get("title")
        if not candidate_primary_title:
            candidate_primary_title = job.title if job and job.title else "Software Professional"

        elements.append(Paragraph(candidate_primary_title, title_sub_style))
        elements.append(Spacer(1, 2))

        # Dynamic Contact Line
        contact_parts = []
        if profile.location:
            contact_parts.append(profile.location)
        if profile.email:
            contact_parts.append(profile.email)
        if profile.phone:
            contact_parts.append(profile.phone)
        contact_line_1 = " &nbsp;|&nbsp; ".join(contact_parts) if contact_parts else "Chennai, India | ananthslvm28@gmail.com"

        links = ["LinkedIn", "GitHub", "Portfolio"]
        contact_line_2 = " &nbsp;|&nbsp; ".join(links)

        elements.append(Paragraph(contact_line_1, contact_style))
        elements.append(Spacer(1, 1))
        elements.append(Paragraph(contact_line_2, contact_style))
        elements.append(Spacer(1, 4))

        # Skill Normalization & Universal Multi-Domain Categorization
        def normalize_skill(s: str) -> str:
            sl = s.strip().lower()
            mapping = {
                "react": "React.js", "react.js": "React.js", "reactjs": "React.js",
                "next": "Next.js", "next.js": "Next.js", "nextjs": "Next.js",
                "node": "Node.js", "node.js": "Node.js", "nodejs": "Node.js",
                "express": "Express.js", "express.js": "Express.js", "expressjs": "Express.js",
                "react native": "React Native", "react-native": "React Native",
                "javascript": "JavaScript (ES6+)", "js": "JavaScript (ES6+)", "es6": "JavaScript (ES6+)",
                "typescript": "TypeScript", "ts": "TypeScript",
                "html": "HTML5", "html5": "HTML5",
                "css": "CSS3", "css3": "CSS3",
                "python": "Python", "django": "Django", "fastapi": "FastAPI", "flask": "Flask",
                "java": "Java", "spring": "Spring Boot", "spring boot": "Spring Boot",
                "rest api": "RESTful APIs", "restful api": "RESTful APIs", "rest apis": "RESTful APIs", "restful apis": "RESTful APIs", "rest": "RESTful APIs",
                "redux": "Redux", "redux toolkit": "Redux", "context api": "Context API",
                "tailwind": "Tailwind CSS", "tailwind css": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
                "bootstrap": "Bootstrap", "bootstrap 5": "Bootstrap",
                "git": "Git", "github": "GitHub", "graphql": "GraphQL",
                "websockets": "WebSockets", "websocket": "WebSockets", "socket.io": "Socket.io", "socketio": "Socket.io",
                "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
                "aws": "AWS", "azure": "Azure", "gcp": "GCP",
                "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "mysql": "MySQL", "mongodb": "MongoDB", "sql": "SQL",
                "pytorch": "PyTorch", "tensorflow": "TensorFlow", "pandas": "Pandas", "numpy": "NumPy",
                "jest": "Jest", "cypress": "Cypress", "selenium": "Selenium",
            }
            return mapping.get(sl, s.strip())

        # Determine categories dynamically based on the candidate's domain and target JD
        all_skills_combined = []
        if matched_skills:
            all_skills_combined.extend(matched_skills)
        if profile.skills:
            all_skills_combined.extend(profile.skills)

        # Dynamic Categories
        categories = [
            ("Languages & Web", ["JavaScript (ES6+)", "TypeScript", "HTML5", "CSS3"]),
            ("Frontend Frameworks & State", ["React.js", "Next.js", "React Hooks", "Redux", "Context API", "React Native"]),
            ("UI Libraries & Styling", ["Tailwind CSS", "Bootstrap", "Ant Design", "Responsive Design"]),
            ("Backend & APIs", ["Node.js", "RESTful APIs", "GraphQL", "WebSockets", "Socket.io"]),
            ("Tools & Practices", ["Git", "GitHub", "Web & Mobile Testing", "SEO Optimization", "Performance Optimization"]),
        ]

        # If candidate or job is in another domain (e.g. Python, Java, Data Science, DevOps), adjust categories
        domain_text = " ".join(all_skills_combined).lower() + " " + (job.title or "").lower()
        if any(w in domain_text for w in ("data science", "machine learning", "pytorch", "pandas", "tensorflow")):
            categories = [
                ("Programming & Analysis", ["Python", "SQL", "R"]),
                ("Machine Learning & Frameworks", ["PyTorch", "TensorFlow", "Scikit-Learn", "Pandas", "NumPy"]),
                ("Data & Cloud Platforms", ["PostgreSQL", "AWS", "BigQuery", "Snowflake"]),
                ("APIs & Deployment", ["RESTful APIs", "FastAPI", "Docker", "Git"]),
                ("Tools & Practices", ["Jupyter", "MLOps", "Model Evaluation", "A/B Testing"]),
            ]
        elif any(w in domain_text for w in ("devops", "cloud engineer", "sre", "kubernetes", "terraform")):
            categories = [
                ("Cloud & Infrastructure", ["AWS", "Azure", "GCP", "Terraform"]),
                ("Containers & Orchestration", ["Docker", "Kubernetes", "Helm"]),
                ("CI/CD & Automation", ["Jenkins", "GitHub Actions", "GitLab CI", "Ansible"]),
                ("Scripting & Systems", ["Python", "Bash", "Linux", "Shell Scripting"]),
                ("Monitoring & Practices", ["Prometheus", "Grafana", "Git", "Security Best Practices"]),
            ]
        elif any(w in domain_text for w in ("java", "spring boot", "backend engineer")):
            categories = [
                ("Languages & Core", ["Java", "SQL", "Python"]),
                ("Backend & Microservices", ["Spring Boot", "Spring MVC", "Hibernate", "RESTful APIs"]),
                ("Databases & Messaging", ["PostgreSQL", "MySQL", "Kafka", "Redis"]),
                ("Cloud & Containers", ["Docker", "Kubernetes", "AWS"]),
                ("Tools & Practices", ["Git", "Maven", "JUnit", "CI/CD", "Agile"]),
            ]

        seen_skills = set()
        category_map = {cat: [] for cat, _ in categories}

        # First pass: map target JD skills & matched skills
        for s in all_skills_combined:
            normed = normalize_skill(s)
            k = normed.lower()
            if k not in seen_skills:
                seen_skills.add(k)
                sl = normed.lower()
                placed = False
                for cat_name, _ in categories:
                    c_lower = cat_name.lower()
                    if ("language" in c_lower or "programming" in c_lower) and any(w in sl for w in ("javascript", "typescript", "python", "java", "html", "css", "sql", "bash", "es6")):
                        category_map[cat_name].append(normed)
                        placed = True
                        break
                    elif ("frontend" in c_lower or "machine learning" in c_lower or "microservice" in c_lower or "framework" in c_lower) and any(w in sl for w in ("react", "next", "vue", "angular", "redux", "pytorch", "tensorflow", "pandas", "numpy", "spring", "django", "fastapi")):
                        category_map[cat_name].append(normed)
                        placed = True
                        break
                    elif ("ui" in c_lower or "styling" in c_lower) and any(w in sl for w in ("tailwind", "bootstrap", "ant", "responsive", "ui", "style", "sass", "material")):
                        category_map[cat_name].append(normed)
                        placed = True
                        break
                    elif ("backend" in c_lower or "api" in c_lower or "database" in c_lower or "cloud" in c_lower or "container" in c_lower) and any(w in sl for w in ("node", "express", "backend", "mongo", "database", "postgres", "redis", "kafka", "rest", "api", "graphql", "socket", "aws", "docker", "kubernetes")):
                        category_map[cat_name].append(normed)
                        placed = True
                        break
                    elif ("tool" in c_lower or "practice" in c_lower or "ci/cd" in c_lower or "monitor" in c_lower) and any(w in sl for w in ("git", "test", "jest", "cypress", "seo", "ci/cd", "webpack", "vite", "performance", "jenkins", "prometheus")):
                        category_map[cat_name].append(normed)
                        placed = True
                        break
                if not placed:
                    # Place in last category
                    last_cat = list(category_map.keys())[-1]
                    category_map[last_cat].append(normed)

        # Fill remaining defaults with zero duplicates
        for cat, defaults in categories:
            for d in defaults:
                dk = d.lower()
                if dk not in seen_skills:
                    seen_skills.add(dk)
                    category_map[cat].append(d)

        # 2. Professional Summary (Clean single paragraph, tailored to candidate's domain & job)
        elements.append(Paragraph("PROFESSIONAL SUMMARY", section_heading))
        elements.append(make_hr())

        has_node = "node.js" in seen_skills
        exp_years = f"{profile.total_experience_years or 2.5} years"
        target_role = job.title if job and job.title else candidate_primary_title

        # Select top skills for summary dynamically
        top_skills_for_summary = [s for s in ("React.js", "Next.js", "Node.js", "JavaScript (ES6+)", "TypeScript", "Redux", "Tailwind CSS") if s.lower() in seen_skills]
        if not top_skills_for_summary:
            top_skills_for_summary = list(seen_skills)[:5]
        core_tech = ", ".join(top_skills_for_summary) if top_skills_for_summary else "modern software engineering practices"

        summary_text = (
            f"{target_role} with {exp_years} of professional experience building responsive, high-performance applications using "
            f"{core_tech}. Skilled in clean component architecture, scalable state management, "
            f"seamless API integrations, real-time communications, performance optimization, and robust testing "
            f"to deliver user-focused digital solutions and accelerate feature delivery."
        )
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 4))

        # 3. Technical Skills (Deduplicated, zero company branding)
        elements.append(Paragraph("TECHNICAL SKILLS", section_heading))
        elements.append(make_hr())

        for cat, s_list in category_map.items():
            if s_list:
                elements.append(Paragraph(f"<b>{cat}:</b> {', '.join(s_list)}", skill_style))

        elements.append(Spacer(1, 4))

        # 4. Professional Experience (Dynamic for any candidate)
        elements.append(Paragraph("PROFESSIONAL EXPERIENCE", section_heading))
        elements.append(make_hr())

        default_experiences = [
            {
                "title": "Front End Developer",
                "company": "LegalOptix Private Limited",
                "location": "Chennai",
                "dates": "Feb 2026 – Sep 2026",
                "bullets": [
                    "Build responsive frontend features with React.js, Next.js, JavaScript, Redux, and Tailwind CSS for application workflows.",
                    "Use React Hooks and Context API to manage component and shared application state across modules.",
                ],
            },
            {
                "title": "Front End Developer",
                "company": "Piccosoft Software Labs Private Limited",
                "location": "Chennai",
                "dates": "Dec 2023 – Nov 2025",
                "bullets": [
                    "Developed responsive web application features using React.js, Next.js, JavaScript, Redux, Tailwind CSS, React Hooks, and Context API.",
                    "Integrated RESTful APIs to connect frontend modules with backend services and support dynamic data updates.",
                    "Optimized semantic HTML, page-load performance, and metadata for SEO.",
                    "Worked with UI/UX designers, backend developers, QA engineers, and product managers to clarify requirements and deliver features on schedule.",
                ],
            },
        ]

        experiences = (
            profile.experience
            if (profile.experience and isinstance(profile.experience, list) and len(profile.experience) > 0)
            else default_experiences
        )

        for exp in experiences:
            exp_title = exp.get("title", "Software Engineer")
            exp_company = exp.get("company", "Company")
            exp_location = exp.get("location", profile.location or "India")
            exp_dates = exp.get("dates") or f"{exp.get('start', '')} – {exp.get('end', '')}".strip(" –")
            if not exp_dates:
                exp_dates = "2024 – Present"

            header_table = Table(
                [[
                    Paragraph(f"<b>{exp_title}</b> &mdash; <i>{exp_company}</i>", job_title_style),
                    Paragraph(f"{exp_dates} | {exp_location}", job_meta_style),
                ]],
                colWidths=[380, 160],
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
            if not bullets:
                bullets = ["Contributed to core development workflows, feature delivery, and software optimization."]

            for b in bullets[:4]:
                elements.append(Paragraph(f"• {b}", bullet_style))
            elements.append(Spacer(1, 2.5))

        # 5. Key Projects (Dynamic for any candidate)
        elements.append(Paragraph("KEY PROJECTS", section_heading))
        elements.append(make_hr())

        ecom_tech = "React.js, Next.js, Node.js, JavaScript, Redux, Context API, WebSockets" if has_node else "React.js, Next.js, JavaScript, Redux, Context API, WebSockets"
        default_projects = [
            {
                "name": "E-Commerce Web Application",
                "tech": ecom_tech,
                "bullets": [
                    "Implemented Wishlist, Cart, Checkout, and Order Management workflows covering returns, refunds, and cancellations.",
                    "Developed Product Comparison, Saved Searches, Offer and Discount Management, and configurable widgets.",
                    "Built buyer registration and login workflows with form validation and API integration.",
                    "Integrated real-time notifications with WebSockets/Socket.io and applied lazy loading and dynamic rendering to support frontend performance.",
                ],
            },
            {
                "name": "Media Platform for Startup Founders",
                "tech": "Next.js, GraphQL",
                "bullets": [
                    "Built a content-publishing platform with Next.js, GraphQL API integration, and dynamic page rendering.",
                    "Applied SEO optimization techniques associated with a reported 25% increase in website traffic.",
                ],
            },
            {
                "name": "Property Loan Management",
                "tech": "React.js, Next.js, Ant Design, Redux",
                "bullets": [
                    "Built responsive frontend components for an OCR-enabled document-processing application that extracts structured data from unstructured documents.",
                    "Integrated external document-parsing APIs and refined UI components for a responsive user experience.",
                ],
            },
        ]

        projects = (
            profile.projects
            if (profile.projects and isinstance(profile.projects, list) and len(profile.projects) > 0)
            else default_projects
        )

        for p in projects[:3]:
            p_name = p.get("name", "Software Project")
            p_tech = p.get("tech") or p.get("technologies") or "Modern Tech Stack"
            elements.append(Paragraph(f"<b>{p_name}</b>", job_title_style))
            elements.append(Paragraph(f"Technologies: {p_tech}", project_tech_style))

            p_bullets = p.get("bullets")
            if not p_bullets and p.get("description"):
                p_bullets = extract_clean_bullets(p.get("description"))
            if not p_bullets:
                p_bullets = ["Architected and delivered core platform workflows with responsive architecture and optimized rendering."]

            for b in p_bullets[:4]:
                elements.append(Paragraph(f"• {b}", bullet_style))
            elements.append(Spacer(1, 2.5))

        # 6. Education (Dynamic for any candidate)
        elements.append(Paragraph("EDUCATION", section_heading))
        elements.append(make_hr())

        default_education = [
            {"degree": "B.E., Computer Science and Engineering", "institution": "Anand Institute of Higher Technology", "year": "2016–2020"}
        ]
        education_items = (
            profile.education
            if (profile.education and isinstance(profile.education, list) and len(profile.education) > 0)
            else default_education
        )

        for edu in education_items:
            deg = edu.get("degree", "Bachelor of Engineering")
            inst = edu.get("institution", "Institution")
            yr = edu.get("year", "2016–2020")
            elements.append(Paragraph(f"<b>{deg}</b> &nbsp;|&nbsp; {inst} &nbsp;|&nbsp; {yr}", body_style))

        # Build PDF cleanly
        doc.build(elements)
        return file_path


tailored_pdf_generator = TailoredResumePdfGenerator()
