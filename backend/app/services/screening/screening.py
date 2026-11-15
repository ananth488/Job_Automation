"""Screening question answer generation service."""

from __future__ import annotations

import re
from typing import Any

from app.models.models import CandidateProfile, CommonAnswer


class ScreeningService:
    """Generates answers for common screening questions."""

    # Common patterns and categories
    PATTERNS: dict[str, list[str]] = {
        "notice_period": [
            r"notice\s*period",
            r"how\s*(?:soon|quickly)\s*(?:can\s*you)?\s*join",
            r"availability\s*(?:to\s*)?start",
        ],
        "ctc": [
            r"current\s*(?:ctc|salary|compensation)",
            r"expected\s*(?:ctc|salary|compensation)",
            r"salary\s*expectation",
        ],
        "authorization": [
            r"work\s*(?:authorization|permit|visa)",
            r"legally\s*(?:authorized|eligible)",
            r"right\s*to\s*work",
        ],
        "relocation": [
            r"(?:willing|open)\s*to\s*relocat",
            r"relocation",
        ],
        "experience_years": [
            r"(?:years?|yrs?)\s*(?:of\s*)?experience",
            r"how\s*(?:many|much)\s*experience",
        ],
    }

    def categorize_question(self, question: str) -> str:
        """Categorize a screening question."""
        q_lower = question.lower()
        for category, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, q_lower):
                    return category
        return "general"

    def generate_answer(
        self,
        question: str,
        profile: CandidateProfile,
        common_answers: list[CommonAnswer] | None = None,
    ) -> dict[str, Any]:
        """Generate an answer for a screening question."""
        category = self.categorize_question(question)

        # Check for user-defined common answers first
        if common_answers:
            for ca in common_answers:
                if ca.category == category or re.search(
                    ca.question_pattern, question, re.IGNORECASE
                ):
                    return {
                        "answer": ca.answer,
                        "confidence": 0.95,
                        "source": "common_answers",
                    }

        # Generate based on category
        if category == "notice_period":
            return {
                "answer": "I can join within 30 days of offer acceptance.",
                "confidence": 0.7,
                "source": "template",
            }
        elif category == "ctc":
            return {
                "answer": "I am open to discussing compensation based on the role and responsibilities.",
                "confidence": 0.6,
                "source": "template",
            }
        elif category == "authorization":
            return {
                "answer": "Yes, I am authorized to work in the required location.",
                "confidence": 0.7,
                "source": "template",
            }
        elif category == "relocation":
            return {
                "answer": "Yes, I am open to relocation for the right opportunity.",
                "confidence": 0.7,
                "source": "template",
            }
        elif category == "experience_years":
            years = profile.total_experience_years
            if years is not None:
                return {
                    "answer": f"I have {years} years of professional experience.",
                    "confidence": 0.9,
                    "source": "profile",
                }
            return {
                "answer": "I have several years of relevant professional experience.",
                "confidence": 0.5,
                "source": "template",
            }
        else:
            return {
                "answer": "Please allow me to provide more details during the interview.",
                "confidence": 0.3,
                "source": "fallback",
            }
