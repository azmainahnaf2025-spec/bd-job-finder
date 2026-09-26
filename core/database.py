"""
SQLite Database Engine for BD Job Finder.
Provides persistent, crash-proof storage for user profiles,
job application tracking (Kanban), and system configuration.
"""

import os
import json
import sqlite3
from datetime import datetime
import pandas as pd

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "jobs.db")
DEFAULT_GEMINI_KEY = "AQ.Ab8RN6KSV7C02uU5e97rlgHCyzGIEUpOSZZf3DcNFnNWCExqWw"

def get_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes schema if not present."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # User Profiles Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                linkedin TEXT,
                github_portfolio TEXT,
                target_industry TEXT,
                target_roles TEXT,
                preferred_locations TEXT,
                education_summary TEXT,
                skills_summary TEXT,
                raw_cv_text TEXT,
                resume_filename TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Applications CRM / Kanban Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                source_portal TEXT,
                apply_url TEXT,
                hr_email TEXT,
                status TEXT DEFAULT 'Saved',
                applied_date TEXT,
                deadline TEXT,
                salary TEXT,
                job_desc TEXT,
                match_score INTEGER DEFAULT 0,
                application_mode TEXT DEFAULT 'Portal',
                notes TEXT,
                screenshot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Safe migration for existing DB
        for col, col_type in [
            ("screenshot_path", "TEXT"),
            ("followup_sent_at", "TEXT"),
            ("interview_date", "TEXT"),
            ("interview_type", "TEXT"),
            ("meeting_link", "TEXT")
        ]:
            try:
                cursor.execute(f"ALTER TABLE applications ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass
        
        # System Settings Table (Gemini Key, theme preferences, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES ('gemini_api_key', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (DEFAULT_GEMINI_KEY,))
        
        conn.commit()

# Ensure database is initialized on import
init_db()

# ==============================================================================
# PROFILE MANAGEMENT (MULTI-CANDIDATE SUPPORT)
# ==============================================================================
def _parse_profile_row(row) -> dict | None:
    """Helper to parse a SQLite row into a clean profile dictionary."""
    if not row:
        return None
    profile = dict(row)
    try:
        profile["target_roles"] = json.loads(profile.get("target_roles") or "[]")
    except Exception:
        profile["target_roles"] = []
        
    try:
        profile["preferred_locations"] = json.loads(profile.get("preferred_locations") or "[]")
    except Exception:
        profile["preferred_locations"] = []
        
    return profile

def list_user_profiles() -> list[dict]:
    """Fetches all registered candidate profiles in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles ORDER BY id ASC")
        rows = cursor.fetchall()
        return [_parse_profile_row(r) for r in rows if r]

def get_active_profile_id() -> int | None:
    """Returns the ID of the currently selected active profile."""
    val = get_setting("active_profile_id", "")
    if val and str(val).isdigit():
        return int(val)
    return None

def set_active_profile_id(profile_id: int) -> bool:
    """Sets the designated active profile ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user_profiles WHERE id = ?", (profile_id,))
        if cursor.fetchone():
            set_setting("active_profile_id", str(profile_id))
            return True
    return False

def get_profile_by_id(profile_id: int) -> dict | None:
    """Retrieves a specific candidate profile by its unique ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
        return _parse_profile_row(cursor.fetchone())

def get_profile_by_email(email: str) -> dict | None:
    """Retrieves a specific candidate profile by email address (case-insensitive)."""
    if not email:
        return None
    clean = email.strip().lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE LOWER(email) = ? ORDER BY id DESC LIMIT 1", (clean,))
        return _parse_profile_row(cursor.fetchone())

def get_active_profile() -> dict | None:
    """Fetches the primary active candidate profile."""
    active_id = get_active_profile_id()
    if active_id:
        p = get_profile_by_id(active_id)
        if p:
            return p

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles ORDER BY updated_at DESC, id DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return None
        p = _parse_profile_row(row)
        set_setting("active_profile_id", str(p["id"]))
        return p

def save_active_profile(profile_data: dict) -> int:
    """
    Creates or updates a candidate profile.
    If profile_data has an id or an email matching an existing profile, updates that candidate.
    Otherwise inserts a new candidate record.
    Designates the saved profile as the currently active profile.
    """
    roles_json = json.dumps(profile_data.get("target_roles", []))
    locs_json = json.dumps(profile_data.get("preferred_locations", []))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    target_id = profile_data.get("id")
    email_clean = (profile_data.get("email") or "").strip().lower()

    with get_connection() as conn:
        cursor = conn.cursor()
        if not target_id and email_clean:
            cursor.execute("SELECT id FROM user_profiles WHERE LOWER(email) = ?", (email_clean,))
            r = cursor.fetchone()
            if r:
                target_id = r["id"]

        if target_id:
            cursor.execute("""
                UPDATE user_profiles SET
                    full_name = ?,
                    email = ?,
                    phone = ?,
                    linkedin = ?,
                    github_portfolio = ?,
                    target_industry = ?,
                    target_roles = ?,
                    preferred_locations = ?,
                    education_summary = ?,
                    skills_summary = ?,
                    raw_cv_text = ?,
                    resume_filename = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                profile_data.get("full_name", ""),
                profile_data.get("email", ""),
                profile_data.get("phone", ""),
                profile_data.get("linkedin", ""),
                profile_data.get("github_portfolio", ""),
                profile_data.get("target_industry", "IT & Software Engineering"),
                roles_json,
                locs_json,
                profile_data.get("education_summary", ""),
                profile_data.get("skills_summary", ""),
                profile_data.get("raw_cv_text", ""),
                profile_data.get("resume_filename", ""),
                now,
                target_id
            ))
            conn.commit()
            set_setting("active_profile_id", str(target_id))
            return target_id
        else:
            cursor.execute("""
                INSERT INTO user_profiles (
                    full_name, email, phone, linkedin, github_portfolio,
                    target_industry, target_roles, preferred_locations,
                    education_summary, skills_summary, raw_cv_text,
                    resume_filename, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile_data.get("full_name", "Job Seeker"),
                profile_data.get("email", ""),
                profile_data.get("phone", ""),
                profile_data.get("linkedin", ""),
                profile_data.get("github_portfolio", ""),
                profile_data.get("target_industry", "IT & Software Engineering"),
                roles_json,
                locs_json,
                profile_data.get("education_summary", ""),
                profile_data.get("skills_summary", ""),
                profile_data.get("raw_cv_text", ""),
                profile_data.get("resume_filename", ""),
                now
            ))
            conn.commit()
            new_id = cursor.lastrowid
            set_setting("active_profile_id", str(new_id))
            return new_id

def delete_user_profile(profile_id: int) -> bool:
    """Deletes a candidate profile. Switches active profile if deleted profile was active."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_profiles WHERE id = ?", (profile_id,))
        conn.commit()
        if cursor.rowcount > 0:
            active_id = get_active_profile_id()
            if active_id == profile_id:
                cursor.execute("SELECT id FROM user_profiles ORDER BY updated_at DESC, id DESC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    set_setting("active_profile_id", str(row["id"]))
                else:
                    set_setting("active_profile_id", "")
            return True
    return False

def get_active_resume_filename(profile: dict = None) -> str | None:
    """Returns the filename of the candidate's active uploaded CV / resume."""
    if profile and profile.get("resume_filename"):
        return profile["resume_filename"]
    prof = get_active_profile()
    if prof and prof.get("resume_filename"):
        return prof["resume_filename"]
    return None

def set_active_resume_filename(filename: str, profile_id: int = None) -> None:
    """Updates the candidate profile with the specified resume filename."""
    with get_connection() as conn:
        cursor = conn.cursor()
        target_id = profile_id or get_active_profile_id()
        if not target_id:
            cursor.execute("SELECT id FROM user_profiles ORDER BY updated_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                target_id = row["id"]
        if target_id:
            cursor.execute(
                "UPDATE user_profiles SET resume_filename = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (filename, target_id)
            )
            conn.commit()

# ==============================================================================
# APPLICATION TRACKER (KANBAN / CRM)
# ==============================================================================
VALID_STATUSES = [
    "Saved",
    "Applied",
    "Followed Up",
    "Interview Scheduled",
    "Interview Received",
    "Offer Received",
    "Rejected",
    "Archived"
]

def add_application(job: dict) -> int:
    """Adds a new opportunity into the tracker. Prevents duplicates by Company + Title, updates if applied."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check duplicate
        cursor.execute(
            "SELECT id, status, screenshot_path, notes FROM applications WHERE LOWER(company) = ? AND LOWER(job_title) = ?",
            (job.get("company", "").strip().lower(), job.get("job_title", "").strip().lower())
        )
        existing = cursor.fetchone()
        
        applied_date = job.get("applied_date") or (datetime.now().strftime("%Y-%m-%d") if "Applied" in str(job.get("status")) else "")
        shot_path = job.get("screenshot_path") or ""

        if existing:
            # If newly applied, update existing record with applied status, notes & screenshot
            if "Applied" in str(job.get("status", "")) or shot_path:
                cursor.execute("""
                    UPDATE applications SET
                        status = ?,
                        applied_date = COALESCE(NULLIF(?, ''), applied_date),
                        application_mode = COALESCE(?, application_mode),
                        notes = COALESCE(?, notes),
                        screenshot_path = COALESCE(NULLIF(?, ''), screenshot_path),
                        match_score = CASE WHEN ? > 0 THEN ? ELSE match_score END
                    WHERE id = ?
                """, (
                    job.get("status", "Applied"),
                    applied_date,
                    job.get("application_mode", "ATS Autopilot"),
                    job.get("notes"),
                    shot_path,
                    int(job.get("match_score", 0)),
                    int(job.get("match_score", 0)),
                    existing["id"]
                ))
                conn.commit()
            return existing["id"]
        
        cursor.execute("""
            INSERT INTO applications (
                job_title, company, location, source_portal, apply_url,
                hr_email, status, applied_date, deadline, salary,
                job_desc, match_score, application_mode, notes, screenshot_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("job_title", "Untitled Role"),
            job.get("company", "Undisclosed Company"),
            job.get("location", "Dhaka, Bangladesh"),
            job.get("source_portal", "BDJobs"),
            job.get("apply_url", ""),
            job.get("hr_email", ""),
            job.get("status", "Saved"),
            applied_date,
            job.get("deadline", "Open"),
            job.get("salary", "Negotiable"),
            job.get("job_desc", ""),
            int(job.get("match_score", 0)),
            job.get("application_mode", "Portal"),
            job.get("notes", ""),
            shot_path
        ))
        conn.commit()
        return cursor.lastrowid

def update_application_status(app_id: int, new_status: str, notes: str = None) -> bool:
    """Updates status and notes of a tracked job."""
    with get_connection() as conn:
        cursor = conn.cursor()
        now_date = datetime.now().strftime("%Y-%m-%d")
        
        if new_status == "Applied":
            cursor.execute("""
                UPDATE applications
                SET status = ?, applied_date = COALESCE(NULLIF(applied_date, ''), ?)
                WHERE id = ?
            """, (new_status, now_date, app_id))
        else:
            cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, app_id))
            
        if notes is not None:
            cursor.execute("UPDATE applications SET notes = ? WHERE id = ?", (notes, app_id))
            
        conn.commit()
        return cursor.rowcount > 0

