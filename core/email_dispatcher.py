"""
Email Dispatcher for BD Job Finder.
Automates 1-click job application submission via Gmail SMTP with tailored pitch,
pre-flight deliverability checks, and candidate resume PDF attached.
"""

import os
import re
import socket
import smtplib
import imaplib
import email
from email.header import Header, decode_header
from datetime import datetime, timedelta
import base64
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from .database import (
    get_credentials,
    update_application_status,
    check_duplicate_application,
    get_due_followups,
    mark_followed_up,
    get_applications,
    get_active_profile
)

RESUMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "resumes")
os.makedirs(RESUMES_DIR, exist_ok=True)

# Known dead / bounce mailboxes to prevent mail routing loops & Google Mailer-Daemon bounces
BOUNCED_OR_DEAD_EMAILS = {
    "fake@example.com", "career@example.com", "jobs@example.com",
    "info@example.com", "no-reply@example.com", "talent@pathao.com",
    "hr@pathao.com", "career@pathao.com", "jobs@pathao.com"
}

RECIPIENT_REDIRECTS = {
    "career@shwapno.com": "career@acilogistics.net",
    "jobs@shwapno.com": "career@acilogistics.net"
}

def get_default_resume_path(profile: dict = None) -> str | None:
    """
    Finds the active resume PDF strictly tied to the candidate profile.
    PRIORITY 1: The exact CV filename designated in candidate profile ['resume_filename'].
    PRIORITY 2: Search for a PDF matching the candidate's name tokens in RESUMES_DIR.
    PRIORITY 3: The most recently modified PDF in RESUMES_DIR as fallback.
    """
    from .database import get_active_profile
    prof = profile or get_active_profile() or {}

    # 1. Check user profile's designated uploaded CV
    if prof.get("resume_filename"):
        candidate_p = os.path.join(RESUMES_DIR, os.path.basename(prof["resume_filename"]))
        if os.path.exists(candidate_p):
            return candidate_p

    # 2. Match by candidate name tokens in RESUMES_DIR
    full_name = prof.get("full_name", "").strip()
    if full_name and full_name.lower() != "job seeker" and os.path.exists(RESUMES_DIR):
        tokens = [t.lower() for t in re.split(r"[\s_.-]+", full_name) if len(t) >= 3]
        if tokens:
            for f in os.listdir(RESUMES_DIR):
                if f.lower().endswith(".pdf"):
                    f_lower = f.lower()
                    if any(tok in f_lower for tok in tokens):
                        matched_p = os.path.join(RESUMES_DIR, f)
                        if os.path.exists(matched_p):
                            return matched_p

    # 3. Fallback to newest PDF in directory if candidate has no specific match
    if os.path.exists(RESUMES_DIR):
        pdf_files = [
            os.path.join(RESUMES_DIR, f) 
            for f in os.listdir(RESUMES_DIR) 
            if f.lower().endswith(".pdf")
        ]
        if pdf_files:
            pdf_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return pdf_files[0]

    return None

def save_uploaded_resume(file_bytes: bytes, filename: str, profile_id: int = None) -> str:
    """Saves candidate uploaded resume into local storage and associates it with profile."""
    from .database import set_active_resume_filename
    safe_name = os.path.basename(filename)
    dest = os.path.join(RESUMES_DIR, safe_name)
    with open(dest, "wb") as f:
        f.write(file_bytes)
    try:
        set_active_resume_filename(safe_name, profile_id=profile_id)
    except Exception:
        pass
    return dest

def list_available_resumes() -> list[dict]:
    """Returns a list of all stored resumes, sorted newest first, with active status."""
    active_path = get_default_resume_path()
    results = []
    if os.path.exists(RESUMES_DIR):
        files = [f for f in os.listdir(RESUMES_DIR) if f.lower().endswith(".pdf")]
        # Sort by modification time descending
        files.sort(key=lambda f: os.path.getmtime(os.path.join(RESUMES_DIR, f)), reverse=True)
        for f in files:
            full_p = os.path.join(RESUMES_DIR, f)
            size_kb = round(os.path.getsize(full_p) / 1024, 1)
            results.append({
                "filename": f,
                "path": full_p,
                "size_kb": size_kb,
                "is_active": (active_path is not None and os.path.normpath(full_p) == os.path.normpath(active_path))
            })
    return results

def get_pdf_base64(filepath: str) -> str | None:
    """Encodes PDF into base64 for in-browser iframe rendering."""
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None
    return None

def verify_domain_accepts_mail(domain_or_email: str) -> tuple[bool, str]:
    """Pre-flight DNS deliverability and domain syntax check."""
    clean = (domain_or_email or "").strip().lower()
    if "@" in clean:
        domain = clean.split("@")[-1].strip()
    else:
        domain = clean

    if not domain or "." not in domain:
        return False, f"Invalid domain name '{domain}'."

    try:
        socket.gethostbyname(domain)
        return True, "OK"
    except socket.gaierror:
        # perm failure on invalid host
        return False, f"Domain '{domain}' could not be resolved (NXDOMAIN)."
    except Exception as e:
        return True, f"Verification notice: {e}"

def generate_gmail_compose_url(to_email: str, subject: str, body: str) -> str:
    """
    Generates a 1-click direct link to open the logged-in user's Gmail in their browser
    with recipient, subject, and tailored application body pre-filled.
    """
    params = {
        "view": "cm",
        "fs": "1",
        "to": to_email,
        "su": subject,
        "body": body
    }
    return f"https://mail.google.com/mail/?{urllib.parse.urlencode(params)}"

def generate_mailto_url(to_email: str, subject: str, body: str) -> str:
    """
    Generates a mailto: link for default desktop email client (Outlook, Apple Mail).
    """
    params = {
        "subject": subject,
        "body": body
    }
    return f"mailto:{urllib.parse.quote(to_email)}?{urllib.parse.urlencode(params)}"

def authenticate_gmail_credentials(sender_email: str, app_password: str) -> tuple[bool, str]:
    """
    Connects to smtp.gmail.com:587 with STARTTLS and tests authentication
    using the provided candidate email and 16-character Google App Password.
    Returns: (is_authenticated: bool, status_message: str)
    """
    email_clean = (sender_email or "").strip()
    pw_clean = (app_password or "").replace(" ", "").strip()
    
    if not email_clean or "@" not in email_clean:
        return False, "Candidate email address is required (e.g. your_email@gmail.com)."
    if not pw_clean:
        return False, "Gmail 16-character App Password is required."
    if len(pw_clean) != 16:
        return False, f"App Password must be exactly 16 characters (currently {len(pw_clean)}). Please copy the exact 16-letter code from Google."

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=12)
        server.starttls()
        server.login(email_clean, pw_clean)
        server.quit()
        return True, f"Authentication successful! Connected to Google SMTP as '{email_clean}'."
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed (535 Bad Credentials). Please ensure 2-Step Verification is active on your Google account and generate a 16-character App Password at https://myaccount.google.com/apppasswords."
    except Exception as e:
        return False, f"SMTP Connection Notice: {str(e)}"

