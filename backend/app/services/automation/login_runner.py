"""Standalone runner script to open a visible login browser window for Naukri or Indeed."""

import argparse
import asyncio
import logging
from pathlib import Path
import random
import re
import subprocess
import sys
import urllib.parse

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

LOG_FILE = Path(__file__).resolve().parents[4] / "browser_automation.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger("LoginRunner")


def resolve_profile_dir(platform: str) -> Path:
    p_name = f"{platform}_stealth"
    try:
        root_p = Path(__file__).resolve().parents[4] / "browser_profile" / p_name
        if root_p.exists():
            return root_p
    except IndexError:
        pass
    try:
        backend_p = Path(__file__).resolve().parents[3] / "browser_profile" / p_name
        if backend_p.exists():
            return backend_p
    except IndexError:
        pass
    root_p = Path(__file__).resolve().parent.parent.parent.parent / "browser_profile" / p_name
    root_p.mkdir(parents=True, exist_ok=True)
    return root_p


STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--test-type",
    "--window-size=1280,850",
    "--no-default-browser-check",
    "--no-first-run",
]


async def inject_banner(page, text: str, bg_color: str = "#4338ca"):
    """Log automation progress cleanly without injecting any visual banners/borders into the page."""
    logger.info("[Portal Status] %s", text)


def kill_profile_lock(profile_name: str):
    """Force release any zombie chromium or edge process holding this profile folder."""
    if sys.platform != "win32":
        return
    try:
        cmd = (
            f'Get-CimInstance Win32_Process | '
            f'Where-Object {{ $_.CommandLine -match "{profile_name}" }} | '
            f'ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}'
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=5)
    except Exception as e:
        logger.warning("Could not kill profile lock: %s", e)


def record_portal_status(job_url: str, new_status: str, notes: str):
    """Update SQLite application record based on verified portal execution outcome."""
    try:
        candidate_paths = [
            Path(__file__).resolve().parents[3] / "job_automation.db",
            Path(__file__).resolve().parents[4] / "backend" / "job_automation.db",
            Path(__file__).resolve().parents[2] / "job_automation.db",
        ]
        db_path = next((p for p in candidate_paths if p.exists()), None)
        if db_path:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                "UPDATE applications SET status = ?, submitted_at = CURRENT_TIMESTAMP, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id IN (SELECT id FROM jobs WHERE url = ? OR url LIKE ?)",
                (new_status, notes, job_url, f"%{job_url}%"),
            )
            conn.commit()
            conn.close()
            logger.info("Updated application status to '%s' in database: %s", new_status, notes)
    except Exception as e:
        logger.warning("Could not update application status in DB: %s", e)