def delete_application(app_id: int) -> bool:
    """Removes a job entry."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_applications(status: str = None, search: str = None) -> list[dict]:
    """Retrieves tracked applications with optional filtering."""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM applications WHERE 1=1"
        params = []
        
        if status and status != "All":
            query += " AND status = ?"
            params.append(status)
            
        if search:
            query += " AND (LOWER(job_title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(location) LIKE ?)"
            term = f"%{search.strip().lower()}%"
            params.extend([term, term, term])
            
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

def check_duplicate_application(company: str = "", title: str = "", email: str = "") -> tuple[bool, str, str, str]:
    """
    Checks whether an application was already dispatched or recorded for this company, role, or email.
    Returns: (is_duplicate: bool, message: str, applied_date: str, status: str)
    """
    comp_clean = (company or "").strip().lower()
    title_clean = (title or "").strip().lower()
    email_clean = (email or "").strip().lower()

    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Check if email was already dispatched to
        if email_clean and "@" in email_clean:
            cursor.execute(
                "SELECT * FROM applications WHERE LOWER(hr_email) = ? AND (status LIKE '%Applied%' OR status IN ('Interview Scheduled', 'Offer Received')) ORDER BY id DESC LIMIT 1",
                (email_clean,)
            )
            row = cursor.fetchone()
            if row:
                d = row["applied_date"] or row["created_at"] or "Earlier"
                s = row["status"] or "Applied"
                msg = f"An application was already dispatched to '{email_clean}' on {d} ({row['company']} - {row['job_title']})."
                return True, msg, str(d), str(s)

        # 2. Check if company + title matches an existing application
        if comp_clean and title_clean:
            cursor.execute(
                "SELECT * FROM applications WHERE LOWER(company) = ? AND LOWER(job_title) = ? AND (status LIKE '%Applied%' OR status IN ('Interview Scheduled', 'Offer Received')) ORDER BY id DESC LIMIT 1",
                (comp_clean, title_clean)
            )
            row = cursor.fetchone()
            if row:
                d = row["applied_date"] or row["created_at"] or "Earlier"
                s = row["status"] or "Applied"
                msg = f"Already dispatched application for '{row['job_title']}' at '{row['company']}' on {d}."
                return True, msg, str(d), str(s)

        # 3. Fuzzy company name match if company has 2+ words
        if comp_clean and len(comp_clean) > 4:
            cursor.execute(
                "SELECT * FROM applications WHERE LOWER(company) LIKE ? AND status IN ('Applied', 'Interview Scheduled', 'Offer Received') ORDER BY id DESC LIMIT 1",
                (f"%{comp_clean}%",)
            )
            row = cursor.fetchone()
            if row and title_clean:
                # check if titles share key tokens
                title_words = [w for w in title_clean.split() if len(w) > 3]
                existing_title = row["job_title"].lower()
                if any(w in existing_title for w in title_words):
                    d = row["applied_date"] or row["created_at"] or "Earlier"
                    s = row["status"] or "Applied"
                    msg = f"Similar application already dispatched to '{row['company']}' ({row['job_title']}) on {d}."
                    return True, msg, str(d), str(s)

    return False, "", "", ""

def is_already_processed(company: str, title: str = "", email: str = "") -> bool:
    """Convenience boolean check for scrapers and queues."""
    is_dup, _, _, _ = check_duplicate_application(company, title, email)
    return is_dup

def get_due_followups() -> list[dict]:
    """
    Retrieves applications that were applied >= 4 days ago and haven't had a follow-up sent yet.
    Directly modeled after Desktop JobPilot's get_due_followups_count.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE (status = 'Applied' OR status LIKE 'Applied%') ORDER BY id DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        
        due = []
        now = datetime.now()
        for app in rows:
            # If already followed up, skip
            if app.get("followup_sent_at"):
                continue
            applied_val = app.get("applied_date")
            if not applied_val:
                continue
            try:
                # Parse date (handles %Y-%m-%d or full timestamp)
                applied_date = datetime.strptime(str(applied_val)[:10], "%Y-%m-%d")
                days_pending = (now - applied_date).days
                if days_pending >= 4:
                    app_copy = dict(app)
                    app_copy["days_pending"] = days_pending
                    due.append(app_copy)
            except Exception:
                pass
        return due

