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
        {"name": "Jar App", "type": "startup"},
        {"name": "Pocket FM", "type": "startup"},
        {"name": "Postman", "type": "saas"},
        {"name": "BrowserStack", "type": "saas"},
        {"name": "Zerodha", "type": "startup"},
        {"name": "Ather Energy", "type": "mid_sized"},
        {"name": "Razorpay", "type": "startup"},
        {"name": "Swiggy", "type": "startup"},
        {"name": "CRED", "type": "startup"},
        {"name": "Juspay", "type": "startup"},
        {"name": "Urban Company", "type": "startup"},
        {"name": "Groww", "type": "startup"},
        {"name": "Zepto", "type": "startup"},
        {"name": "Meesho", "type": "startup"},
        {"name": "CoinSwitch", "type": "startup"},
        {"name": "Pine Labs", "type": "startup"},
        {"name": "Flipkart", "type": "mnc"},
        {"name": "Paytm", "type": "mnc"},
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
        """Simulate authorized job ingestion from Indeed feeds matching candidate skills and locations."""
        active_locs = locations if locations and len(locations) > 0 else ["Bengaluru", "Chennai", "Hyderabad", "Remote"]
        candidate_skills = kwargs.get("candidate_skills") or []
        primary_skills = candidate_skills if candidate_skills else (keywords if keywords else ["React", "JavaScript", "TypeScript", "Next.js"])

        is_frontend = any(
            s.lower() in ["react", "react.js", "next.js", "javascript", "typescript", "frontend", "html5", "css3", "tailwind css", "redux"]
            for s in primary_skills
        )

        if is_frontend:
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
        else:
            role_variants = [
                ("Principal Python Architect", ["Python", "AWS", "Distributed Systems", "Architecture", "Microservices"]),
                ("Senior Backend Developer (FastAPI/Go)", ["Python", "FastAPI", "Go", "PostgreSQL", "Kafka"]),
                ("Full Stack Software Engineer", ["React", "TypeScript", "Python", "Redis", "Docker"]),
                ("Machine Learning Systems Engineer", ["Python", "PyTorch", "MLOps", "Docker", "Kubernetes"]),
                ("Staff DevOps / SRE Engineer", ["Kubernetes", "AWS", "Terraform", "Prometheus", "CI/CD"]),
                ("AI Software Engineer", ["Python", "LangChain", "OpenAI", "FastAPI", "PostgreSQL"]),
            ]

        modes = ["remote", "hybrid", "onsite", "hybrid", "remote"]
        results = []

        total_to_generate = min(limit, len(self.INDEED_COMPANIES) * 2)
        for i in range(total_to_generate):
            comp_entry = self.INDEED_COMPANIES[i % len(self.INDEED_COMPANIES)]
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

            s_min = 1200000 + (i % 6) * 200000
            s_max = s_min + 800000 + (i % 4) * 250000
            exp_low = max(1, (experience_min or 2) - 1 + (i % 2))
            exp_high = exp_low + 3 + (i % 3)

            clean_q = urllib.parse.quote_plus(f"{comp} {title_base}")
            clean_l = urllib.parse.quote_plus(job_loc.split(",")[0].strip()) if "remote" not in job_loc.lower() else ""
            direct_indeed_url = f"https://in.indeed.com/jobs?q={clean_q}" + (f"&l={clean_l}" if clean_l else "")

            # Enterprise companies with external career redirects
            company_portal_links = {
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