async def launch_login(
    platform: str = "naukri",
    target_url: str | None = None,
    auto_apply: bool = False,
    company: str | None = None,
    job_title: str | None = None,
):
    platform = platform.lower().strip()
    if platform == "indeed":
        profile_dir = resolve_profile_dir("indeed")
        default_url = "https://in.indeed.com/"
        title = "Indeed Portal"
    else:
        profile_dir = resolve_profile_dir("naukri")
        default_url = "https://www.naukri.com/nlogin/login"
        title = "Naukri Portal"

    dest_url = target_url.strip() if target_url else default_url
    profile_dir.mkdir(parents=True, exist_ok=True)
    is_company_site = False

    # Remove stale lock files if any
    for lock_name in ["SingletonLock", "lockfile", "SingletonCookie", "SingletonSocket"]:
        lf = profile_dir / lock_name
        if lf.exists():
            try:
                lf.unlink(missing_ok=True)
            except Exception:
                pass

    logger.info("Launching %s in persistent profile (%s) navigating to: %s", title, profile_dir, dest_url)

    async with async_playwright() as p:
        browser_kwargs = {
            "user_data_dir": str(profile_dir),
            "headless": False,
            "args": STEALTH_ARGS,
            "ignore_default_args": ["--enable-automation", "--no-sandbox", "--disable-setuid-sandbox"],
            "viewport": {"width": 1280, "height": 850},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        }

        context = None
        for ch in ["msedge", "chrome", None]:
            try:
                if ch:
                    context = await p.chromium.launch_persistent_context(**browser_kwargs, channel=ch)
                else:
                    context = await p.chromium.launch_persistent_context(**browser_kwargs)
                logger.info("Launched browser using channel: %s", ch or "chromium default")
                break
            except Exception as launch_err:
                err_str = str(launch_err)
                logger.warning("Could not launch channel %s: %s. Checking profile lock...", ch, launch_err)
                if "Opening in existing browser session" in err_str or "already in use" in err_str:
                    logger.info("Profile directory %s is locked. Clearing stale instances...", profile_dir.name)
                    kill_profile_lock(profile_dir.name)
                    await asyncio.sleep(1.2)
                    try:
                        if ch:
                            context = await p.chromium.launch_persistent_context(**browser_kwargs, channel=ch)
                        else:
                            context = await p.chromium.launch_persistent_context(**browser_kwargs)
                        logger.info("Successfully launched browser after unlocking profile with channel: %s", ch or "chromium default")
                        break
                    except Exception as retry_err:
                        logger.warning("Retry launch failed for channel %s: %s", ch, retry_err)

        if not context:
            logger.error("Failed to launch any browser context.")
            return

        page = context.pages[0] if context.pages else await context.new_page()

        # Listen for any new popups or tabs created (e.g. clicking a job from list)
        active_tabs = [page]

        def on_page_event(new_p):
            active_tabs.append(new_p)
            logger.info("New tab opened: %s", new_p.url)

        context.on("page", on_page_event)

        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.navigator.chrome = { runtime: {} };
            """
        )

        logger.info("Navigating to %s...", dest_url)
        try:
            await page.goto(dest_url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            logger.warning("Initial navigation note: %s", e)
        await asyncio.sleep(2.0)

        # 1. Resolve to specific job detail post if on a listing page
        if platform == "naukri":
            # If on a company jobs page or search results list, click into job post
            if "-jobs" in page.url or "/jobs" in page.url:
                logger.info("Landed on Naukri listings page. Resolving to specific job detail card...")
                await asyncio.sleep(2.0)

                # Find job card matching role or title
                target_link = None
                card_candidates = [
                    f"div.srp-jobtuple-wrapper:has-text('{job_title}') a.title" if job_title else None,
                    f"div.cust-job-tuple:has-text('{job_title}') a.title" if job_title else None,
                    f"div.srp-jobtuple-wrapper:has-text('{company}') a.title" if company else None,
                    f"div.cust-job-tuple:has-text('{company}') a.title" if company else None,
                    "div.srp-jobtuple-wrapper a.title",
                    "div.cust-job-tuple a.title",
                    "article.jobTuple a.title",
                    "a.title",
                ]
                for cand in card_candidates:
                    if not cand:
                        continue
                    loc = page.locator(cand).first
                    if await loc.is_visible():
                        target_link = loc
                        logger.info("Matched job link via locator: %s", cand)
                        break

                if target_link:
                    try:
                        async with context.expect_page(timeout=6000) as new_page_info:
                            await target_link.click()
                        new_page = await new_page_info.value
                        await new_page.wait_for_load_state("domcontentloaded")
                        page = new_page
                        logger.info("Switched active view to opened job detail tab: %s", page.url)
                    except Exception:
                        href = await target_link.get_attribute("href")
                        if href:
                            if not href.startswith("http"):
                                href = f"https://www.naukri.com{href}"
                            logger.info("Navigating directly to job detail URL: %s", href)
                            await page.goto(href, timeout=30000, wait_until="domcontentloaded")
                    await asyncio.sleep(2.0)

        elif platform == "indeed":
            if "/jobs?q=" in page.url or "jobs?" in page.url:
                logger.info("Landed on Indeed listings page. Locating job card in left pane...")
                await asyncio.sleep(2.0)

                indeed_cards = [
                    f"div.job_seen_beacon:has-text('{company}') a.jcs-JobTitle" if company else None,
                    f"div.job_seen_beacon:has-text('{company}')" if company else None,
                    "a.jcs-JobTitle",
                    "h2.jobTitle a",
                    "div.job_seen_beacon",
                ]
                for ind_sel in indeed_cards:
                    if not ind_sel:
                        continue
                    candidate = page.locator(ind_sel).first
                    if await candidate.is_visible():
                        try:
                            await candidate.click()
                            logger.info("Clicked job card in Indeed list: %s", ind_sel)
                            await asyncio.sleep(2.5)
                            break
                        except Exception as ce:
                            logger.warning("Error clicking Indeed card %s: %s", ind_sel, ce)

        # 2. Check if logged in
        is_logged_in = True
        if platform == "naukri":
            login_prompt = page.locator("a[href*='nlogin'], button:has-text('Login'), .login-btn")
            if await login_prompt.first.is_visible() or "login" in page.url:
                is_logged_in = False
                logger.warning("Action Required: Please log in to your Naukri account in this window.")
        elif platform == "indeed":
            login_prompt = page.locator("a[href*='account/login'], a:has-text('Sign in')")
            if await login_prompt.first.is_visible() or "auth" in page.url:
                is_logged_in = False
                logger.warning("Action Required: Please sign in to your Indeed account in this window.")

        # 3. If auto_apply requested, execute application submission
        if auto_apply and is_logged_in:
            logger.info("Starting automatic 1-Click apply inspection...")
            await asyncio.sleep(2.0)

            # Check if already applied
            already_applied = False
            for sel in ["text=Already Applied", "text=Applied", ".already-applied", "button:has-text('Already Applied')", "text=Applied on Indeed"]:
                if await page.locator(sel).first.is_visible():
                    already_applied = True
                    break

            if already_applied:
                logger.info("Already applied previously to this position.")
                await asyncio.sleep(3.0)
            else:
                apply_btn = None
                is_company_site = False

                for _ in range(12):  # poll up to 6 seconds
                    # A. Check for external company portal apply FIRST
                    company_locators = [
                        "div#jobsearch-ViewjobPaneWrapper a:has-text('Apply on company site')",
                        "div#jobsearch-ViewjobPaneWrapper button:has-text('Apply on company site')",
                        "button:has-text('Apply on company site')",
                        "a:has-text('Apply on company site')",
                        "button:has-text('Company Site')",
                        "a:has-text('Company Site')",
                    ]
                    for sel in company_locators:
                        candidate = page.locator(sel).first
                        if await candidate.is_visible():
                            apply_btn = candidate
                            is_company_site = True
                            break
                    if is_company_site:
                        break

                    # B. Check for official direct 1-click apply button (STRICT selectors, never match filter pills)
                    if platform == "indeed":
                        direct_locators = [
                            "div#jobsearch-ViewjobPaneWrapper button#indeedApplyButton",
                            "div#jobsearch-ViewjobPaneWrapper button[id*='indeedApply']",
                            "div#indeedApplyButton button",
                            "div#indeedApplyButton",
                            "span.indeed-apply-widget button",
                            "button#indeedApplyButton",
                            "div#jobsearch-ViewjobPaneWrapper button:has-text('Apply now')",
                        ]
                    else:
                        direct_locators = [
                            "button#apply-button",
                            "button.apply-button",
                            "button:has-text('Apply on Naukri')",
                            "div.apply-button-container button",
                            ".apply-button-wrap button",
                            "button:has-text('Apply'):not(:has-text('Company'))",
                        ]

                    for sel in direct_locators:
                        candidate = page.locator(sel).first
                        if await candidate.is_visible():
                            apply_btn = candidate
                            break
                    if apply_btn:
                        break

                    await asyncio.sleep(0.5)

                if is_company_site:
                    logger.info("This position requires application on employer portal. Opening link for user to complete manually...")
                    record_portal_status(dest_url, "company_portal", f"Redirected to employer career portal ({title}) for manual submission")
                    if apply_btn:
                        try:
                            await apply_btn.click()
                            logger.info("Opened employer portal for manual completion as requested.")
                        except Exception as ce:
                            logger.warning("Could not auto-click company portal button: %s", ce)
                    await asyncio.sleep(5.0)

                elif apply_btn and await apply_btn.is_visible():
                    btn_text = (await apply_btn.inner_text() or "").strip()
                    logger.info("Found direct 1-click apply button: '%s'. Executing automatic submission...", btn_text)
                    await asyncio.sleep(1.0)

                    try:
                        box = await apply_btn.bounding_box()
                        if box:
                            await page.mouse.click(
                                box["x"] + box["width"] / 2 + random.uniform(-4, 4),
                                box["y"] + box["height"] / 2 + random.uniform(-2, 2),
                            )
                        else:
                            await apply_btn.click()

                        logger.info("Clicked direct Apply button. Processing any screening modals...")
                        await asyncio.sleep(2.5)

                        # Handle Naukri questionnaire drawer or modal if present
                        drawer = page.locator(".chatbot_Drawer, .apply-drawer, .custom-questions, .drawer-wrapper, div[role='dialog']")
                        if await drawer.first.is_visible():
                            notice_input = page.locator("input[placeholder*='Notice'], input[name*='notice']")
                            if await notice_input.first.is_visible():
                                await notice_input.first.fill("30")

                            submit_btn = page.locator(
                                "button:has-text('Save & Apply'), button:has-text('Submit'), button:has-text('Apply Now'), button:has-text('Continue')"
                            ).first
                            if await submit_btn.is_visible():
                                await submit_btn.click()
                                await asyncio.sleep(2.0)

                        # Handle Indeed multi-step modals if present
                        if platform == "indeed":
                            for _ in range(4):
                                submit_modal_btn = page.locator(
                                    "button:has-text('Submit your application'), button:has-text('Submit application'), button:has-text('Review your application')"
                                ).first
                                continue_modal_btn = page.locator(
                                    "button:has-text('Continue'), button:has-text('Next')"
                                ).first

                                if await submit_modal_btn.is_visible():
                                    await submit_modal_btn.click()
                                    await asyncio.sleep(2.5)
                                    break
                                elif await continue_modal_btn.is_visible():
                                    await continue_modal_btn.click()
                                    await asyncio.sleep(2.0)
                                else:
                                    break

                        logger.info("Application officially confirmed on %s portal!", title)
                        record_portal_status(dest_url, "applied", f"Confirmed submitted directly on official {title} portal")
                        await asyncio.sleep(6.0)
                    except Exception as apply_err:
                        logger.warning("Error clicking direct apply button: %s", apply_err)
                        record_portal_status(dest_url, "failed", f"Failed to submit on {title}: {str(apply_err)}")
                else:
                    logger.info("Could not locate direct apply button on this posting.")
                    record_portal_status(dest_url, "failed", f"Could not locate 1-Click Apply button on {title} posting")

        # Keep browser open appropriately:
        # If redirected to employer company website or manual mode, keep window open until candidate finishes!
        if is_company_site or not auto_apply:
            logger.info("Company portal / manual login active: Keeping browser open until candidate finishes and closes the window (up to 45 minutes)...")
            for _ in range(1350):  # up to 45 minutes of manual completion time
                await asyncio.sleep(2)
                try:
                    open_pages = [p for p in context.pages if not p.is_closed()]
                    if not open_pages:
                        logger.info("Candidate completed and closed the browser window.")
                        break
                except Exception:
                    break
        else:
            # For 1-click auto-apply, keep open for candidate confirmation review
            logger.info("Direct auto-apply completed. Keeping window open for review...")
            for _ in range(45):
                await asyncio.sleep(1)
                try:
                    open_pages = [p for p in context.pages if not p.is_closed()]
                    if not open_pages:
                        break
                except Exception:
                    break

        try:
            await context.close()
        except Exception:
            pass
        logger.info("%s session successfully saved and unlocked.", title)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", default="naukri", help="naukri or indeed")
    parser.add_argument("--url", default=None, help="Target job URL to open directly in authenticated profile")
    parser.add_argument("--auto-apply", action="store_true", help="Automatically click apply and submit on portal")
    parser.add_argument("--company", default=None, help="Target company name")
    parser.add_argument("--job-title", default=None, help="Target job title")
    args = parser.parse_args()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(
        launch_login(
            platform=args.platform,
            target_url=args.url,
            auto_apply=args.auto_apply,
            company=args.company,
            job_title=args.job_title,
        )
    )
