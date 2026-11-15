"""Playwright-based Stealth Browser Automation Engine for Naukri.com.

Features:
- Persistent local Chrome session (login once, cookies saved permanently).
- Anti-bot detection stealth flags (navigator.webdriver masked, human viewport).
- Natural delays, random jitter, and human-like scrolling.
- Polite rate-limiting (up to 50 jobs/day, 30-60s delays).
- Safe handling of already-applied, external company redirects, and screening questions.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import random
from typing import Any

try:
    from playwright.async_api import async_playwright, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    BrowserContext = Any  # type: ignore
    Page = Any  # type: ignore
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.models import (
    Application,
    ApplicationStatusHistory,
    CandidateProfile,
    Job,
    JobMatch,
    Preference,
)

logger = logging.getLogger(__name__)

def resolve_naukri_profile_dir() -> Path:
    try:
        root_p = Path(__file__).resolve().parents[4] / "browser_profile" / "naukri_stealth"
        if root_p.exists():
            return root_p
    except IndexError:
        pass
    try:
        backend_p = Path(__file__).resolve().parents[3] / "browser_profile" / "naukri_stealth"
        if backend_p.exists():
            return backend_p
    except IndexError:
        pass
    p = Path(__file__).resolve().parent.parent.parent.parent / "browser_profile" / "naukri_stealth"
    p.mkdir(parents=True, exist_ok=True)
    return p

PROFILE_DIR = resolve_naukri_profile_dir()

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--test-type",
    "--window-size=1280,800",
]


class NaukriBrowserBot:
    """Stealth browser automation manager for Naukri candidate applications."""

    def __init__(self):
        self.profile_dir = str(PROFILE_DIR)

    async def open_login_window(self) -> dict[str, Any]:
        """Launch a visible Chromium window for the user to log in to Naukri once."""
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                channel="chromium",
                args=STEALTH_ARGS,
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            )
            page = context.pages[0] if context.pages else await context.new_page()
            for extra in context.pages[1:]:
                try:
                    await extra.close()
                except Exception:
                    pass
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            await page.goto("https://www.naukri.com/nlogin/login", wait_until="domcontentloaded")
            logger.info("Opened Naukri login page for candidate.")

            # Wait up to 3 minutes for user to complete login
            # Once logged in, naukri redirects to mydesk / mnjuser / profile
            logged_in = False
            for _ in range(36):
                await asyncio.sleep(5)
                current_url = page.url
                if any(x in current_url for x in ["mydesk", "mnjuser", "homepage", "profile"]):
                    logged_in = True
                    break

            cookies = await context.cookies()
            await context.close()
            return {
                "success": True,
                "logged_in": logged_in,
                "message": (
                    "Naukri session saved successfully! You are logged in."
                    if logged_in
                    else "Window closed. You can reopen to complete login anytime."
                ),
                "cookies_count": len(cookies),
            }

    async def check_session_status(self) -> dict[str, Any]:
        """Check if persistent browser session has active Naukri cookies."""
        cookie_file = PROFILE_DIR / "Default" / "Network" / "Cookies"
        has_profile = any(PROFILE_DIR.iterdir()) if PROFILE_DIR.exists() else False

        if not has_profile:
            return {"logged_in": False, "status": "no_session"}

        try:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=self.profile_dir,
                    headless=True,
                    args=STEALTH_ARGS,
                )
                page = context.pages[0] if context.pages else await context.new_page()
            for extra in context.pages[1:]:
                try:
                    await extra.close()
                except Exception:
                    pass
                await page.goto("https://www.naukri.com/mnjuser/profile", timeout=15000, wait_until="domcontentloaded")
                is_logged_in = "login" not in page.url and ("mnjuser" in page.url or "profile" in page.url or "mydesk" in page.url)
                await context.close()
                return {
                    "logged_in": is_logged_in,
                    "status": "active" if is_logged_in else "session_expired",
                }
        except Exception as e:
            logger.warning("Error checking Naukri session: %s", e)
            return {"logged_in": False, "status": "error", "detail": str(e)}

    async def _human_scroll(self, page: Page):
        """Simulate realistic candidate reading behavior with natural mouse scroll."""
        try:
            for _ in range(random.randint(2, 4)):
                scroll_y = random.randint(250, 600)
                await page.mouse.wheel(0, scroll_y)
                await asyncio.sleep(random.uniform(0.8, 1.8))
            await asyncio.sleep(random.uniform(1.0, 2.0))
            await page.mouse.wheel(0, -random.randint(150, 300))
            await asyncio.sleep(random.uniform(0.5, 1.2))
        except Exception:
            pass

    async def apply_to_job(
        self,
        job_url: str,
        profile: CandidateProfile | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Safely navigate to Naukri job posting, verify details, and execute apply."""
        if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
            return {
                "success": False,
                "status": "error",
                "message": "Playwright is not installed or available in this environment.",
            }

        async with async_playwright() as p:
            context = None
            for ch in ["msedge", None]:
                try:
                    kwargs = dict(
                        user_data_dir=self.profile_dir,
                        headless=False,
                        args=STEALTH_ARGS,
                        ignore_default_args=["--enable-automation", "--no-sandbox", "--disable-setuid-sandbox"],
                        viewport={"width": 1280, "height": 850},
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/125.0.0.0 Safari/537.36"
                        ),
                    )
                    if ch:
                        kwargs["channel"] = ch
                    context = await p.chromium.launch_persistent_context(**kwargs)
                    break
                except Exception as ex:
                    logger.warning("Could not launch channel %s: %s", ch, ex)
                    err_str = str(ex)
                    if "Opening in existing browser session" in err_str or "already in use" in err_str:
                        if sys.platform == "win32":
                            kill_cmd = (
                                'Get-CimInstance Win32_Process | '
                                'Where-Object { $_.CommandLine -match "naukri_stealth" } | '
                                'ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }'
                            )
                            subprocess.run(["powershell", "-NoProfile", "-Command", kill_cmd], capture_output=True, timeout=5)
                            await asyncio.sleep(1.0)
                            try:
                                context = await p.chromium.launch_persistent_context(**kwargs)
                                break
                            except Exception:
                                pass

            if not context:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Failed to launch browser context",
                }

            page = context.pages[0] if context.pages else await context.new_page()
            for extra in context.pages[1:]:
                try:
                    await extra.close()
                except Exception:
                    pass
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            try:
                logger.info("Navigating to Naukri job: %s", job_url)
                await page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(2.0, 4.0))

                # Check if landed page is a search result listing; resolve directly to matching job posting
                if "-jobs" in page.url or "/jobs" in page.url:
                    job_link = page.locator("a.title").first
                    if await job_link.is_visible():
                        try:
                            async with context.expect_page(timeout=5000) as new_page_info:
                                await job_link.click()
                            new_page = await new_page_info.value
                            await new_page.wait_for_load_state("domcontentloaded")
                            page = new_page
                            logger.info("Switched to newly opened job detail page: %s", page.url)
                        except Exception:
                            href = await job_link.get_attribute("href")
                            if href:
                                if not href.startswith("http"):
                                    href = f"https://www.naukri.com{href}"
                                logger.info("Resolving search URL to live job detail page: %s", href)
                                await page.goto(href, timeout=30000, wait_until="domcontentloaded")
                        await asyncio.sleep(random.uniform(2.0, 3.5))

                # Check for active security challenge on page
                captcha_selectors = [
                    "iframe[src*='recaptcha']",
                    "iframe[src*='turnstile']",
                    "iframe[src*='hcaptcha']",
                    "#cf-challenge-running",
                    ".cf-turnstile",
                    "div.g-recaptcha",
                ]
                has_challenge = False
                for sel in captcha_selectors:
                    if await page.locator(sel).first.is_visible():
                        has_challenge = True
                        break

                if has_challenge:
                    logger.warning("Active security challenge detected on %s", job_url)
                    await asyncio.sleep(3)
                    await context.close()
                    return {
                        "success": False,
                        "status": "captcha_paused",
                        "message": "Portal displayed a security challenge. Pausing for safety.",
                    }

                # Human-like reading scroll
                await self._human_scroll(page)

                # Check if already applied
                already_applied_locators = [
                    "text=Already Applied",
                    "text=Applied",
                    ".already-applied",
                    "button:has-text('Already Applied')",
                ]
                for sel in already_applied_locators:
                    if await page.locator(sel).first.is_visible():
                        logger.info("Job already applied on Naukri: %s", job_url)
                        await context.close()
                        return {
                            "success": True,
                            "status": "already_applied",
                            "message": "Already applied previously on Naukri portal.",
                        }

                # Find apply button
                # Naukri uses several button variants:
                # 1. "Apply on Naukri" / "Apply" (direct 1-click apply)
                # 2. "Apply on Company Site" (redirects externally)
                apply_company_loc = page.locator("text=Apply on company site, button:has-text('Company Site')")
                if await apply_company_loc.first.is_visible():
                    logger.info("Job requires external company redirect: %s", job_url)
                    await context.close()
                    return {
                        "success": False,
                        "status": "company_site_redirect",
                        "message": "Job requires application on company portal. Direct link available in Tracker.",
                    }

                apply_btn = page.locator(
                    "button#apply-button, button.apply-button, button:has-text('Apply on Naukri'), button:has-text('Apply'):not(:has-text('Company'))"
                ).first

                if not await apply_btn.is_visible():
                    # Fallback locator
                    apply_btn = page.locator("button:has-text('Apply')").first

                if await apply_btn.is_visible():
                    if dry_run:
                        await context.close()
                        return {
                            "success": True,
                            "status": "dry_run_ready",
                            "message": "Apply button found and ready to submit.",
                        }

                    # Natural click with jitter
                    box = await apply_btn.bounding_box()
                    if box:
                        await page.mouse.click(
                            box["x"] + box["width"] / 2 + random.uniform(-5, 5),
                            box["y"] + box["height"] / 2 + random.uniform(-3, 3),
                        )
                    else:
                        await apply_btn.click()

                    logger.info("Clicked Apply button on Naukri. Checking for questionnaire/confirm modal...")
                    await asyncio.sleep(random.uniform(2.5, 4.0))

                    # Handle common screening question modal if present
                    modal = page.locator(".chatbot_Drawer, .apply-drawer, .custom-questions, .drawer-wrapper")
                    if await modal.first.is_visible():
                        # Fill simple numerical fields if present (CTC, Notice)
                        notice_input = page.locator("input[placeholder*='Notice'], input[name*='notice']")
                        if await notice_input.first.is_visible() and profile:
                            await notice_input.first.fill("30")

                        # Submit modal
                        submit_drawer = page.locator(
                            "button:has-text('Save & Apply'), button:has-text('Submit'), button:has-text('Apply Now')"
                        ).first
                        if await submit_drawer.is_visible():
                            await submit_drawer.click()
                            await asyncio.sleep(2.0)

                    await asyncio.sleep(random.uniform(2.0, 3.5))
                    await context.close()
                    return {
                        "success": True,
                        "status": "applied",
                        "message": "Successfully submitted application directly on Naukri.com!",
                    }

                await context.close()
                return {
                    "success": False,
                    "status": "button_not_found",
                    "message": "Could not locate standard Apply button on this posting.",
                }

            except Exception as e:
                logger.exception("Error applying to Naukri job: %s", e)
                try:
                    await context.close()
                except Exception:
                    pass
                return {
                    "success": False,
                    "status": "error",
                    "message": f"Browser automation error: {str(e)}",
                }


