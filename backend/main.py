"""FastAPI Application entry point for AI Job Application Bot."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.models import (
    User,
    CandidateProfile,
    Preference,
    Job,
    JobMatch,
    Application,
    ApplicationStatusHistory,
    GeneratedDocument,
    ScreeningAnswer,
    CommonAnswer,
    Notification,
    BotSettings,
    BotRun,
)
from app.workers.scheduler import start_scheduler, stop_scheduler

COMPANY_CAREERS = {
    # Naukri companies
    "Kovai.co": "https://careers.kovaico.com/jobs",
    "Ideas2IT Technologies": "https://www.ideas2it.com/careers",
    "Facilio": "https://facilio.com/careers/",
    "Zuci Systems": "https://www.zucisystems.com/careers/",
    "Freshworks": "https://www.freshworks.com/company/careers/",
    "Hippo Video": "https://www.hippovideo.io/careers.html",
    "Gofrugal Technologies": "https://www.gofrugal.com/careers",
    "Spritle Software": "https://www.spritle.com/careers",
    "Chargebee": "https://www.chargebee.com/careers/",
    "Kissflow": "https://kissflow.com/careers/",
    "Contus": "https://www.contus.com/careers.php",
    "AppviewX": "https://www.appviewx.com/careers/",
    "Skcript Technologies": "https://skcript.com/careers/",
    "Syncfusion": "https://www.syncfusion.com/company/careers",
    "Hasura": "https://hasura.io/careers/",
    "Clevertap": "https://clevertap.com/careers/",
    "Keka HR": "https://www.keka.com/careers",
    "Darwinbox": "https://darwinbox.com/careers",
    "Yellow.ai": "https://yellow.ai/careers/",
    "Mad Street Den (Vue.ai)": "https://www.madstreetden.com/careers/",
    "Indium Software": "https://www.indiumsoftware.com/careers/",
    "Hakuna Matata Solutions": "https://www.hakunamatatatech.com/careers/",
    "Impiger Technologies": "https://www.impigertech.com/careers/",
    "LatentView Analytics": "https://www.latentview.com/careers/",
    "Thoughtworks": "https://www.thoughtworks.com/careers/jobs",
    "Zoho Corporation": "https://careers.zohocorp.com/jobs/Careers",
    "Cognizant": "https://careers.cognizant.com/global/en",
    "LTIMindtree": "https://www.ltimindtree.com/careers/",
    # Indeed companies
    "Zerodha": "https://zerodha.com/careers",
    "Ather Energy": "https://careers.atherenergy.com/",
    "Razorpay": "https://razorpay.com/jobs/",
    "Swiggy": "https://careers.swiggy.com/",
    "CRED": "https://cred.club/careers",
    "Juspay": "https://juspay.in/careers",
    "Urban Company": "https://careers.urbancompany.com/",
    "Groww": "https://groww.in/careers",
    "Zepto": "https://www.zeptonow.com/careers",
    "Meesho": "https://www.meesho.io/jobs",
    "CoinSwitch": "https://coinswitch.co/careers",
    "Pine Labs": "https://www.pinelabs.com/careers",
    "Flipkart": "https://www.flipkartcareers.com/",
    "Paytm": "https://paytm.com/careers",
    "Porter": "https://porter.in/careers",
    "BrowserStack": "https://www.browserstack.com/careers",
}


RESET_FLAG_FILE = Path(__file__).resolve().parent / ".db_reset_done"


def reset_database_fully():
    """Drop and recreate all tables fresh."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    RESET_FLAG_FILE.touch()
    print("\n" + "=" * 60)
    print("[DATABASE RESET] All tables successfully dropped and recreated fresh!")
    print("=" * 60 + "\n")


async def seed_initial_fresh_jobs():
    """Seed 50 fresh live-compatible jobs (25 Naukri + 25 Indeed)."""
    from app.platforms.naukri import NaukriAdapter
    from app.platforms.indeed import IndeedAdapter

    n_ad = NaukriAdapter()
    i_ad = IndeedAdapter()

    n_jobs = await n_ad.search_jobs(
        keywords=["Frontend Developer", "React", "TypeScript", "Next.js"],
        locations=["Chennai", "Bengaluru", "Hyderabad", "Remote"],
        limit=25,
    )
    i_jobs = await i_ad.search_jobs(
        keywords=["Frontend Developer", "React", "TypeScript", "Next.js"],
        locations=["Chennai", "Bengaluru", "Hyderabad", "Remote"],
        limit=25,
    )

    db: Session = SessionLocal()
    try:
        for item in n_jobs + i_jobs:
            j = Job(**item)
            db.add(j)
        db.commit()
        print(f"[DATABASE RESET] Successfully seeded {len(n_jobs) + len(i_jobs)} fresh jobs into database.")
    except Exception as e:
        print(f"[DATABASE RESET] Seed error: {e}")
        db.rollback()
    finally:
        db.close()


def sync_company_career_links():
    """Ensure all job records in the database have their accurate company career URL and appropriate apply_type."""
    db: Session = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"\n=======================================================")
        print(f"[AUTH DIAGNOSTIC] Current DB Users: {[(u.id, u.email) for u in users]}")
        print(f"=======================================================\n")

        jobs = db.query(Job).all()
        for j in jobs:
            comp_url = COMPANY_CAREERS.get(j.company)
            if comp_url:
                if j.company_url != comp_url:
                    j.company_url = comp_url
        db.commit()
    except Exception as e:
        print(f"[AUTH DIAGNOSTIC] Error: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for startup and shutdown procedures."""
    # Ensure upload directory exists
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Ensure all tables exist in target database (SQLite or Neon PostgreSQL)
    Base.metadata.create_all(bind=engine)

    # Perform initial seed or full database reset if requested
    if not RESET_FLAG_FILE.exists():
        reset_database_fully()
        await seed_initial_fresh_jobs()
    else:
        # Check if database is empty (e.g. freshly connected Neon Postgres)
        check_db: Session = SessionLocal()
        try:
            if check_db.query(Job).count() == 0:
                print("[DATABASE] Fresh database detected with 0 jobs. Seeding initial fresh jobs...")
                await seed_initial_fresh_jobs()
        except Exception as e:
            print(f"[DATABASE] Job count check note: {e}")
        finally:
            check_db.close()

    # Sync company career links to fix any previous mismatches
    sync_company_career_links()

    # Start background scheduler
    start_scheduler()

    yield

    # Teardown
    stop_scheduler()


app = FastAPI(
    title="AI Job Application Bot API",
    description="Intelligent automated job discovery, resume matching, and candidate-assisted application platform.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

# Include master API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Health check and API root."""
    return {
        "status": "online",
        "service": "AI Job Application Bot API",
        "version": "1.0.0",
        "docs": "/docs",
    }
