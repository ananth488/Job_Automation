"""Resume parsing service — extracts text and structured data from PDF/DOCX files."""

import re
from pathlib import Path
from typing import Any

from app.schemas.resume import ParsedResumeData


class ResumeParser:
    """Parses uploaded resume files into structured data without false positives across all career domains."""

    DISCARD_SUBSTRINGS = {
        "specialties", "specialty", "healthcare systems", "compliance & regulations",
        "revenue cycle", "medical knowledge", "overview", "competencies", "areas of",
        "tools &", "methodologies", "frameworks", "technologies", "languages",
        "license id", "credential", "registered", "certified by", "completed", "proficient",
        "experience", "work history", "education", "declaration", "phone", "email",
        "address", "hobbies", "personal details", "profile summary", "professional summary"
    }

    # Canonical mapping of skills with display casing across all major career domains
    SKILLS_MAP: dict[str, str] = {
        # --- Medical Coding & Healthcare ---
        "icd-10": "ICD-10",
        "icd-10-cm": "ICD-10-CM",
        "icd-10-pcs": "ICD-10-PCS",
        "icd-9": "ICD-9",
        "cpt": "CPT",
        "cpt-4": "CPT-4",
        "hcpcs": "HCPCS",
        "medical coding": "Medical Coding",
        "medical billing": "Medical Billing",
        "hipaa": "HIPAA",
        "cpc": "CPC (AAPC)",
        "ccs": "CCS (AHIMA)",
        "ccs-p": "CCS-P",
        "coc": "COC",
        "cic": "CIC",
        "crc": "CRC",
        "cpma": "CPMA",
        "aapc": "AAPC",
        "ahima": "AHIMA",
        "rcm": "Revenue Cycle Management (RCM)",
        "revenue cycle management": "Revenue Cycle Management (RCM)",
        "medical terminology": "Medical Terminology",
        "human anatomy": "Human Anatomy",
        "anatomy": "Anatomy",
        "physiology": "Physiology",
        "pathology": "Pathology",
        "pharmacology": "Pharmacology",
        "ehr": "EHR",
        "emr": "EMR",
        "epic": "Epic Systems",
        "epic systems": "Epic Systems",
        "cerner": "Cerner",
        "meditech": "MEDITECH",
        "athenahealth": "Athenahealth",
        "nextgen": "NextGen",
        "chart auditing": "Chart Auditing",
        "clinical documentation": "Clinical Documentation",
        "cdi": "CDI",
        "ipdrg": "IPDRG",
        "opps": "OPPS",
        "hcc": "HCC Coding",
        "hcc coding": "HCC Coding",
        "risk adjustment": "Risk Adjustment",
        "denial management": "Denial Management",
        "payment posting": "Payment Posting",
        "claim submission": "Claim Submission",
        "inpatient coding": "Inpatient Coding",
        "outpatient coding": "Outpatient Coding",
        "ed coding": "ED Coding",
        "surgery coding": "Surgery Coding",
        "e/m coding": "E/M Coding",
        "drg": "DRG Coding",

        # --- Finance, Accounting & Banking ---
        "tally": "Tally",
        "tally prime": "Tally Prime",
        "tally erp 9": "Tally ERP 9",
        "tally erp": "Tally ERP",
        "gst": "GST",
        "gst filing": "GST Filing",
        "tds": "TDS",
        "income tax": "Income Tax",
        "financial accounting": "Financial Accounting",
        "auditing": "Auditing",
        "internal audit": "Internal Audit",
        "statutory audit": "Statutory Audit",
        "taxation": "Taxation",
        "bookkeeping": "Bookkeeping",
        "balance sheet": "Balance Sheet",
        "p&l": "P&L",
        "general ledger": "General Ledger",
        "accounts payable": "Accounts Payable",
        "accounts receivable": "Accounts Receivable",
        "bank reconciliation": "Bank Reconciliation",
        "sap fico": "SAP FICO",
        "sap": "SAP",
        "payroll": "Payroll",
        "mis reporting": "MIS Reporting",
        "cost accounting": "Cost Accounting",
        "financial modeling": "Financial Modeling",
        "ifrs": "IFRS",
        "gaap": "GAAP",
        "advanced excel": "Advanced Excel",

        # --- Human Resources & Recruitment ---
        "talent acquisition": "Talent Acquisition",
        "technical recruitment": "Technical Recruitment",
        "recruitment": "Recruitment",
        "hr operations": "HR Operations",
        "employee engagement": "Employee Engagement",
        "employee relations": "Employee Relations",
        "onboarding": "Onboarding",
        "offboarding": "Offboarding",
        "hr policies": "HR Policies",
        "performance management": "Performance Management",
        "hrms": "HRMS",
        "hris": "HRIS",
        "workday": "Workday",
        "bamboohr": "BambooHR",
        "zoho people": "Zoho People",
        "keka": "Keka HR",
        "darwinbox": "Darwinbox",
        "payroll processing": "Payroll Processing",
        "statutory compliance": "Statutory Compliance",
        "sourcing": "Sourcing",
        "screening": "Candidate Screening",
        "headhunting": "Headhunting",

        # --- Digital Marketing & Sales ---
        "digital marketing": "Digital Marketing",
        "seo": "SEO",
        "sem": "SEM",
        "google ads": "Google Ads",
        "meta ads": "Meta Ads",
        "social media marketing": "Social Media Marketing",
        "content marketing": "Content Marketing",
        "email marketing": "Email Marketing",
        "hubspot": "HubSpot",
        "salesforce": "Salesforce",
        "crm": "CRM",
        "lead generation": "Lead Generation",
        "b2b sales": "B2B Sales",
        "b2c sales": "B2C Sales",
        "inside sales": "Inside Sales",
        "cold calling": "Cold Calling",
        "business development": "Business Development",
        "customer support": "Customer Support",
        "technical support": "Technical Support",
        "zendesk": "Zendesk",
        "freshdesk": "Freshdesk",

        # --- Core Engineering ---
        "autocad": "AutoCAD",
        "solidworks": "SolidWorks",
        "catia": "CATIA",
        "ansys": "ANSYS",
        "revit": "Revit",
        "matlab": "MATLAB",
        "plc": "PLC",
        "scada": "SCADA",
        "embedded systems": "Embedded Systems",
        "vlsi": "VLSI",
        "verilog": "Verilog",
        "pcb design": "PCB Design",
        "six sigma": "Six Sigma",
        "lean manufacturing": "Lean Manufacturing",
        "quality control": "Quality Control",
        "quality assurance": "Quality Assurance",

        # --- Programming Languages ---
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "java": "Java",
        "c++": "C++",
        "c#": "C#",
        "golang": "Go",
        "go": "Go",
        "rust": "Rust",
        "ruby": "Ruby",
        "php": "PHP",
        "swift": "Swift",
        "kotlin": "Kotlin",
        "scala": "Scala",
        "sql": "SQL",
        "pl/sql": "PL/SQL",
        # Frameworks & Libraries
        "react": "React",
        "react.js": "React",
        "reactjs": "React",
        "react native": "React Native",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "express": "Express.js",
        "express.js": "Express.js",
        "angular": "Angular",
        "vue": "Vue.js",
        "vue.js": "Vue.js",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "spring boot": "Spring Boot",
        "spring": "Spring",
        ".net": ".NET",
        "dotnet": ".NET",
        # Frontend / Styling
        "tailwind": "Tailwind CSS",
        "tailwind css": "Tailwind CSS",
        "bootstrap": "Bootstrap",
        "html": "HTML",
        "html5": "HTML5",
        "css": "CSS",
        "css3": "CSS3",
        "sass": "SASS",
        "redux": "Redux",
        "redux toolkit": "Redux Toolkit",
        # Cloud & DevOps
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "terraform": "Terraform",
        "ansible": "Ansible",
        "ci/cd": "CI/CD",
        "jenkins": "Jenkins",
        "github actions": "GitHub Actions",
        # Databases & Caches
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "elasticsearch": "Elasticsearch",
        "cassandra": "Cassandra",
        "dynamodb": "DynamoDB",
        "sqlite": "SQLite",
        "oracle": "Oracle",
        # Architecture & Messaging
        "rest": "REST API",
        "rest api": "REST API",
        "restful": "RESTful API",
        "graphql": "GraphQL",
        "grpc": "gRPC",
        "microservices": "Microservices",
        "kafka": "Kafka",
        "rabbitmq": "RabbitMQ",
        "celery": "Celery",
        # AI, Data & Analytics
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "nlp": "NLP",
        "llm": "LLM",
        "genai": "GenAI",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "scikit-learn": "Scikit-Learn",
        "spark": "Apache Spark",
        "hadoop": "Hadoop",
        "tableau": "Tableau",
        "power bi": "Power BI",
        "snowflake": "Snowflake",
        "databricks": "Databricks",
        # Tools & Testing
        "git": "Git",
        "github": "GitHub",
        "gitlab": "GitLab",
        "linux": "Linux",
        "jira": "Jira",
        "pytest": "PyTest",
        "jest": "Jest",
        "selenium": "Selenium",
        "cypress": "Cypress",
    }

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file using PyMuPDF (fitz), pdfplumber, or pypdf."""
        # 1. Try PyMuPDF (fitz) - fastest and most reliable for multi-column resumes
        try:
            import fitz

            doc = fitz.open(file_path)
            parts = [page.get_text() for page in doc]
            full_text = "\n".join(parts).strip()
            if full_text:
                return full_text
        except Exception:
            pass

        # 2. Try pdfplumber
        try:
            import pdfplumber

            with pdfplumber.open(file_path) as pdf:
                parts = [page.extract_text() for page in pdf.pages if page.extract_text()]
                full_text = "\n".join(parts).strip()
                if full_text:
                    return full_text
        except Exception:
            pass

        # 3. Try pypdf
        try:
            import pypdf

            reader = pypdf.PdfReader(file_path)
            parts = [page.extract_text() for page in reader.pages if page.extract_text()]
            full_text = "\n".join(parts).strip()
            if full_text:
                return full_text
        except Exception:
            pass

        return ""

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file using python-docx."""
        try:
            from docx import Document

            doc = Document(file_path)
            text_parts: list[str] = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            return "\n".join(text_parts)
        except Exception:
            return ""

    def extract_text(self, file_path: str) -> str:
        """Extract text from a file based on its extension."""
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext in (".docx", ".doc"):
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_email(self, text: str) -> str | None:
        """Extract email address from text."""
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        return match.group(0).strip() if match else None

    def _extract_phone(self, text: str) -> str | None:
        """Extract phone number from text supporting Indian and International formats."""
        # Indian mobile format (+91 XXXXXXXXXX, 0XXXXXXXXXX, XXXXXXXXXX)
        match_in = re.search(r"(?:\+?91[\s-]?)?[6-9]\d{9}", text)
        if match_in:
            return match_in.group(0).strip()

        # International format
        match = re.search(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            text,
        )
        return match.group(0).strip() if match else None

    def _extract_name(self, text: str) -> str | None:
        """Extract candidate name — cleans out header labels."""
        skip_words = {"resume", "curriculum vitae", "cv", "profile", "biodata", "bio"}
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:6]:
            clean = line.strip()
            if clean.lower() in skip_words or clean.lower().startswith("curriculum"):
                continue
            # Must not be email, url, or pure digits
            if "@" not in clean and "http" not in clean.lower() and not re.search(r"\d", clean):
                words = clean.split()
                if 1 <= len(words) <= 5:
                    return clean[:80]
        return None

    def _clean_skill_token(self, token: str) -> str | None:
        """Clean and normalize a raw candidate skill token extracted from text."""
        t = token.strip()
        t = re.sub(r"^[\s•\*\-▸▪–·✓✔o>\:\|\,\;\(\)\[\]]+", "", t)
        t = re.sub(r"[\s\:\|\,\;\(\)\[\]]+$", "", t).strip()
        if not t:
            return None
        if "@" in t or "http" in t.lower() or "www." in t.lower():
            return None
        if len(t) < 2 or len(t) > 40:
            return None
        # Discard if looks like a license ID / pure number / date string
        if re.search(r"\b\d{4,}\b", t) or re.match(r"^[A-Z0-9_-]{8,}$", t):
            return None
        # Discard if more than 4 words (likely a sentence fragment)
        words = t.split()
        if len(words) > 4:
            return None
        low = t.lower()
        if low in self.DISCARD_SUBSTRINGS or any(sub == low for sub in self.DISCARD_SUBSTRINGS):
            return None
        if any(stop in low for stop in [
            "responsible for", "years of", "experienced in", "knowledge of", "proficient in",
            "good understanding", "hands on", "ability to", "curriculum", "resume", "page 1"
        ]):
            return None

        # Standardize known acronyms
        acronyms = {
            "icd-10": "ICD-10", "icd-10-cm": "ICD-10-CM", "icd-10-pcs": "ICD-10-PCS",
            "cpt": "CPT", "cpt-4": "CPT-4", "hcpcs": "HCPCS", "hipaa": "HIPAA",
            "cpc": "CPC (AAPC)", "ccs": "CCS (AHIMA)", "rcm": "Revenue Cycle Management (RCM)",
            "ehr": "EHR", "emr": "EMR", "gst": "GST", "tds": "TDS", "sap": "SAP", "sql": "SQL",
            "aws": "AWS", "gcp": "GCP", "html": "HTML", "html5": "HTML5", "css": "CSS",
            "css3": "CSS3", "api": "API", "rest": "REST API", "seo": "SEO", "sem": "SEM",
            "crm": "CRM", "hrms": "HRMS", "hris": "HRIS", "ed": "Emergency Department (ED)",
            "mis": "MIS", "drg": "DRG Coding", "oig": "OIG Compliance", "cms": "CMS Guidelines",
            "ui": "UI", "ux": "UX", "qa": "QA", "qc": "QC"
        }
        if low in acronyms:
            return acronyms[low]
        if t.islower():
            return t.title()
        return t

    def _extract_dynamic_skills(self, text: str) -> set[str]:
        """Dynamically extract candidate skills from any resume layout and section headings."""
        section_patterns = [
            r"(?:CORE\s+COMPETENCIES\s*&?\s*SKILLS|CORE\s+COMPETENCIES|AREAS\s+OF\s+EXPERTISE|KEY\s+SKILLS|TECHNICAL\s+SKILLS|PROFESSIONAL\s+SKILLS|SKILLS\s*&?\s*ABILITIES|SKILLS\s+SUMMARY|DOMAIN\s+EXPERTISE|SPECIALIZATIONS|SKILLS|TECHNOLOGIES)\s*[:\n](.*?)(?=\n\s*(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EXPERIENCE|EMPLOYMENT|EDUCATION|ACADEMIC|PROJECTS|KEY\s+PROJECTS|PUBLICATIONS|CERTIFICATIONS|AWARDS|LANGUAGES|DECLARATION|PERSONAL\s+DETAILS)|\Z)",
            r"(?:CERTIFICATIONS?\s*&?\s*LICENSES?|CERTIFICATIONS?|CREDENTIALS?)\s*[:\n](.*?)(?=\n\s*(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EXPERIENCE|EMPLOYMENT|EDUCATION|ACADEMIC|PROJECTS|SKILLS|LANGUAGES|DECLARATION)|\Z)",
        ]
        extracted: set[str] = set()

        for pattern in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            sec_text = match.group(1).strip()
            lines = sec_text.split("\n")
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue

                # Category headers e.g. "Medical Coding: ICD-10-CM, CPT"
                if ":" in line_str:
                    parts = line_str.split(":", 1)
                    left_cand = self._clean_skill_token(parts[0])
                    if left_cand and left_cand.lower() not in self.DISCARD_SUBSTRINGS:
                        extracted.add(left_cand)
                    content = parts[1]
                elif " - " in line_str and not line_str.startswith("-"):
                    parts = line_str.split(" - ", 1)
                    left_cand = self._clean_skill_token(parts[0])
                    if left_cand and left_cand.lower() not in self.DISCARD_SUBSTRINGS:
                        extracted.add(left_cand)
                    content = parts[1]
                else:
                    content = line_str

                # Sub-skills in parentheses e.g. "Certified Professional Coder (CPC - AAPC)"
                paren_matches = re.findall(r"\((.*?)\)", content)
                for p in paren_matches:
                    for sub in re.split(r"[,;\|/-]+", p):
                        tok = self._clean_skill_token(sub)
                        if tok:
                            extracted.add(tok)
                outer_content = re.sub(r"\(.*?\)", "", content)

                tokens = re.split(r"[\,\;\|\•\*\▸\▪\–·]+", outer_content)
                for t in tokens:
                    tok = self._clean_skill_token(t)
                    if tok:
                        extracted.add(tok)

        return extracted

    def _extract_skills(self, text: str) -> list[str]:
        """Extract skills using dynamic section parsing combined with multi-domain dictionary matching."""
        found_skills: set[str] = set()

        # 1. Dynamic section parsing (works for ANY resume format or niche domain)
        dynamic_tokens = self._extract_dynamic_skills(text)
        found_skills.update(dynamic_tokens)

        # 2. Universal dictionary matching across full resume corpus
        for keyword, display_name in self.SKILLS_MAP.items():
            if keyword == "java":
                pattern = r"\bjava\b(?!\s*script)"
                if re.search(pattern, text, re.IGNORECASE):
                    found_skills.add(display_name)
                continue

            if keyword in ("rest", "rest api", "restful"):
                pattern = r"\b(?:REST\s*API|RESTful(?:\s*API)?|\bREST\b)\b"
                if re.search(pattern, text):
                    found_skills.add(display_name)
                continue

            if keyword == "go":
                pattern = r"\b(?:golang|\bgo\b(?:\s*programming|\s*developer|\s*backend)?)"
                if re.search(r"\bgolang\b", text, re.IGNORECASE):
                    found_skills.add(display_name)
                continue

            if keyword in ("c++", "c#", ".net"):
                if re.search(rf"(?:\b|\s){re.escape(keyword)}(?:[\s,;.\)]|$)", text, re.IGNORECASE):
                    found_skills.add(display_name)
                continue

            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.add(display_name)

        # De-duplicate case-insensitively, preferring canonical casing from SKILLS_MAP
        norm_map: dict[str, str] = {}
        for s in found_skills:
            key = re.sub(r"[\s\-_.]+", "", s.lower())
            if key not in norm_map or len(s) > len(norm_map[key]):
                norm_map[key] = s

        return sorted(list(norm_map.values()))

    def detect_domain(self, skills: list[str], text: str = "") -> str:
        """Classify candidate career domain from skills and resume content."""
        search_blob = (" ".join(skills) + " " + text).lower()

        # Check Medical Coding / Healthcare RCM
        med_keywords = [
            "icd-10", "cpt", "hcpcs", "medical coding", "medical coder", "medical billing",
            "hipaa", "cpc", "ccs", "rcm", "epic systems", "cerner", "inpatient coding",
            "outpatient coding", "chart auditing", "pathology", "anatomy", "physiology"
        ]
        if any(k in search_blob for k in med_keywords):
            return "medical_coding"

        # Check Healthcare / Nursing / Clinical
        health_keywords = ["nurse", "nursing", "clinical", "hospital", "patient care", "pharmacist", "pharmacy"]
        if any(k in search_blob for k in health_keywords):
            return "healthcare"

        # Check Finance & Accounting
        fin_keywords = [
            "tally", "gst", "tds", "income tax", "financial accounting", "auditing",
            "statutory audit", "balance sheet", "p&l", "general ledger", "sap fico", "accounts payable"
        ]
        if any(k in search_blob for k in fin_keywords):
            return "finance"

        # Check HR & Recruitment
        hr_keywords = [
            "talent acquisition", "recruitment", "hr operations", "employee engagement",
            "hrms", "hris", "workday", "bamboohr", "onboarding", "headhunting", "labor laws"
        ]
        if any(k in search_blob for k in hr_keywords):
            return "hr"

        # Check Digital Marketing & Sales
        mkt_keywords = [
            "digital marketing", "seo", "sem", "google ads", "social media marketing",
            "content marketing", "b2b sales", "cold calling", "lead generation"
        ]
        if any(k in search_blob for k in mkt_keywords):
            return "marketing_sales"

        # Check Data Science & AI
        data_keywords = ["machine learning", "deep learning", "nlp", "llm", "power bi", "tableau", "pytorch", "tensorflow", "data engineer"]
        if any(k in search_blob for k in data_keywords):
            return "data_ai"

        # Check DevOps & Cloud
        devops_keywords = ["kubernetes", "docker", "terraform", "ansible", "ci/cd", "devops", "aws", "gcp", "azure"]
        if any(k in search_blob for k in devops_keywords):
            return "devops_cloud"

        # Check Core Engineering
        core_keywords = ["autocad", "solidworks", "catia", "ansys", "matlab", "plc", "scada", "embedded systems", "vlsi"]
        if any(k in search_blob for k in core_keywords):
            return "core_engineering"

        # Check Frontend vs Backend vs Full Stack
        fe_keywords = ["react", "react.js", "next.js", "tailwind", "html5", "css3", "javascript", "typescript", "frontend"]
        be_keywords = ["python", "fastapi", "django", "flask", "node.js", "express", "spring boot", "golang", "backend"]
        has_fe = any(k in search_blob for k in fe_keywords)
        has_be = any(k in search_blob for k in be_keywords)

        if has_fe and has_be:
            return "fullstack"
        elif has_fe:
            return "frontend"
        elif has_be:
            return "backend"

        return "general"

    def _extract_summary(self, text: str) -> str | None:
        """Extract professional summary or profile objective."""
        match = re.search(
            r"(?:PROFESSIONAL\s+SUMMARY|EXECUTIVE\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE)\s*[:\n](.*?)(?=\n\s*(?:TECHNICAL\s+SKILLS|SKILLS|PROFESSIONAL\s+EXPERIENCE|WORK\s+EXPERIENCE|EXPERIENCE|EDUCATION)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            cleaned = " ".join(match.group(1).strip().split())
            if len(cleaned) > 20:
                return cleaned[:1000]
        return None

    def _extract_location(self, text: str) -> str | None:
        """Extract candidate city or region from header area."""
        for line in text.split("\n")[:8]:
            parts = [p.strip() for p in line.split("|")]
            for p in parts:
                if re.search(
                    r"\b(Chennai|Bengaluru|Bangalore|Hyderabad|Pune|Mumbai|Delhi|Noida|Gurugram|Gurgaon|Coimbatore|Kochi|Trivandrum|India)\b",
                    p,
                    re.IGNORECASE,
                ):
                    if "@" not in p and not re.search(r"\d{5,}", p):
                        return p[:80]
        return None

    def _extract_experience(self, text: str) -> list[dict[str, Any]]:
        """Extract work experience entries supporting multi-line formats and standard date ranges."""
        experiences: list[dict[str, Any]] = []

        # 1. Look for the Experience section first
        exp_section_match = re.search(
            r"(?:PROFESSIONAL\s+EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT\s+HISTORY|WORK\s+HISTORY|EXPERIENCE)\s*[:\n](.*?)(?=\n\s*(?:KEY\s+PROJECTS|PROJECTS|EDUCATION|ACADEMIC|CERTIFICATIONS|AWARDS|SKILLS|TECHNICAL\s+SKILLS)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        section_text = exp_section_match.group(1) if exp_section_match else text

        date_regex = re.compile(
            r"((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4})\s*(?:–|-|to)\s*((?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+)?\d{4}|Present|Current)",
            re.IGNORECASE,
        )

        lines = [line.strip() for line in section_text.split("\n")]
        date_matches: list[tuple[int, re.Match]] = []
        for i, line in enumerate(lines):
            m = date_regex.search(line)
            if m:
                date_matches.append((i, m))

        if date_matches:
            for idx, (line_idx, match) in enumerate(date_matches):
                start_date = match.group(1).strip()
                end_date = match.group(2).strip()

                title = ""
                company = ""

                # Look at previous lines (within 3 lines)
                prev_lines = [
                    lines[j]
                    for j in range(max(0, line_idx - 3), line_idx)
                    if lines[j] and not lines[j].startswith(("▸", "•", "-", "*"))
                ]
                # Look at next lines (within 3 lines)
                next_lines = [
                    lines[j]
                    for j in range(line_idx + 1, min(len(lines), line_idx + 4))
                    if lines[j] and not lines[j].startswith(("▸", "•", "-", "*"))
                ]

                if prev_lines and next_lines:
                    title = prev_lines[-1]
                    company = next_lines[0]
                elif prev_lines:
                    if len(prev_lines) >= 2:
                        company = prev_lines[-2]
                        title = prev_lines[-1]
                    else:
                        title = prev_lines[-1]
                elif next_lines:
                    title = next_lines[0]
                    if len(next_lines) >= 2:
                        company = next_lines[1]

                # Extract bullet descriptions up to the next experience item
                bullets: list[str] = []
                next_limit = date_matches[idx + 1][0] if idx + 1 < len(date_matches) else len(lines)
                for j in range(line_idx + 1, next_limit):
                    l = lines[j]
                    if l == company or l == title:
                        continue
                    if l.startswith(("▸", "•", "-", "*")):
                        cleaned = re.sub(r"^[▸•\-\*]\s*", "", l)
                        if cleaned:
                            bullets.append(cleaned)
                    elif bullets:
                        # Continuation of previous bullet
                        bullets[-1] += " " + l
                    elif l and not any(kw in l.lower() for kw in ["project", "education"]):
                        bullets.append(l)

                # Clean up company if it contains pipe or comma for location
                location = ""
                if "|" in company:
                    parts = [p.strip() for p in company.split("|")]
                    company = parts[0]
                    if len(parts) > 1:
                        location = parts[1]

                if title or company:
                    experiences.append(
                        {
                            "title": title[:100],
                            "company": company[:100],
                            "location": location[:60],
                            "start": start_date,
                            "end": end_date,
                            "description": " ".join(bullets)[:1500],
                        }
                    )

        # Fallback to single-line regex if multi-line returned nothing
        if not experiences:
            exp_pattern = re.compile(
                r"(?:^|\n)(.+?)(?:\s*[\|–-]\s*)(.+?)(?:\s*[\|–-]\s*)"
                r"(\w+\s*\d{4})\s*(?:to|–|-)\s*(\w+\s*\d{4}|present|current)",
                re.IGNORECASE | re.MULTILINE,
            )
            for match in exp_pattern.finditer(text):
                experiences.append(
                    {
                        "company": match.group(1).strip()[:100],
                        "title": match.group(2).strip()[:100],
                        "start": match.group(3).strip(),
                        "end": match.group(4).strip(),
                        "description": "",
                    }
                )

        return experiences

    def _extract_education(self, text: str) -> list[dict[str, Any]]:
        """Extract education entries using pattern matching."""
        education: list[dict[str, Any]] = []
        edu_section_match = re.search(
            r"(?:EDUCATION|ACADEMIC\s+BACKGROUND|QUALIFICATIONS)\s*[:\n](.*?)(?=\n\s*(?:PROJECTS|EXPERIENCE|SKILLS|CERTIFICATIONS)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        search_lines = (
            edu_section_match.group(1).split("\n") if edu_section_match else text.split("\n")
        )
        for line in search_lines:
            clean = line.strip()
            if not clean:
                continue
            if re.search(
                r"\b(B\.?E\.?|B\.?Tech|B\.?S\.?|B\.?Sc|BCA|M\.?E\.?|M\.?Tech|M\.?S\.?|MCA|MBA|Bachelor|Master|Diploma|Degree)\b",
                clean,
                re.IGNORECASE,
            ):
                parts = [p.strip() for p in clean.split("|")]
                if len(parts) >= 2:
                    degree = parts[0]
                    institution = parts[1]
                    year = parts[2].replace("–", "-") if len(parts) > 2 else ""
                    education.append(
                        {
                            "degree": degree[:100],
                            "institution": institution[:100],
                            "year": year[:30],
                        }
                    )
                else:
                    education.append(
                        {
                            "degree": clean[:100],
                            "institution": "",
                        }
                    )

        # Fallback regex if empty
        if not education:
            edu_pattern = re.compile(
                r"(?:B\.?(?:Tech|E|S|Sc|A|Com)|M\.?(?:Tech|E|S|Sc|A|Com|BA)|Ph\.?D|MBA|BCA|MCA|Diploma)"
                r"[^,\n]*(?:,\s*|\s+from\s+|\s+at\s+|\s*[-–]\s*)([^\n,]+)",
                re.IGNORECASE,
            )
            for match in edu_pattern.finditer(text):
                education.append(
                    {
                        "degree": match.group(0).strip()[:100],
                        "institution": match.group(1).strip()[:100] if match.group(1) else "",
                    }
                )
        return education

    def _estimate_experience_years(self, text: str) -> float | None:
        """Estimate years of experience from text."""
        match = re.search(
            r"(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
            text,
            re.IGNORECASE,
        )
        if match:
            return float(match.group(1))
        return None

    def parse(self, file_path: str) -> ParsedResumeData:
        """Parse a resume file and return structured data."""
        raw_text = self.extract_text(file_path)
        return self.parse_text(raw_text)

    def parse_text(self, raw_text: str) -> ParsedResumeData:
        """Parse raw resume text and return structured data."""
        return ParsedResumeData(
            full_name=self._extract_name(raw_text),
            email=self._extract_email(raw_text),
            phone=self._extract_phone(raw_text),
            location=self._extract_location(raw_text),
            summary=self._extract_summary(raw_text),
            skills=self._extract_skills(raw_text),
            experience=self._extract_experience(raw_text),
            education=self._extract_education(raw_text),
            total_experience_years=self._estimate_experience_years(raw_text),
        )