def get_due_followups_count() -> int:
    """Returns total count of applications due for 4-day follow-up."""
    return len(get_due_followups())

def mark_followed_up(app_id: int, notes: str = None, followup_date: str = None) -> bool:
    """Marks an application as Followed Up and records the timestamp."""
    f_date = followup_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        if notes:
            cursor.execute("""
                UPDATE applications
                SET status = 'Followed Up',
                    followup_sent_at = ?,
                    notes = CASE WHEN notes IS NULL OR notes = '' THEN ? ELSE notes || ' | ' || ? END
                WHERE id = ?
            """, (f_date, notes, notes, app_id))
        else:
            cursor.execute("""
                UPDATE applications
                SET status = 'Followed Up',
                    followup_sent_at = ?
                WHERE id = ?
            """, (f_date, app_id))
        conn.commit()
        return cursor.rowcount > 0

def get_interview_opportunities() -> list[dict]:
    """Retrieves all tracked applications that have reached an interview stage."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM applications
            WHERE status IN ('Interview Scheduled', 'Interview Received')
            ORDER BY id DESC
        """)
        return [dict(r) for r in cursor.fetchall()]

def record_interview_chance(
    app_id: int,
    interview_date: str = "",
    interview_type: str = "Technical Interview",
    meeting_link: str = "",
    notes: str = ""
) -> bool:
    """
    Updates or records an interview opportunity for a given application ID.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE applications SET
                status = 'Interview Scheduled',
                interview_date = COALESCE(NULLIF(?, ''), interview_date),
                interview_type = COALESCE(NULLIF(?, ''), interview_type),
                meeting_link = COALESCE(NULLIF(?, ''), meeting_link),
                notes = CASE 
                    WHEN ? IS NULL OR ? = '' THEN notes 
                    WHEN notes IS NULL OR notes = '' THEN ? 
                    ELSE notes || ' | ' || ? 
                END
            WHERE id = ?
        """, (interview_date, interview_type, meeting_link, notes, notes, notes, notes, app_id))
        conn.commit()
        return cursor.rowcount > 0

