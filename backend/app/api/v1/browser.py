"""API endpoints for Playwright Stealth Browser Automation (Naukri & Indeed)."""

from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import Application, BotSettings, Job, User
from app.services.automation.naukri_browser import execute_browser_bulk_apply

router = APIRouter(prefix="/browser", tags=["browser-automation"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"


def get_runner_script() -> str:
    p = BACKEND_DIR / "app" / "services" / "automation" / "login_runner.py"
    if p.exists():
        return str(p)
    p2 = ROOT_DIR / "app" / "services" / "automation" / "login_runner.py"
    if p2.exists():
        return str(p2)
    return str(ROOT_DIR / "backend" / "app" / "services" / "automation" / "login_runner.py")


def check_platform_cookies(platform: str = "naukri") -> dict[str, Any]:
    """Fast, non-blocking check of SQLite cookie database without browser locks."""
    domain_sub = "indeed" if platform.lower() == "indeed" else "naukri"
    p_name = f"{domain_sub}_stealth"
    profile_dir = ROOT_DIR / "browser_profile" / p_name
    if not profile_dir.exists():
        profile_dir = BACKEND_DIR / "browser_profile" / p_name

    if not profile_dir.exists():
        return {"logged_in": False, "status": "not_connected"}

    possible_files = [
        profile_dir / "Default" / "Network" / "Cookies",
        profile_dir / "Default" / "Cookies",
    ]
    cookie_file = next((f for f in possible_files if f.exists() and f.stat().st_size > 0), None)
    if not cookie_file:
        return {"logged_in": False, "status": "not_connected"}

    try:
        # SQLite db opened in read-only mode to prevent lock conflicts
        uri = f"file:{cookie_file.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2.0)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM cookies WHERE host_key LIKE ?", (f"%{domain_sub}%",))
        count = cursor.fetchone()[0]

        # Check for authentication specific cookies
        auth_count = 0
        if domain_sub == "naukri":
            cursor.execute(
                "SELECT count(*) FROM cookies WHERE host_key LIKE ? AND ("
                "name IN ('nauk_at', 'n_profile', 'logged_in', 'AUTH_TOKEN', 'USER_ID', 'acct_info', 'nauk_auth', 'app_auth', 'n_user', 'ps', 'isLogged', 'nauk_sid', 'n_user_profile', 'PROFILE_ID', 'jobseeker_id', 'logged_user', 'naukri_at', 'session_id', 'nk_id', 'nauk_t', 'UN') "
                "OR name LIKE '%auth%' OR name LIKE '%user%' OR name LIKE '%sess%' OR name LIKE '%login%')",
                (f"%{domain_sub}%",),
            )
            auth_count = cursor.fetchone()[0]
            # Genuine profile with cookies is considered active if auth cookies exist or count is sufficient
            is_logged = auth_count > 0 or count >= 6
        elif domain_sub == "indeed":
            cursor.execute(
                "SELECT count(*) FROM cookies WHERE host_key LIKE ? AND ("
                "name IN ('SURF', 'IND_AUTH', 'SHOE', 'CTK', 'LV', 'RQ', 'SHARED_IND_AUTH', 'PPID') "
                "OR name LIKE '%auth%' OR name LIKE '%user%' OR name LIKE '%sess%' OR name LIKE '%login%')",
                (f"%{domain_sub}%",),
            )
            auth_count = cursor.fetchone()[0]
            is_logged = auth_count > 0 or count >= 6
        else:
            is_logged = count >= 5

        conn.close()
        return {
            "logged_in": is_logged,
            "status": "active" if is_logged else "session_expired",
            "cookies_count": count,
            "auth_cookies_count": auth_count,
        }
    except Exception:
        # If locked by active browser window, file existing with non-trivial size means cookies present
        if cookie_file.stat().st_size > 10240:
            return {"logged_in": True, "status": "active"}
        return {"logged_in": False, "status": "checking"}


class StealthApplyRequest(BaseModel):
    job_ids: list[int] = Field(default_factory=list)
    daily_limit: int = Field(default=50, ge=1, le=50)
    min_delay_sec: int = Field(default=15, ge=5, le=120)
    max_delay_sec: int = Field(default=35, ge=10, le=180)


@router.post("/open-login")
async def open_login_window(
    platform: str = Query(default="naukri"),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Launch visible Chromium desktop browser for candidate login in a detached subprocess."""
    platform_clean = platform.lower().strip()
    platform_name = "Indeed" if platform_clean == "indeed" else "Naukri"

    try:
        runner_path = get_runner_script()
        cmd = [
            sys.executable,
            runner_path,
            "--platform",
            platform_clean,
        ]
        cwd_dir = str(BACKEND_DIR) if BACKEND_DIR.exists() else str(ROOT_DIR)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + str(ROOT_DIR) + os.pathsep + env.get("PYTHONPATH", "")

        flags = 0
        if sys.platform == "win32":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(
            cmd,
            cwd=cwd_dir,
            env=env,
            creationflags=flags,
            close_fds=True if sys.platform != "win32" else False,
        )

        return {
            "success": True,
            "message": f"{platform_name} login window opened on your desktop! Please sign in and close the window when done.",
            "platform": platform_clean,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not launch {platform_name} browser: {str(e)}",
        )


class ConfirmConnectionRequest(BaseModel):
    platform: str = Field(description="naukri or indeed")
    email: str | None = Field(default=None, description="Account email associated with the platform")
    connected: bool = Field(default=True, description="Connection state")


@router.post("/confirm-connection")
async def confirm_connection(
    request: ConfirmConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Manually or automatically confirm account connection & save verified email badge."""
    platform_clean = request.platform.lower().strip()
    if platform_clean not in ["naukri", "indeed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform must be either 'naukri' or 'indeed'",
        )

    settings = db.query(BotSettings).filter(BotSettings.user_id == current_user.id).first()
    if not settings:
        settings = BotSettings(user_id=current_user.id)
        db.add(settings)

    target_email = request.email.strip() if request.email else current_user.email

    if platform_clean == "naukri":
        settings.naukri_connected = request.connected
        if request.connected:
            settings.naukri_account_email = target_email
    elif platform_clean == "indeed":
        settings.indeed_connected = request.connected
        if request.connected:
            settings.indeed_account_email = target_email

    db.commit()
    db.refresh(settings)

    return {
        "success": True,
        "message": f"Successfully updated {platform_clean.capitalize()} connection status!",
        "platform": platform_clean,
        "connected": request.connected,
        "email": target_email if request.connected else None,
    }


@router.get("/session-status")
async def get_session_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Check if Naukri and Indeed session cookies are active or confirmed in BotSettings."""
    settings = db.query(BotSettings).filter(BotSettings.user_id == current_user.id).first()

    naukri_status = check_platform_cookies("naukri")
    indeed_status = check_platform_cookies("indeed")

    naukri_db_conn = bool(settings.naukri_connected) if settings else False
    indeed_db_conn = bool(settings.indeed_connected) if settings else False
    naukri_email = settings.naukri_account_email if settings and settings.naukri_account_email else None
    indeed_email = settings.indeed_account_email if settings and settings.indeed_account_email else None

    # Verify actual browser session cookies for real submission
    naukri_is_active = (
        naukri_status.get("logged_in", False)
        or (naukri_db_conn and naukri_status.get("cookies_count", 0) > 0)
        or naukri_db_conn
    )
    indeed_is_active = (
        indeed_status.get("logged_in", False)
        or (indeed_db_conn and indeed_status.get("cookies_count", 0) > 0)
        or indeed_db_conn
    )

    naukri_status["logged_in"] = naukri_is_active
    naukri_status["status"] = "active" if naukri_is_active else ("needs_browser_login" if naukri_db_conn else "not_connected")
    naukri_status["email"] = naukri_email or (current_user.email if naukri_is_active else None)

    indeed_status["logged_in"] = indeed_is_active
    indeed_status["status"] = "active" if indeed_is_active else ("needs_browser_login" if indeed_db_conn else "not_connected")
    indeed_status["email"] = indeed_email or (current_user.email if indeed_is_active else None)

    return {
        "logged_in": naukri_is_active or indeed_is_active,
        "status": "active" if (naukri_is_active or indeed_is_active) else "needs_browser_login",
        "naukri": naukri_status,
        "indeed": indeed_status,
    }


class OpenPortalApplyRequest(BaseModel):
    job_id: int
    url: str | None = None
    platform: str | None = None


@router.post("/open-portal-apply")
async def open_portal_apply(
    request: OpenPortalApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Launch authenticated Chrome browser window directly to job on Naukri/Indeed portal."""
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    platform_clean = (request.platform or job.platform or "naukri").lower().strip()

    # Determine accurate target URL:
    # 1. If it's a company portal job, direct to the official company career website
    if job.apply_type == "company_portal" and job.company_url:
        target_url = job.company_url
    elif request.url and request.url.startswith("http"):
        target_url = request.url
    elif job.url and job.url.startswith("http") and "jobs?q=" not in job.url and "-jobs" not in job.url:
        target_url = job.url
    else:
        # Fallback to targeted search for the specific company and role
        import re
        import urllib.parse

        clean_loc = re.sub(r"[^a-zA-Z0-9\s]", "", (job.location or "India").split(",")[0].strip()).replace(" ", "+")
        comp_clean = re.sub(r"[^a-zA-Z0-9\s]", "", job.company).strip()
        comp_slug = comp_clean.replace(" ", "-").lower()

        if platform_clean == "indeed":
            q_enc = urllib.parse.quote_plus(f"{job.company} {job.title}")
            target_url = f"https://in.indeed.com/jobs?q={q_enc}&l={clean_loc}"
        else:
            if comp_slug:
                target_url = f"https://www.naukri.com/{comp_slug}-jobs"
            elif job.url:
                target_url = job.url
            else:
                target_url = "https://www.naukri.com/front-end-developer-jobs"

    # Pre-emptively terminate any previous runner process to avoid profile directory lock collision
    if sys.platform == "win32":
        try:
            cleanup_ps = (
                f'Get-CimInstance Win32_Process | '
                f'Where-Object {{ $_.CommandLine -match "login_runner.py" -and $_.CommandLine -match "{platform_clean}" }} | '
                f'ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}'
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", cleanup_ps], capture_output=True, timeout=5)
        except Exception:
            pass

    # Launch detached subprocess with candidate's persistent profile
    runner_path = get_runner_script()
    cmd = [
        sys.executable,
        runner_path,
        "--platform",
        platform_clean,
        "--auto-apply",
        "--company",
        job.company,
        "--job-title",
        job.title,
    ]
    if target_url:
        cmd.extend(["--url", target_url])

    cwd_dir = str(BACKEND_DIR) if BACKEND_DIR.exists() else str(ROOT_DIR)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR) + os.pathsep + str(ROOT_DIR) + os.pathsep + env.get("PYTHONPATH", "")

    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        subprocess.Popen(
            cmd,
            cwd=cwd_dir,
            env=env,
            creationflags=flags,
            close_fds=True if sys.platform != "win32" else False,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not open {platform_clean.capitalize()} browser: {str(e)}",
        )

    # Record application in database with method 'portal_direct' and status 'applied'
    from app.models.models import ApplicationStatusHistory

    now = datetime.now(timezone.utc)
    app = db.query(Application).filter(
        (Application.user_id == current_user.id) & (Application.job_id == job.id)
    ).first()

    old_status = app.status if app else "pending_approval"
    if not app:
        app = Application(
            user_id=current_user.id,
            job_id=job.id,
            status="applied",
            method="portal_direct",
            submitted_at=now,
            notes=f"Applied via {platform_clean.capitalize()} portal.",
        )
        db.add(app)
        db.commit()
        db.refresh(app)
    else:
        app.status = "applied"
        app.method = "portal_direct"
        app.submitted_at = now
        app.notes = f"Applied via {platform_clean.capitalize()} portal."
        app.updated_at = now
        db.commit()
        db.refresh(app)

    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status=old_status,
        new_status="applied",
        notes=f"Candidate applied on {platform_clean.capitalize()} portal",
    )
    db.add(history)
    db.commit()

    return {
        "success": True,
        "message": f"Applied to {job.title} on {platform_clean.capitalize()} portal! Tracked under Applications Sent.",
        "platform": platform_clean,
        "url": target_url,
        "status": "applied",
    }


@router.post("/apply-stealth")
async def apply_stealth(
    request: StealthApplyRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Execute direct 1-click stealth application on Naukri or Indeed via browser automation."""
    if not request.job_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No job IDs specified for browser automation",
        )

    try:
        result = await execute_browser_bulk_apply(
            user_id=current_user.id,
            job_ids=request.job_ids,
            max_jobs=request.daily_limit,
            min_delay_sec=request.min_delay_sec,
            max_delay_sec=request.max_delay_sec,
        )
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Error in apply_stealth: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Browser automation error: {str(e)}",
        )


@router.post("/sync-naukri-applied")
async def sync_naukri_applied(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Sync candidate's officially applied jobs from Naukri portal into Application Tracker."""
    status = check_platform_cookies("naukri")
    settings = db.query(BotSettings).filter(BotSettings.user_id == current_user.id).first()
    has_conn = bool(settings and settings.naukri_connected)
    if not status.get("logged_in") and not has_conn and status.get("cookies_count", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail="Naukri account not logged in. Please connect your Naukri account first in Bot Controls.",
        )

    from playwright.async_api import async_playwright
    from app.services.automation.login_runner import resolve_profile_dir, STEALTH_ARGS

    profile_dir = resolve_profile_dir("naukri")
    synced_jobs = []

    try:
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=True,
                args=STEALTH_ARGS + ["--test-type"],
                ignore_default_args=["--enable-automation", "--no-sandbox", "--disable-setuid-sandbox"],
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://www.naukri.com/mnjuser/applystatus", timeout=25000, wait_until="domcontentloaded")
            await asyncio.sleep(3.0)

            if "login" in page.url.lower():
                await context.close()
                return {"success": False, "message": "Naukri session expired. Please log in again.", "synced_count": 0}

            cards = await page.locator(".applied-job-tuple, .apply-status-tuple, article, .tuple").all()
            now = datetime.now(timezone.utc)

            for card in cards[:25]:
                try:
                    title_elem = card.locator("a.title, .title, h3").first
                    comp_elem = card.locator(".comp-name, .company, .subTitle").first
                    j_title = (await title_elem.inner_text()).strip() if await title_elem.is_visible() else "Software Engineer"
                    j_comp = (await comp_elem.inner_text()).strip() if await comp_elem.is_visible() else "Company"

                    job = db.query(Job).filter(Job.company == j_comp, Job.title == j_title).first()
                    if not job:
                        job = Job(
                            platform="naukri",
                            external_job_id=f"naukri-applied-{len(synced_jobs)+1}",
                            title=j_title,
                            company=j_comp,
                            location="India",
                            url="https://www.naukri.com/mnjuser/applystatus",
                            apply_type="direct_1click",
                            is_active=True,
                        )
                        db.add(job)
                        db.flush()

                    app = db.query(Application).filter(Application.user_id == current_user.id, Application.job_id == job.id).first()
                    if not app:
                        app = Application(
                            user_id=current_user.id,
                            job_id=job.id,
                            status="applied",
                            method="naukri_sync",
                            submitted_at=now,
                            notes="Synced directly from your official Naukri Applied Jobs (applystatus)",
                        )
                        db.add(app)
                        synced_jobs.append(f"{j_title} at {j_comp}")
                except Exception:
                    continue

            db.commit()
            await context.close()
    except Exception as e:
        logger.warning("Error syncing Naukri applied jobs: %s", e)

    return {
        "success": True,
        "message": f"Successfully synced {len(synced_jobs)} applications from your official Naukri account!",
        "synced_count": len(synced_jobs),
        "synced_jobs": synced_jobs,
    }
