"""Indeed platform adapter following compliance rules."""

from datetime import datetime, timedelta, timezone
from typing import Any
import random

import urllib.parse
from app.platforms.base import PlatformAdapter, PlatformCapabilities


class IndeedAdapter(PlatformAdapter):
    """Adapter for Indeed.com.
    
    can_search=True, can_auto_apply=False (requires candidate confirmation/approval queue).
    """

    INDEED_COMPANIES = [
        {"name": "Smallcase", "type": "startup"},
        {"name": "InVideo", "type": "startup"},
        {"name": "Jupiter Money", "type": "startup"},
        {"name": "Porter", "type": "startup"},
        {"name": "Rapido", "type": "startup"},
        {"name": "Spinny", "type": "startup"},
        {"name": "Classplus", "type": "startup"},
        {"name": "Plum Insurance", "type": "startup"},
        {"name": "Postman", "type": "saas"},
        {"name": "BrowserStack", "type": "saas"},
        {"name": "Zerodha", "type": "startup"},
        {"name": "Razorpay", "type": "startup"},
        {"name": "Swiggy", "type": "startup"},
        {"name": "CRED", "type": "startup"},
        {"name": "Juspay", "type": "startup"},
        {"name": "Urban Company", "type": "startup"},
        {"name": "Groww", "type": "startup"},
        {"name": "Zepto", "type": "startup"},
        {"name": "Meesho", "type": "startup"},
        {"name": "Flipkart", "type": "mnc"},
        {"name": "Paytm", "type": "mnc"},
    ]

    MEDICAL_CODING_COMPANIES = [
        {"name": "Omega Healthcare", "type": "mnc"},
        {"name": "Episource", "type": "mid_sized"},
        {"name": "Access Healthcare", "type": "mnc"},
        {"name": "AGS Health", "type": "mid_sized"},
        {"name": "CorroHealth", "type": "mnc"},
        {"name": "R1 RCM", "type": "mnc"},
        {"name": "Optum", "type": "mnc"},
        {"name": "GeBBS Healthcare", "type": "mid_sized"},
        {"name": "Vee Technologies", "type": "mid_sized"},
        {"name": "Sagility Health", "type": "mnc"},
        {"name": "Visionary RCM", "type": "mid_sized"},
    ]

    FINANCE_COMPANIES = [
        {"name": "Deloitte", "type": "mnc"},
        {"name": "EY", "type": "mnc"},
        {"name": "PwC", "type": "mnc"},
        {"name": "KPMG", "type": "mnc"},
        {"name": "Genpact", "type": "mnc"},
        {"name": "WNS", "type": "mnc"},
    ]

    HR_COMPANIES = [
        {"name": "Randstad", "type": "mnc"},
        {"name": "Adecco", "type": "mnc"},
        {"name": "Michael Page", "type": "mnc"},
        {"name": "TeamLease", "type": "mid_sized"},
    ]

    def __init__(self):
        super().__init__(
            name="indeed",
            capabilities=PlatformCapabilities(
                can_search=True,
                can_auto_apply=False,
                requires_browser=False,
                rate_limit_per_minute=25,
            ),
        )

    async def search_jobs(
        self,
        keywords: list[str],
        locations: list[str] | None = None,
        experience_min: int | None = None,
        limit: int = 25,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Simulate authorized job ingestion from Indeed feeds matching candidate skills, domain, and locations."""
        active_locs = locations if locations and len(locations) > 0 else ["Bengaluru", "Chennai", "Hyderabad", "Remote"]
        candidate_skills = kwargs.get("candidate_skills") or []
        primary_skills = candidate_skills if candidate_skills else (keywords if keywords else ["React", "JavaScript", "TypeScript", "Next.js"])

        # Detect domain
        domain = kwargs.get("domain")
        if not domain:
            from app.services.resume_parser.parser import ResumeParser
            p = ResumeParser()
            domain = p.detect_domain(primary_skills)

        # Domain-specific companies and roles
        if domain in ("medical_coding", "healthcare"):
            active_companies = self.MEDICAL_CODING_COMPANIES
            role_variants = [
                ("Inpatient Medical Coder (ICD-10 & CPT)", ["ICD-10-CM", "ICD-10-PCS", "CPT", "Inpatient Coding", "HIPAA"]),
                ("Certified Outpatient Coder (COC / CPC)", ["CPC (AAPC)", "CPT-4", "HCPCS", "Outpatient Coding", "Medical Terminology"]),
                ("Risk Adjustment Coder (HCC Specialist)", ["HCC Coding", "Risk Adjustment", "ICD-10-CM", "Chart Auditing", "EHR"]),
                ("Medical Billing & AR Executive", ["Medical Billing", "Accounts Receivable", "Revenue Cycle Management (RCM)", "Denial Management"]),
                ("Clinical Documentation & Coding Specialist", ["Clinical Documentation", "Chart Auditing", "ICD-10-CM", "CPT", "CDI"]),
                ("Emergency Room (ED) Medical Coder", ["Emergency Department (ED)", "ICD-10-CM", "CPT", "Surgery Coding"]),
                ("Senior RCM Coder - Multi-specialty", ["ICD-10-CM", "CPT", "Revenue Cycle Management (RCM)", "Claim Submission", "EHR"]),
            ]
            salary_base = 480000
            salary_mult = 75000
        elif domain == "finance":
            active_companies = self.FINANCE_COMPANIES
            role_variants = [
                ("Senior Accountant - GST & Tally", ["Tally Prime", "GST", "GST Filing", "TDS", "Financial Accounting"]),
                ("Financial Analyst (FP&A)", ["Financial Modeling", "MIS Reporting", "Advanced Excel", "Budgeting", "P&L"]),
                ("Accounts Executive (AP/AR)", ["Accounts Payable", "Accounts Receivable", "Bank Reconciliation", "General Ledger"]),
                ("Direct & Indirect Tax Specialist", ["Taxation", "Income Tax", "GST", "TDS", "Auditing"]),
            ]
            salary_base = 600000
            salary_mult = 95000
        elif domain == "hr":
            active_companies = self.HR_COMPANIES
            role_variants = [
                ("Technical IT Recruiter", ["Technical Recruitment", "Talent Acquisition", "Sourcing", "Candidate Screening"]),
                ("HR Operations Executive", ["HR Operations", "HRMS", "Onboarding", "Payroll Processing"]),
                ("HR Specialist (People & Culture)", ["Employee Engagement", "HR Policies", "Statutory Compliance", "Workday"]),
            ]
            salary_base = 520000
            salary_mult = 85000
        elif domain in ("frontend", "fullstack") or any(s.lower() in ["react", "react.js", "next.js", "javascript", "typescript", "frontend", "html5", "css3", "tailwind css", "redux"] for s in primary_skills):
            active_companies = self.INDEED_COMPANIES
            role_variants = [
                ("Senior Frontend Developer (Next.js)", ["Next.js", "React", "TypeScript", "Tailwind CSS", "Redux"]),
                ("Software Development Engineer - Frontend", ["React", "JavaScript", "TypeScript", "RESTful API", "HTML5"]),
                ("Full Stack Software Engineer", ["React", "TypeScript", "Next.js", "Node.js", "REST API"]),
                ("UI Engineer (React / Web Platforms)", ["React", "Context API", "CSS3", "Bootstrap", "Git"]),
                ("Web Application Developer", ["React", "JavaScript", "Tailwind CSS", "Next.js", "GraphQL"]),
                ("Senior React.js Engineer", ["React", "Redux", "TypeScript", "REST API", "GitHub"]),
                ("React Native & Web Developer", ["React Native", "React", "TypeScript", "Tailwind CSS", "Redux"]),
                ("Staff Frontend Engineer", ["React", "Next.js", "TypeScript", "GraphQL", "Performance Optimization"]),
                ("Product Frontend Engineer", ["React", "Next.js", "Tailwind CSS", "TypeScript", "RESTful API"]),
            ]
            salary_base = 1200000
            salary_mult = 200000
        else:
            active_companies = self.INDEED_COMPANIES
            role_variants = [
                ("Principal Python Architect", ["Python", "AWS", "Distributed Systems", "Architecture", "Microservices"]),
                ("Senior Backend Developer (FastAPI/Go)", ["Python", "FastAPI", "Go", "PostgreSQL", "Kafka"]),
                ("Full Stack Software Engineer", ["React", "TypeScript", "Python", "Redis", "Docker"]),
                ("Machine Learning Systems Engineer", ["Python", "PyTorch", "MLOps", "Docker", "Kubernetes"]),
                ("Staff DevOps / SRE Engineer", ["Kubernetes", "AWS", "Terraform", "Prometheus", "CI/CD"]),
                ("AI Software Engineer", ["Python", "LangChain", "OpenAI", "FastAPI", "PostgreSQL"]),
            ]
            salary_base = 1250000
            salary_mult = 210000

        modes = ["remote", "hybrid", "onsite", "hybrid", "remote"]
        results = []

        total_to_generate = min(limit, len(active_companies) * 2)
        for i in range(total_to_generate):
            comp_entry = active_companies[i % len(active_companies)]
            comp = comp_entry["name"]
            comp_type = comp_entry.get("type", "startup")
            title_base, default_skills = role_variants[i % len(role_variants)]
            job_loc = active_locs[i % len(active_locs)]
            mode = modes[i % len(modes)]

            # Combine candidate's verified skills with role requirements
            merged_skills: list[str] = []
            for s in default_skills:
                if s not in merged_skills:
                    merged_skills.append(s)
            for s in candidate_skills[:4]:
                if s not in merged_skills:
                    merged_skills.append(s)

            s_min = salary_base + (i % 6) * salary_mult
            s_max = s_min + int(salary_base * 0.65) + (i % 4) * salary_mult
            exp_low = max(1, (experience_min or 2) - 1 + (i % 2))
            exp_high = exp_low + 3 + (i % 3)

            clean_q = urllib.parse.quote_plus(f"{comp} {title_base}")
            clean_l = urllib.parse.quote_plus(job_loc.split(",")[0].strip()) if "remote" not in job_loc.lower() else ""
            direct_indeed_url = f"https://in.indeed.com/jobs?q={clean_q}" + (f"&l={clean_l}" if clean_l else "")

            # Enterprise companies with external career redirects
            company_portal_links = {
                # Medical Coding
                "Omega Healthcare": "https://www.omegahms.com/careers/",
                "Episource": "https://www.episource.com/careers",
                "Access Healthcare": "https://www.accesshealthcare.com/careers",
                "AGS Health": "https://www.agshealth.com/careers",
                "CorroHealth": "https://corrohealth.com/careers/",
                "R1 RCM": "https://www.r1rcm.com/careers",
                "Optum": "https://careers.unitedhealthgroup.com/",
                "GeBBS Healthcare": "https://gebbs.com/careers/",
                "Vee Technologies": "https://www.veetechnologies.com/careers/",
                "Sagility Health": "https://sagilityhealth.com/careers/",
                # Finance
                "Deloitte": "https://www2.deloitte.com/ui/en/pages/careers/careers.html",
                "EY": "https://www.ey.com/en_in/careers",
                "PwC": "https://www.pwc.in/careers.html",
                "KPMG": "https://home.kpmg/in/en/home/careers.html",
                "Genpact": "https://www.genpact.com/careers",
                "WNS": "https://www.wns.com/careers",
                # HR
                "Randstad": "https://www.randstad.in/jobs/",
                "Adecco": "https://www.adecco.co.in/jobs/",
                "Michael Page": "https://www.michaelpage.co.in/jobs",
                "TeamLease": "https://www.teamlease.com/careers",
                # Tech
                "Flipkart": "https://www.flipkartcareers.com/",
                "Paytm": "https://paytm.com/careers",
                "Porter": "https://porter.in/careers",
                "BrowserStack": "https://www.browserstack.com/careers",
                "Meesho": "https://www.meesho.io/jobs",
                "Swiggy": "https://careers.swiggy.com/",
                "Razorpay": "https://razorpay.com/jobs/",
                "Urban Company": "https://careers.urbancompany.com/",
            }
            if comp in company_portal_links:
                apply_type = "company_portal"
                company_url = company_portal_links[comp]
            else:
                apply_type = "direct_1click"
                company_url = None

            days_ago = (i * 2 + 1) % 28
            hours_ago = (i * 4) % 24
            posted_dt = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)

            ext_id = f"indeed-{comp.lower().replace(' ', '')}-{2000 + i}"
            results.append({
                "platform": "indeed",
                "external_job_id": ext_id,
                "url": direct_indeed_url,
                "apply_type": apply_type,
                "company_url": company_url,
                "title": title_base,
                "company": comp,
                "company_type": comp_type,
                "location": job_loc,
                "work_mode": mode,
                "salary_min": s_min,
                "salary_max": s_max,
                "experience_min": exp_low,
                "experience_max": exp_high,
                "description": (
                    f"Exciting opportunity at {comp} for a {title_base} ({mode.capitalize()}) based in {job_loc}. "
                    f"Join our high-impact team building modern, scalable digital platforms. "
                    f"Key competencies needed: {', '.join(merged_skills[:4])}. Experience with modern development workflows required."
                ),
                "skills_required": merged_skills,
                "posted_date": posted_dt,
                "is_active": True,
            })
        return results

    async def get_job_details(self, external_job_id: str) -> dict[str, Any] | None:
        return {
            "external_job_id": external_job_id,
            "platform": "indeed",
            "full_description": "Job details fetched from Indeed posting with company background and benefits.",
        }

    async def apply(
        self,
        external_job_id: str,
        application_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "success": False,
            "method": "manual",
            "message": "Candidate assisted submission prepared with copy-ready answers and tailored resume.",
            "direct_url": f"https://www.indeed.com/viewjob?jk={external_job_id}",
        }