def get_application_stats() -> dict:
    """Returns count breakdown by status, including follow-ups due and interviews."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) as cnt FROM applications GROUP BY status")
        counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
        
        due_followups = get_due_followups_count()
        interviews = counts.get("Interview Scheduled", 0) + counts.get("Interview Received", 0)
        total = sum(counts.values())
        return {
            "Total": total,
            "Saved": counts.get("Saved", 0),
            "Applied": counts.get("Applied", 0),
            "Followed Up": counts.get("Followed Up", 0),
            "Interviews": interviews,
            "Interview Scheduled": counts.get("Interview Scheduled", 0),
            "Interview Received": counts.get("Interview Received", 0),
            "Offer Received": counts.get("Offer Received", 0),
            "Rejected": counts.get("Rejected", 0),
            "Archived": counts.get("Archived", 0),
            "Due Followups": due_followups
        }

def export_applications_dataframe() -> pd.DataFrame:
    """Exports tracker to a clean pandas DataFrame for Excel/CSV generation."""
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM applications ORDER BY id DESC", conn)
        return df

# ==============================================================================
# SYSTEM SETTINGS
# ==============================================================================
# Default Gemini API key from Desktop JobPilot
DEFAULT_GEMINI_KEY = "AQ.Ab8RN6KSV7C02uU5e97rlgHCyzGIEUpOSZZf3DcNFnNWCExqWw"

def get_setting(key: str, default: str = "") -> str:
    """Retrieves a persistent setting value."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row and row["value"] and row["value"].strip():
            return row["value"]
        if key == "gemini_api_key":
            return default or DEFAULT_GEMINI_KEY
        return default

