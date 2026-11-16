import pytest
from app.services.resume_parser.parser import ResumeParser


@pytest.fixture
def parser():
    return ResumeParser()


def test_parse_ananth_resume(parser):
    result = parser.parse("backend/uploads/1/Ananth_P_Resume_old.pdf")
    assert len(result.experience) == 2

    # Job 1
    job1 = result.experience[0]
    assert job1["title"] == "Front End Developer"
    assert "LegalOptix" in job1["company"]
    assert job1["location"] == "Chennai"
    assert job1["start"] == "Feb 2026"
    assert job1["end"] == "Sep 2026"

    # Job 2
    job2 = result.experience[1]
    assert job2["title"] == "Front End Developer"
    assert "Piccosoft" in job2["company"]
    assert job2["location"] == "Chennai"
    assert job2["start"] == "Dec 2023"
    assert job2["end"] == "Nov 2025"
    assert len(job2["description"]) > 50


def test_classify_header_pipe_format(parser):
    title, company, loc = parser._classify_experience_header(["Senior Software Engineer | TechCorp | Bengaluru, India"])
    assert title == "Senior Software Engineer"
    assert company == "TechCorp"
    assert "Bengaluru" in loc


def test_classify_header_reverse_order(parser):
    title, company, loc = parser._classify_experience_header(["LegalOptix Private Limited • Chennai", "Front End Developer"])
    assert title == "Front End Developer"
    assert "LegalOptix" in company
    assert loc == "Chennai"


def test_classify_medical_coding(parser):
    title, company, loc = parser._classify_experience_header(["Omega Healthcare Management Services", "Medical Coder", "Chennai"])
    assert title == "Medical Coder"
    assert "Omega Healthcare" in company
    assert loc == "Chennai"


def test_classify_hospital_nurse(parser):
    title, company, loc = parser._classify_experience_header(["Staff Nurse", "Apollo Hospitals | Chennai"])
    assert title == "Staff Nurse"
    assert "Apollo Hospitals" in company
    assert loc == "Chennai"