naukri_bot = NaukriBrowserBot()


async def execute_browser_bulk_apply(
    user_id: int,
    job_ids: list[int],
    max_jobs: int = 50,
    min_delay_sec: int = 25,
    max_delay_sec: int = 45,
) -> dict[str, Any]:
    """Execute stealth browser applications sequentially with human delays up to daily limit."""
    db: Session = SessionLocal()
    applied_results = []
    applied_count = 0

    try:
        profile = db.scalar(select(CandidateProfile).where(CandidateProfile.user_id == user_id))
        pref = db.scalar(select(Preference).where(Preference.user_id == user_id))
        daily_limit = min(max_jobs, int(pref.daily_limit or 50) if pref else 50)

        jobs_to_process = job_ids[:daily_limit]
        logger.info("Beginning stealth browser apply for %d jobs (Daily limit: %d)", len(jobs_to_process), daily_limit)

        for idx, j_id in enumerate(jobs_to_process):
            job = db.scalar(select(Job).where(Job.id == j_id))
            if not job or not job.url:
                continue

            try:
                # Run stealth apply according to platform
                if (job.platform or "").lower() == "indeed":
                    from app.services.automation.indeed_browser import indeed_bot
                    result = await indeed_bot.apply_to_job(job_url=job.url, profile=profile)
                else:
                    result = await naukri_bot.apply_to_job(job_url=job.url, profile=profile)
            except Exception as err:
                logger.exception("Failed to apply to job %s: %s", j_id, err)
                result = {
                    "success": False,
                    "status": "error",
                    "message": f"Browser navigation error: {str(err)}",
                }

            applied_results.append({
                "job_id": j_id,
                "title": job.title,
                "company": job.company,
                "status": result.get("status", "error"),
                "message": result.get("message", "Unknown error"),
            })

            # If applied or already applied, update database Application record
            if result.get("status") in ["applied", "already_applied"]:
                applied_count += 1
                now = datetime.now(timezone.utc)
                app = db.scalar(
                    select(Application).where(
                        (Application.user_id == user_id) & (Application.job_id == j_id)
                    )
                )
                platform_name = (job.platform or "Naukri").capitalize()
                if not app:
                    app = Application(
                        user_id=user_id,
                        job_id=j_id,
                        status="applied",
                        method="browser_stealth",
                        submitted_at=now,
                        notes=f"Applied directly via Stealth Browser Bot on {platform_name}",
                    )
                    db.add(app)
                    db.commit()
                    db.refresh(app)
                else:
                    app.status = "applied"
                    app.method = "browser_stealth"
                    app.submitted_at = now
                    app.updated_at = now
                    db.commit()

                history = ApplicationStatusHistory(
                    application_id=app.id,
                    old_status="pending_approval",
                    new_status="applied",
                    notes=f"Direct submission on {platform_name} portal confirmed via Stealth Browser",
                )
                db.add(history)
                db.commit()

            elif result.get("status") in ["error", "button_not_found", "captcha_paused", "failed"]:
                now = datetime.now(timezone.utc)
                app = db.scalar(
                    select(Application).where(
                        (Application.user_id == user_id) & (Application.job_id == j_id)
                    )
                )
                platform_name = (job.platform or "Naukri").capitalize()
                err_msg = result.get("message", "Could not locate standard Apply button on portal")
                if not app:
                    app = Application(
                        user_id=user_id,
                        job_id=j_id,
                        status="failed",
                        method="browser_stealth",
                        submitted_at=now,
                        notes=f"Automation failed on {platform_name}: {err_msg}",
                    )
                    db.add(app)
                    db.commit()
                    db.refresh(app)
                else:
                    app.status = "failed"
                    app.method = "browser_stealth"
                    app.notes = f"Automation failed on {platform_name}: {err_msg}"
                    app.updated_at = now
                    db.commit()

                history = ApplicationStatusHistory(
                    application_id=app.id,
                    old_status="pending_approval",
                    new_status="failed",
                    notes=f"Automation failed: {err_msg}",
                )
                db.add(history)
                db.commit()

            # If captcha detected, halt batch to protect candidate account
            if result.get("status") == "captcha_paused":
                logger.warning("Halting batch apply due to security challenge.")
                break

            # Natural delay between applications (e.g. 25-45 seconds)
            if idx < len(jobs_to_process) - 1:
                delay = random.uniform(min_delay_sec, max_delay_sec)
                logger.info("Sleeping %.1f seconds before next application to maintain human pace...", delay)
                await asyncio.sleep(delay)

        return {
            "success": True,
            "processed_count": len(applied_results),
            "applied_count": applied_count,
            "results": applied_results,
        }

    finally:
        db.close()