def set_setting(key: str, value: str):
    """Sets or updates a persistent setting. Protects Gemini API key from being changed."""
    if key == "gemini_api_key":
        value = DEFAULT_GEMINI_KEY
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()

def get_credentials(profile_id: int = None) -> dict:
    """Retrieves API and email dispatch credentials dynamically based on active user profile."""
    prof = get_profile_by_id(profile_id) if profile_id else get_active_profile()
    prof = prof or {}
    user_email = prof.get("email", "")
    pid = prof.get("id")

    # Check candidate-specific sender email and password first, then candidate profile email, then global settings
    cand_sender = get_setting(f"sender_email_{pid}", "") if pid else ""
    cand_pw = get_setting(f"app_password_{pid}", "") if pid else ""

    # Primary default sender is active candidate profile email
    sender_email = cand_sender or user_email or get_setting("sender_email", "").strip()

    # App Password resolution:
    # 1. Candidate's own configured App Password
    # 2. Or global app_password ONLY if sender_email matches the global sender_email account
    global_sender = get_setting("sender_email", "").strip().lower()
    global_pw = get_setting("app_password", "").strip()

    if cand_pw:
        app_password = cand_pw
    elif sender_email.lower() == global_sender and global_pw:
        app_password = global_pw
    else:
        # Never leak an unrelated candidate's Google password into another user's email!
        app_password = ""

    return {
        "gemini_api_key": DEFAULT_GEMINI_KEY,
        "sender_email": sender_email,
        "app_password": app_password
    }