def dispatch_application_email(
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: str = None,
    sender_email: str = None,
    app_password: str = None,
    company: str = "",
    title: str = "",
    allow_duplicate: bool = False,
    dry_run: bool = False
) -> dict:
    """
    Sends a formal job application email via Gmail SMTP using the logged-in user's credentials
    with the candidate's resume attached and anti-duplicate guards.
    """
    recipient_email = (recipient_email or "").strip().strip("<>").strip()
    if not recipient_email or "@" not in recipient_email:
        return {"success": False, "message": "Invalid recipient email address."}

    clean_recipient = recipient_email.lower()
    if clean_recipient in RECIPIENT_REDIRECTS:
        clean_recipient = RECIPIENT_REDIRECTS[clean_recipient]
        recipient_email = clean_recipient

    if clean_recipient in BOUNCED_OR_DEAD_EMAILS:
        if "pathao" in clean_recipient:
            return {
                "success": False,
                "message": (
                    "🛑 Blocked: Pathao strictly accepts applications via its official Career Portal (https://careers.pathao.com). "
                    "Unsolicited emails to talent@pathao.com bounce (NoSuchUser). Please use 'Run ATS Form Autopilot' to submit directly on the portal."
                )
            }
        return {"success": False, "message": f"Blocked: '{clean_recipient}' is a known dead or bounce address."}

    # Strict Duplicate Dispatch Check
    if not allow_duplicate:
        is_dup, dup_msg, dup_date, dup_status = check_duplicate_application(
            company=company,
            title=title,
            email=clean_recipient
        )
        if is_dup:
            return {
                "success": False,
                "message": f"Duplicate dispatch blocked: {dup_msg} (Dispatched: {dup_date}, Status: {dup_status})"
            }

    # Deliverability Check
    is_deliv, deliv_reason = verify_domain_accepts_mail(clean_recipient)
    if not is_deliv:
        return {"success": False, "message": f"Deliverability check failed: {deliv_reason}"}

    creds = get_credentials()
    sender_email = (sender_email or creds.get("sender_email") or "").strip()
    app_password = (app_password or creds.get("app_password") or "").strip()

    if not sender_email:
        return {
            "success": False,
            "message": "User email address is missing. Please provide your email in your profile or login form."
        }

    if not app_password and not dry_run:
        return {
            "success": False,
            "message": "Gmail 16-character App Password not set for your account. Enter it in Settings/Apply Console, or click '🚀 Open in My Gmail (Pre-filled)' to send in 1 click from your browser!"
        }

    # If no specific attachment provided, use default
    if not attachment_path or not os.path.exists(attachment_path):
        attachment_path = get_default_resume_path()

    if dry_run:
        return {
            "success": True,
            "message": f"[DRY RUN] Application simulated to {recipient_email} with subject '{subject}'. Resume attached: {os.path.basename(attachment_path) if attachment_path else 'None'}."
        }

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Attach PDF Resume
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "pdf")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(attachment_path)}"'
            )
            msg.attach(part)

        # Connect to Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.starttls()
        server.login(sender_email, app_password.replace(" ", "").strip())
        server.send_message(msg)
        server.quit()

        return {
            "success": True,
            "message": f"Successfully dispatched application to {recipient_email} with resume '{os.path.basename(attachment_path) if attachment_path else 'CV'}' attached!"
        }
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "Gmail authentication failed! Verify your 16-character Google App Password in Settings."
        }
    except Exception as err:
        return {
            "success": False,
            "message": f"SMTP Dispatch Error: {str(err)}"
        }

