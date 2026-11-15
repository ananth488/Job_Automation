"""Resume parsing service — extracts text and structured data from PDF/DOCX files."""

import re
from pathlib import Path
from typing import Any

from app.schemas.resume import ParsedResumeData


class ResumeParser:
    """Parses uploaded resume files into structured data without false positives."""

    # Canonical mapping of skills with display casing
    SKILLS_MAP: dict[str, str] = {
        # Programming Languages
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

    def _extract_skills(self, text: str) -> list[str]:
        """Extract skills using strict word boundaries to avoid false positives (e.g. Java from JavaScript)."""
        found_skills: set[str] = set()

        # Check if there is an isolated Skills section for higher precision
        skills_section_match = re.search(
            r"(?:technical\s+skills|skills|core\s+competencies|technologies|tools\s*&\s*technologies)\s*[:\n](.*?)(?=\n\s*(?:work\s+experience|experience|employment|education|projects|certifications|awards|summary)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        search_corpus = text
        if skills_section_match and len(skills_section_match.group(1).strip()) > 15:
            # Also search specifically inside skills section
            search_corpus = skills_section_match.group(1) + "\n" + text

        for keyword, display_name in self.SKILLS_MAP.items():
            # 1. Special rule for Java: MUST NOT match JavaScript
            if keyword == "java":
                pattern = r"\bjava\b(?!\s*script)"
                if re.search(pattern, search_corpus, re.IGNORECASE):
                    found_skills.add(display_name)
                continue

            # 2. Special rule for REST: only match REST API, RESTful, or uppercase standalone REST
            if keyword in ("rest", "rest api", "restful"):
                pattern = r"\b(?:REST\s*API|RESTful(?:\s*API)?|\bREST\b)\b"
                if re.search(pattern, search_corpus):
                    found_skills.add(display_name)
                continue

            # 3. Special rule for Go: must be standalone Go or Golang
            if keyword == "go":
                pattern = r"\b(?:golang|\bgo\b(?:\s*programming|\s*developer|\s*backend)?)"
                if re.search(pattern, search_corpus, re.IGNORECASE):
                    # To avoid common English word "go", only match if Golang or in technical context
                    if re.search(r"\bgolang\b", search_corpus, re.IGNORECASE) or (skills_section_match and re.search(r"\bgo\b", skills_section_match.group(1), re.IGNORECASE)):
                        found_skills.add(display_name)
                continue

            # 4. Special rule for C++ / C# / .NET
            if keyword == "c++":
                if re.search(r"(?:\b|\s)c\+\+(?:[\s,;.\)]|$)", search_corpus, re.IGNORECASE):
                    found_skills.add(display_name)
                continue
            if keyword == "c#":
                if re.search(r"(?:\b|\s)c\#(?:[\s,;.\)]|$)", search_corpus, re.IGNORECASE):
                    found_skills.add(display_name)
                continue
            if keyword == ".net":
                if re.search(r"(?:\b|\s)\.net(?:\b|[\s,;.\)]|$)", search_corpus, re.IGNORECASE):
                    found_skills.add(display_name)
                continue

            # 5. All other skills: STRICT WORD BOUNDARIES
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, search_corpus, re.IGNORECASE):
                found_skills.add(display_name)

        return sorted(found_skills)

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