def save_credentials(gemini_api_key: str = None, sender_email: str = "", app_password: str = "", profile_id: int = None):
    """Saves API and email dispatch credentials globally and for the specific candidate profile."""
    pid = profile_id or get_active_profile_id()
    # Gemini API Key is locked to DEFAULT_GEMINI_KEY and cannot be altered
    set_setting("gemini_api_key", DEFAULT_GEMINI_KEY)
    if sender_email is not None:
        clean_sender = sender_email.strip()
        set_setting("sender_email", clean_sender)
        if pid:
            set_setting(f"sender_email_{pid}", clean_sender)
    if app_password is not None:
        clean_pw = app_password.strip()
        set_setting("app_password", clean_pw)
        if pid:
            set_setting(f"app_password_{pid}", clean_pw)

def is_system_configured() -> bool:
    """Checks whether the primary candidate profile and basic settings exist."""
    prof = get_active_profile()
    if prof and prof.get("full_name") and prof.get("full_name") != "Job Seeker":
        return True
    return False

def logout_and_wipe_all_user_data() -> None:
    """
    Completely forgets/purges all user information across the app on logout:
    - Deletes all candidate records from user_profiles
    - Deletes all CRM applications from applications
    - Deletes all candidate credentials (sender_email, app_password, active_profile_id, etc.) from settings
    - Keeps the permanent Gemini API key intact and unchangeable
    - Deletes all uploaded resume/CV files from data/resumes
    - Cleans up temporary screenshots from data/screenshots
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_profiles")
        cursor.execute("DELETE FROM applications")
        cursor.execute("DELETE FROM settings WHERE key != 'gemini_api_key'")
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES ('gemini_api_key', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (DEFAULT_GEMINI_KEY,))
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('user_profiles', 'applications')")
        except Exception:
            pass
        conn.commit()

    # Delete all candidate CVs from disk
    resumes_dir = os.path.join(DB_DIR, "resumes")
    if os.path.exists(resumes_dir):
        for f in os.listdir(resumes_dir):
            fp = os.path.join(resumes_dir, f)
            if os.path.isfile(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass

    # Delete application/ats screenshots from disk
    screenshots_dir = os.path.join(DB_DIR, "screenshots")
    if os.path.exists(screenshots_dir):
        for f in os.listdir(screenshots_dir):
            fp = os.path.join(screenshots_dir, f)
            if os.path.isfile(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass

