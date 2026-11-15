"""Playwright-based Stealth Browser Automation Engine for Indeed.com.

Features:
- Dedicated local persistent browser profile for Indeed (login once, cookies saved).
- Stealth flags & human-like viewport / user-agent.
- Safe detection of "Apply now", "Easily apply", already-applied state, and company redirects.
- Human-like scrolling, delay jitter, and polite rate limiting.
"""

import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
import random
from typing import Any

try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Page = Any  # type: ignore
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.models import (
    Application,
    ApplicationStatusHistory,
    CandidateProfile,
    Job,
    Preference,
)

logger = logging.getLogger(__name__)

def resolve_indeed_profile_dir() -> Path:
    try:
        root_p = Path(__file__).resolve().parents[4] / "browser_profile" / "indeed_stealth"
        if root_p.exists():
            return root_p
    except IndexError:
        pass
    try:
        backend_p = Path(__file__).resolve().parents[3] / "browser_profile" / "indeed_stealth"
        if backend_p.exists():
            return backend_p
    except IndexError:
        pass
    p = Path(__file__).resolve().parent.parent.parent.parent / "browser_profile" / "indeed_stealth"
    p.mkdir(parents=True, exist_ok=True)
    return p

INDEED_PROFILE_DIR = resolve_indeed_profile_dir()

STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--test-type",
    "--window-size=1280,850",
]


