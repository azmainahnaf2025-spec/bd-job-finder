"""
Autonomous Agent Runtime Daemon for BD Job Finder.
Runs background workers to:
1. Process automated ATS Autopilot portal submissions and account registrations.
2. Monitor 4-day follow-up timelines and dispatch polite inquiry emails.
3. Continuously scan candidate Gmail inboxes via IMAP for interview invitations.
4. Keep the SQLite CRM tracker updated in real-time.

Usage:
    python -m core.agent_runtime --workers 2 --poll 3
    python -m core.agent_runtime --workers 4 --poll 5 --dry-run
"""

import os
import sys
import time
import signal
import argparse
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.database import (
    get_active_profile,
    get_profile_by_id,
    get_applications,
    update_application_status,
    get_due_followups,
    mark_followed_up,
    record_interview_chance,
    get_application_stats,
    get_credentials
)
from core.email_dispatcher import (
    dispatch_application_email,
    dispatch_followup_email,
    scan_inbox_for_interview_invites,
    get_default_resume_path
)
from core.ai_engine import (
    generate_application_pitch,
    generate_followup_pitch
)
from core.site_dispatcher import launch_ats_autopilot_session

# Global shutdown flag
RUNNING = True

def signal_handler(sig, frame):
    global RUNNING
    print("\n\n[SHUTDOWN] Intercepted stop signal (Ctrl+C). Terminating workers gracefully...")
    RUNNING = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def log(tag: str, msg: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [{tag}] {msg}")

def process_queued_ats_job(job_record: dict, candidate_profile: dict, dry_run: bool = False):
    """Worker task: Dispatches autonomous ATS agent to apply on an employer portal."""
    app_id = job_record.get("id")
    company = job_record.get("company", "Employer")
    title = job_record.get("job_title", "Role")
    portal_url = job_record.get("apply_url") or job_record.get("portal_url") or ""

    if not portal_url:
        log("ATS-WORKER", f"Skipping #{app_id} ({company}): No portal URL provided.")
        return

    log("ATS-WORKER", f"Dispatching Autonomous ATS Agent to #{app_id} for '{title}' at '{company}'...")
    resume_path = get_default_resume_path(candidate_profile)
    cand_locs = candidate_profile.get("preferred_locations", [])
    cand_addr = cand_locs[0] if cand_locs else "Dhaka, Bangladesh"

    if dry_run:
        log("DRY-RUN", f"Simulated ATS application on {portal_url}. Candidate CV: {os.path.basename(resume_path) if resume_path else 'None'}")
        return

    try:
        res = launch_ats_autopilot_session(
            portal_url=portal_url,
            candidate_name=candidate_profile.get("full_name", "Candidate"),
            candidate_email=candidate_profile.get("email", ""),
            candidate_phone=candidate_profile.get("phone", ""),
            candidate_address=cand_addr,
            candidate_linkedin=candidate_profile.get("linkedin", ""),
            job_title=title,
            company=company,
            resume_path=resume_path,
            candidate_profile=candidate_profile,
            headless=True
        )
        if res.get("success"):
            new_notes = f"Autonomous ATS Agent submitted on {portal_url}. {res.get('message', '')}"
            update_application_status(app_id, "Applied via ATS Autopilot", notes=new_notes)
            log("ATS-SUCCESS", f"Successfully applied to '{company}'! Proof screenshot: {res.get('screenshot')}")
        else:
            log("ATS-NOTICE", f"ATS session completed with notice for '{company}': {res.get('message')}")
    except Exception as err:
        log("ATS-ERROR", f"Failed applying to '{company}': {err}")

def process_due_followup(app_record: dict, candidate_profile: dict, creds: dict, dry_run: bool = False):
    """Worker task: Dispatches a 4-day polite follow-up email to recruiter."""
    app_id = app_record.get("id")
    company = app_record.get("company", "Employer")
    title = app_record.get("job_title", "Position")
    recip_email = app_record.get("hr_email")
    days_pending = app_record.get("days_pending", 4)

    if not recip_email:
        log("FOLLOWUP-SKIP", f"Skipping #{app_id} ({company}): No direct HR email on file.")
        return

    log("FOLLOWUP-WORKER", f"Application to '{company}' ({title}) is {days_pending} days old. Synthesizing follow-up pitch...")
    f_pitch = generate_followup_pitch(app_record, candidate_profile=candidate_profile)
    
    sender_em = creds.get("sender_email") or candidate_profile.get("email")
    app_pw = creds.get("app_password")

    if not app_pw and not dry_run:
        log("FOLLOWUP-SKIP", f"Skipping #{app_id}: Gmail 16-character App Password not set in settings.")
        return

    res = dispatch_followup_email(
        app_id=app_id,
        recipient_email=recip_email,
        subject=f_pitch.get("subject", f"Following up: {title} Application — {candidate_profile.get('full_name')}"),
        body=f_pitch.get("body", ""),
        sender_email=sender_em,
        app_password=app_pw,
        dry_run=dry_run
    )

    if res.get("success"):
        mark_followed_up(app_id, notes=f"Automated 4-day follow-up sent via runtime agent ({days_pending} days post-apply).")
        log("FOLLOWUP-SUCCESS", f"Follow-up delivered to '{recip_email}' for '{company}'!")
    else:
        log("FOLLOWUP-ERROR", f"Follow-up error for '{company}': {res.get('message')}")

def run_agent_runtime(workers: int = 2, poll_interval: float = 3.0, profile_id: int = None, dry_run: bool = False, run_once: bool = False):
    """Main daemon loop running worker threads and queue monitors."""
    global RUNNING
    
    # 1. Resolve Candidate Profile
    active_profile = get_profile_by_id(profile_id) if profile_id else get_active_profile()
    if not active_profile:
        print("[ERROR] No active candidate profile found in database. Please run the app to create a profile.")
        sys.exit(1)

    cand_name = active_profile.get("full_name", "Job Seeker")
    cand_email = active_profile.get("email", "Not Set")
    cand_phone = active_profile.get("phone", "Not Set")
    cand_resume = active_profile.get("resume_filename", "None")

    print("================================================================================")
    print("                 🇧🇩 BD JOB FINDER — AUTONOMOUS AGENT RUNTIME")
    print("================================================================================")
    print(f"👤 Candidate Name:       {cand_name}")
    print(f"📧 Candidate Gmail:      {cand_email}")
    print(f"📱 Candidate Phone:      {cand_phone}")
    print(f"📎 Attached CV Resume:   {cand_resume}")
    print(f"⚙️  Worker Pool:          {workers} Concurrent Background Threads")
    print(f"⏱️  Polling Interval:     {poll_interval} Seconds")
    print(f"🧪 Dry Run Mode:         {'ENABLED (Simulation Only)' if dry_run else 'DISABLED (Real Submissions & Emails)'}")
    print("================================================================================")
    print("[ONLINE] Agent Runtime active. Press Ctrl+C anytime to stop.\n")

    executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="BDJobWorker")
    
    poll_count = 0
    last_imap_scan_time = 0
    IMAP_SCAN_INTERVAL = 45  # Scan inbox every 45 seconds

    try:
        while RUNNING:
            poll_count += 1
            now_time = time.time()
            creds = get_credentials(active_profile.get("id"))

            # --- SUBTASK 1: CHECK 4-DAY FOLLOW-UPS ---
            due_followups = get_due_followups()
            if due_followups:
                log("DAEMON", f"Found {len(due_followups)} application(s) due for 4-day follow-up inquiry.")
                for df in due_followups[:workers]:
                    executor.submit(process_due_followup, df, active_profile, creds, dry_run)

            # --- SUBTASK 2: CHECK QUEUED / PENDING ATS SUBMISSIONS ---
            queued_apps = get_applications(status="Queued") + get_applications(status="Auto-Apply")
            if queued_apps:
                log("DAEMON", f"Found {len(queued_apps)} application(s) in ATS Autopilot queue.")
                for q_job in queued_apps[:workers]:
                    executor.submit(process_queued_ats_job, q_job, active_profile, dry_run)

            # --- SUBTASK 3: IMAP RECRUITER & INTERVIEW SCANNER ---
            if (now_time - last_imap_scan_time) >= IMAP_SCAN_INTERVAL and creds.get("app_password") and creds.get("sender_email"):
                last_imap_scan_time = now_time
                def _scan_task():
                    try:
                        scan_res = scan_inbox_for_interview_invites(
                            sender_email=creds.get("sender_email"),
                            app_password=creds.get("app_password"),
                            days_back=14
                        )
                        found_interviews = scan_res.get("interviews", [])
                        if found_interviews:
                            log("INTERVIEW-SCAN", f"🎉 Detected {len(found_interviews)} interview invitation email(s) in inbox!")
                            for inv in found_interviews:
                                log("INTERVIEW-OPPORTUNITY", f"Candidate: {cand_name} | Company: {inv.get('company')} | Subject: {inv.get('subject')}")
                    except Exception as err:
                        log("IMAP-NOTICE", f"Inbox scan notice: {err}")

                executor.submit(_scan_task)

            # --- HEARTBEAT REPORT (Every 10 polls) ---
            if poll_count % 10 == 1:
                stats = get_application_stats()
                log("HEARTBEAT", f"CRM Total: {stats['Total']} | Applied: {stats['Applied']} | Followed Up: {stats['Followed Up']} | Interviews: {stats['Interviews']} | Due Follow-ups: {len(due_followups)}")

            if run_once:
                log("DAEMON", "--once specified. Cycle complete. Exiting...")
                break

            # Sleep in small increments for responsive Ctrl+C handling
            sleep_chunks = max(1, int(poll_interval / 0.2))
            for _ in range(sleep_chunks):
                if not RUNNING:
                    break
                time.sleep(poll_interval / sleep_chunks)

    finally:
        print("\n[DAEMON] Shutting down thread pool executor...")
        executor.shutdown(wait=False)
        print("[SUCCESS] Autonomous Agent Runtime safely stopped.")

def main():
    parser = argparse.ArgumentParser(description="BD Job Finder - Autonomous Background Agent Runtime")
    parser.add_argument("--workers", type=int, default=2, help="Number of concurrent worker threads (default: 2)")
    parser.add_argument("--poll", type=float, default=3.0, help="Polling interval in seconds (default: 3.0)")
    parser.add_argument("--profile-id", type=int, default=None, help="Candidate profile ID to run for (default: active profile)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate submissions and emails without sending")
    parser.add_argument("--once", action="store_true", help="Run a single polling cycle and terminate")

    args = parser.parse_args()
    run_agent_runtime(
        workers=args.workers,
        poll_interval=args.poll,
        profile_id=args.profile_id,
        dry_run=args.dry_run,
        run_once=args.once
    )

if __name__ == "__main__":
    main()