def dispatch_followup_email(
    app_id: int,
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: str = None,
    sender_email: str = None,
    app_password: str = None,
    dry_run: bool = False
) -> dict:
    """
    Dispatches an automated or 1-click Day-4 follow-up email to the employer/recruiter
    with candidate's active resume re-attached and status transitioned to 'Followed Up'.
    """
    res = dispatch_application_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        attachment_path=attachment_path,
        sender_email=sender_email,
        app_password=app_password,
        allow_duplicate=True,
        dry_run=dry_run
    )
    if res.get("success"):
        mark_followed_up(app_id, notes=f"Day-4 Follow-up dispatched on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return res

def run_followup_cycle(
    sender_email: str = None,
    app_password: str = None,
    dry_run: bool = False
) -> dict:
    """
    Executes a batch follow-up cycle for all applications pending over 4 days,
    modeled directly after Desktop JobPilot's run_followup_cycle().
    """
    from .ai_engine import generate_followup_pitch
    
    due_apps = get_due_followups()
    if not due_apps:
        return {
            "success": True,
            "total_due": 0,
            "dispatched": 0,
            "skipped": 0,
            "errors": 0,
            "message": "No applications are currently due for Day-4 follow-up (0 pending).",
            "results": []
        }

    profile = get_active_profile() or {}
    creds = get_credentials()
    sender = (sender_email or creds.get("sender_email") or profile.get("email") or "").strip()
    pw = (app_password or creds.get("app_password") or "").strip()
    
    resume_path = get_default_resume_path()
    results = []
    dispatched_count = 0
    skipped_count = 0
    error_count = 0

    for app in due_apps:
        app_id = app["id"]
        company = app.get("company", "Company")
        role = app.get("job_title", "Position")
        recipient = (app.get("hr_email") or "").strip()

        # Check if recipient email exists
        if not recipient or "@" not in recipient:
            skipped_count += 1
            results.append({
                "app_id": app_id,
                "company": company,
                "role": role,
                "status": "Skipped (No HR email recorded)"
            })
            continue

        clean_recip = recipient.lower()
        if clean_recip in RECIPIENT_REDIRECTS:
            clean_recip = RECIPIENT_REDIRECTS[clean_recip]
            recipient = clean_recip

        if clean_recip in BOUNCED_OR_DEAD_EMAILS:
            skipped_count += 1
            results.append({
                "app_id": app_id,
                "company": company,
                "role": role,
                "status": f"Skipped (Flagged dead/bounce address {clean_recip})"
            })
            continue

        # Generate tailored follow-up pitch
        pitch = generate_followup_pitch(app, profile, language="auto")
        
        # Dispatch
        res = dispatch_followup_email(
            app_id=app_id,
            recipient_email=recipient,
            subject=pitch["subject"],
            body=pitch["body"],
            attachment_path=resume_path,
            sender_email=sender,
            app_password=pw,
            dry_run=dry_run
        )
        
        if res.get("success"):
            dispatched_count += 1
            results.append({
                "app_id": app_id,
                "company": company,
                "role": role,
                "status": "Dispatched",
                "recipient": recipient
            })
        else:
            error_count += 1
            results.append({
                "app_id": app_id,
                "company": company,
                "role": role,
                "status": f"Failed ({res.get('message')})",
                "recipient": recipient
            })

    return {
        "success": True,
        "total_due": len(due_apps),
        "dispatched": dispatched_count,
        "skipped": skipped_count,
        "errors": error_count,
        "message": f"Follow-up cycle finished: {dispatched_count} dispatched, {skipped_count} skipped, {error_count} errors.",
        "results": results
    }

def _decode_header_str(val: str) -> str:
    """Helper to decode MIME RFC2047 headers to unicode string."""
    if not val:
        return ""
    decoded_parts = []
    try:
        parts = decode_header(val)
        for text, charset in parts:
            if isinstance(text, bytes):
                try:
                    decoded_parts.append(text.decode(charset or "utf-8", errors="ignore"))
                except Exception:
                    decoded_parts.append(text.decode("latin-1", errors="ignore"))
            else:
                decoded_parts.append(str(text))
        return "".join(decoded_parts)
    except Exception:
        return str(val)

def scan_inbox_for_interview_invites(
    sender_email: str = None,
    app_password: str = None,
    days_back: int = 21,
    max_emails: int = 50
) -> dict:
    """
    Connects to candidate's Gmail inbox via IMAP SSL and looks up recruiter replies
    or interview opportunities matching tracked applications or interview keywords.
    """
    creds = get_credentials()
    email_clean = (sender_email or creds.get("sender_email") or "").strip()
    pw_clean = (app_password or creds.get("app_password") or "").replace(" ", "").strip()

    if not email_clean or not pw_clean:
        return {
            "success": False,
            "message": "Candidate Gmail credentials are missing. Please verify your email and 16-character Google App Password in Settings or Login Gateway."
        }

    # Retrieve all tracked companies and titles for correlation
    all_apps = get_applications(status="All")
    tracked_companies = {
        app["id"]: {
            "company": app.get("company", "").strip(),
            "role": app.get("job_title", "").strip(),
            "email": (app.get("hr_email") or "").strip().lower(),
            "status": app.get("status", "")
        }
        for app in all_apps if app.get("company")
    }

    # Interview indicator keywords (Bilingual BD context)
    interview_keywords = [
        "interview", "shortlisted", "shortlist", "assessment",
        "written test", "written exam", "technical test", "screening",
        "hiring process", "invitation to interview", "schedule an interview",
        "interview scheduled", "next round", "meeting link",
        "google meet", "zoom meeting", "congratulations",
        "সাক্ষাৎকার", "মৌখিক পরীক্ষা", "লিখিত পরীক্ষা", "নির্বাচন", "শর্টলিস্ট"
    ]

    # Regex for meeting links
    meeting_link_regex = re.compile(
        r'https?://(?:meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}|[a-zA-Z0-9\-\.]*zoom\.us/j/[0-9\?=_]+|teams\.microsoft\.com/l/meetup-join/[^\s"\'<>]+)',
        re.IGNORECASE
    )

    detected_interviews = []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=15)
        mail.login(email_clean, pw_clean)
        mail.select("INBOX", readonly=True)

        # Search for messages from the last N days
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        status, data = mail.search(None, f'(SINCE "{since_date}")')
        
        if status != "OK" or not data or not data[0]:
            mail.logout()
            return {
                "success": True,
                "count": 0,
                "interviews": [],
                "message": f"Connected to Gmail inbox ({email_clean}). No recruiter messages found in the last {days_back} days."
            }

        msg_ids = data[0].split()
        # Take the most recent messages up to max_emails
        recent_ids = msg_ids[-max_emails:]
        recent_ids.reverse()  # Newest first

        for mid in recent_ids:
            try:
                res_code, msg_data = mail.fetch(mid, "(RFC822.HEADER BODY[TEXT])")
                if res_code != "OK" or not msg_data:
                    continue

                raw_email = None
                for part in msg_data:
                    if isinstance(part, tuple) and len(part) > 1:
                        raw_email = part[1]
                        break

                if not raw_email:
                    continue

                msg = email.message_from_bytes(raw_email)
                subject = _decode_header_str(msg.get("Subject", ""))
                from_header = _decode_header_str(msg.get("From", ""))
                date_header = msg.get("Date", "")

                # Extract text body snippet
                body_snippet = ""
                if msg.is_multipart():
                    for subpart in msg.walk():
                        ctype = subpart.get_content_type()
                        cdispo = str(subpart.get("Content-Disposition"))
                        if ctype == "text/plain" and "attachment" not in cdispo:
                            payload = subpart.get_payload(decode=True)
                            if payload:
                                body_snippet += payload.decode("utf-8", errors="ignore")
                        elif ctype == "text/html" and not body_snippet and "attachment" not in cdispo:
                            payload = subpart.get_payload(decode=True)
                            if payload:
                                html_text = re.sub(r'<[^>]+>', ' ', payload.decode("utf-8", errors="ignore"))
                                body_snippet += " ".join(html_text.split())
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body_snippet = payload.decode("utf-8", errors="ignore")

                content_combined = f"{subject} {body_snippet} {from_header}".lower()

                # Check keyword match
                matched_kw = [kw for kw in interview_keywords if kw in content_combined]
                if not matched_kw:
                    continue

                # Check meeting links
                meeting_matches = meeting_link_regex.findall(f"{subject} {body_snippet}")
                meeting_url = meeting_matches[0] if meeting_matches else ""

                # Correlate with tracked applications
                matched_app = None
                confidence = "Medium"

                for app_id, app_info in tracked_companies.items():
                    c_name = app_info["company"].lower()
                    h_email = app_info["email"]
                    if (h_email and h_email in from_header.lower()) or (len(c_name) > 3 and c_name in content_combined):
                        matched_app = {
                            "id": app_id,
                            "company": app_info["company"],
                            "role": app_info["role"],
                            "current_status": app_info["status"]
                        }
                        confidence = "High"
                        break

                # Extract company name from sender if not matched
                inferred_company = matched_app["company"] if matched_app else from_header.split("<")[0].replace('"', '').strip()
                inferred_role = matched_app["role"] if matched_app else "Applicant"

                # Truncate clean snippet
                clean_snip = " ".join(body_snippet.split())[:280]

                detected_interviews.append({
                    "subject": subject,
                    "from": from_header,
                    "date": date_header,
                    "company": inferred_company,
                    "role": inferred_role,
                    "matched_app": matched_app,
                    "meeting_link": meeting_url,
                    "matched_keywords": matched_kw[:4],
                    "snippet": clean_snip,
                    "confidence": confidence
                })

            except Exception:
                continue

        try:
            mail.close()
        except Exception:
            pass
        mail.logout()

        return {
            "success": True,
            "count": len(detected_interviews),
            "interviews": detected_interviews,
            "message": f"Inbox scan complete: Found {len(detected_interviews)} potential interview opportunities or recruiter responses."
        }

    except imaplib.IMAP4.error as imap_err:
        return {
            "success": False,
            "message": f"Gmail IMAP authentication failed: {str(imap_err)}. Verify 16-character App Password in Settings."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Inbox lookup error: {str(e)}"
        }