class IndeedBrowserBot:
    """Stealth browser automation manager for Indeed candidate applications."""

    def __init__(self):
        self.profile_dir = str(INDEED_PROFILE_DIR)

    async def open_login_window(self) -> dict[str, Any]:
        """Launch a visible Chromium window for the user to log in to Indeed once."""
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                channel="chromium",
                args=STEALTH_ARGS,
                viewport={"width": 1280, "height": 850},
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

            await page.goto("https://secure.indeed.com/auth", wait_until="domcontentloaded")
            logger.info("Opened Indeed login page for candidate.")

            # Wait up to 3 minutes for candidate to log in
            logged_in = False
            for _ in range(36):
                await asyncio.sleep(5)
                current_url = page.url
                # Once authenticated, redirected to indeed.com home, profile, or account
                if "auth" not in current_url and any(x in current_url for x in ["indeed.com", "myjobs", "profile"]):
                    logged_in = True
                    break

            cookies = await context.cookies()
            await context.close()
            return {
                "success": True,
                "logged_in": logged_in,
                "message": (
                    "Indeed session saved successfully! You are logged in."
                    if logged_in
                    else "Window closed. You can reopen to complete login anytime."
                ),
                "cookies_count": len(cookies),
            }

    async def check_session_status(self) -> dict[str, Any]:
        """Check if persistent browser session has active Indeed cookies."""
        has_profile = any(INDEED_PROFILE_DIR.iterdir()) if INDEED_PROFILE_DIR.exists() else False

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
                await page.goto("https://in.indeed.com/myjobs", timeout=15000, wait_until="domcontentloaded")
                is_logged_in = "auth" not in page.url and "login" not in page.url and "indeed.com" in page.url
                await context.close()
                return {
                    "logged_in": is_logged_in,
                    "status": "active" if is_logged_in else "session_expired",
                }
        except Exception as e:
            logger.warning("Error checking Indeed session: %s", e)
            return {"logged_in": False, "status": "error", "detail": str(e)}

    async def _human_scroll(self, page: Page):
        """Natural mouse scroll simulation."""
        try:
            for _ in range(random.randint(2, 4)):
                scroll_y = random.randint(200, 500)
                await page.mouse.wheel(0, scroll_y)
                await asyncio.sleep(random.uniform(0.7, 1.5))
            await asyncio.sleep(random.uniform(1.0, 2.0))
            await page.mouse.wheel(0, -random.randint(100, 250))
            await asyncio.sleep(random.uniform(0.5, 1.0))
        except Exception:
            pass

    async def apply_to_job(
        self,
        job_url: str,
        profile: CandidateProfile | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Safely navigate to Indeed job posting and execute apply."""
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
                                'Where-Object { $_.CommandLine -match "indeed_stealth" } | '
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
                logger.info("Navigating to Indeed job: %s", job_url)
                await page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(2.5, 4.0))

                # Check if landed page is a search result listing; resolve directly to matching job posting
                if "/jobs?q=" in page.url or "jobs?" in page.url:
                    job_link = page.locator("a.jcs-JobTitle, h2.jobTitle a, div.job_seen_beacon a[data-jk]").first
                    if await job_link.is_visible():
                        try:
                            await job_link.click()
                            await asyncio.sleep(2.0)
                        except Exception:
                            href = await job_link.get_attribute("href")
                            if href:
                                if not href.startswith("http"):
                                    href = f"https://in.indeed.com{href}"
                                logger.info("Resolving Indeed search to live job detail page: %s", href)
                                await page.goto(href, timeout=30000, wait_until="domcontentloaded")
                        await asyncio.sleep(random.uniform(1.5, 2.5))

                # Human-like scrolling
                await self._human_scroll(page)

                # Check if already applied
                already_applied = page.locator("text=Already applied, text=Applied on Indeed, .already-applied-status")
                if await already_applied.first.is_visible():
                    logger.info("Job already applied on Indeed: %s", job_url)
                    await context.close()
                    return {
                        "success": True,
                        "status": "already_applied",
                        "message": "Already applied previously on Indeed portal.",
                    }

                # Check if external redirect in job pane
                company_apply = page.locator(
                    "div#jobsearch-ViewjobPaneWrapper a:has-text('Apply on company site'), "
                    "div#jobsearch-ViewjobPaneWrapper button:has-text('Apply on company site'), "
                    "a:has-text('Apply on company site'), button:has-text('Apply on company site')"
                )
                if await company_apply.first.is_visible():
                    logger.info("Indeed job requires company site redirect: %s", job_url)
                    await context.close()
                    return {
                        "success": False,
                        "status": "company_site_redirect",
                        "message": "Requires application on employer portal. Link saved in Tracker.",
                    }

                # Find 1-Click direct Indeed Apply button (STRICT to job pane, NEVER filter pills)
                apply_btn = page.locator(
                    "div#jobsearch-ViewjobPaneWrapper button#indeedApplyButton, "
                    "div#jobsearch-ViewjobPaneWrapper button[id*='indeedApply'], "
                    "div#indeedApplyButton button, "
                    "div#indeedApplyButton, "
                    "span.indeed-apply-widget button, "
                    "button#indeedApplyButton, "
                    "div#jobsearch-ViewjobPaneWrapper button:has-text('Apply now')"
                ).first

                if not await apply_btn.is_visible():
                    pane_btn = page.locator("div#jobsearch-ViewjobPaneWrapper button:has-text('Apply')").first
                    if await pane_btn.is_visible():
                        apply_btn = pane_btn

                if await apply_btn.is_visible():
                    if dry_run:
                        await context.close()
                        return {
                            "success": True,
                            "status": "dry_run_ready",
                            "message": "Indeed Apply button found and ready.",
                        }

                    box = await apply_btn.bounding_box()
                    if box:
                        await page.mouse.click(
                            box["x"] + box["width"] / 2 + random.uniform(-4, 4),
                            box["y"] + box["height"] / 2 + random.uniform(-3, 3),
                        )
                    else:
                        await apply_btn.click()

                    logger.info("Clicked Apply button on Indeed. Checking modal steps...")
                    await asyncio.sleep(random.uniform(3.0, 5.0))

                    # Indeed Apply often has 1 to 3 "Continue" steps or "Submit your application"
                    for step in range(4):
                        submit_btn = page.locator(
                            "button:has-text('Submit your application'), button:has-text('Submit application'), button:has-text('Review your application')"
                        ).first
                        continue_btn = page.locator(
                            "button:has-text('Continue'), button:has-text('Next')"
                        ).first

                        if await submit_btn.is_visible():
                            await submit_btn.click()
                            await asyncio.sleep(3.0)
                            break
                        elif await continue_btn.is_visible():
                            await continue_btn.click()
                            await asyncio.sleep(random.uniform(2.0, 3.5))
                        else:
                            break

                    await asyncio.sleep(random.uniform(2.0, 3.5))
                    await context.close()
                    return {
                        "success": True,
                        "status": "applied",
                        "message": "Successfully submitted application directly on Indeed.com!",
                    }

                await context.close()
                return {
                    "success": False,
                    "status": "button_not_found",
                    "message": "Could not locate standard Apply button on this Indeed posting.",
                }

            except Exception as e:
                logger.exception("Error applying to Indeed job: %s", e)
                try:
                    await context.close()
                except Exception:
                    pass
                return {
                    "success": False,
                    "status": "error",
                    "message": f"Indeed browser automation error: {str(e)}",
                }


indeed_bot = IndeedBrowserBot()

