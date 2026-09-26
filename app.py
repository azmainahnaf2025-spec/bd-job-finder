"""
BD Job Finder — All-Bangladesh Public Job Search & Circular Assistant.
Public-facing web platform for job seekers across all sectors and districts in Bangladesh.
"""

import os
import io
import json
import time
import importlib
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

import core.database
import core.taxonomy
import core.portals_registry
import core.cv_parser
import core.scraper
import core.ai_engine
import core.email_dispatcher

try:
    importlib.reload(core.database)
    importlib.reload(core.taxonomy)
    importlib.reload(core.portals_registry)
    importlib.reload(core.cv_parser)
    importlib.reload(core.scraper)
    importlib.reload(core.ai_engine)
    importlib.reload(core.email_dispatcher)
except Exception:
    pass

from core.taxonomy import (
    BD_JOB_TAXONOMY,
    BD_DIVISIONS_AND_DISTRICTS,
    JOB_TYPES,
    EXPERIENCE_LEVELS,
    get_all_job_titles,
    get_all_districts
)
from core.portals_registry import (
    BD_JOB_PORTALS,
    get_portal_search_url,
    get_portals_by_category
)
from core.database import (
    get_active_profile,
    save_active_profile,
    add_application,
    update_application_status,
    delete_application,
    get_applications,
    get_application_stats,
    export_applications_dataframe,
    get_setting,
    set_setting,
    get_credentials,
    save_credentials,
    is_system_configured,
    logout_and_wipe_all_user_data,
    DEFAULT_GEMINI_KEY,
    VALID_STATUSES,
    check_duplicate_application,
    is_already_processed,
    get_active_resume_filename,
    set_active_resume_filename,
    get_due_followups,
    get_due_followups_count,
    mark_followed_up,
    get_interview_opportunities,
    record_interview_chance,
    list_user_profiles,
    set_active_profile_id,
    get_profile_by_id,
    get_profile_by_email,
    delete_user_profile
)
from core.cv_parser import (
    extract_text_from_pdf,
    summarize_profile_from_cv,
    deep_parse_cv_with_ai
)
import importlib
import core.site_dispatcher
importlib.reload(core.site_dispatcher)
from core.site_dispatcher import (
    launch_ats_autopilot_session,
    submit_to_site_form_playwright,
    detect_company_contact_form
)
from core.scraper import (
    search_bangladesh_jobs,
    discover_ai_strategic_targets,
    get_estimated_search_metrics,
    crawl_bangladesh_job_portals,
    deep_extract_company_recruitment_email
)
from core.ai_engine import (
    scan_circular_image,
    analyze_resume_match,
    generate_application_pitch,
    generate_followup_pitch,
    generate_interview_prep,
    resolve_job_salary,
    get_gemini_client
)
from core.email_dispatcher import (
    dispatch_application_email,
    dispatch_followup_email,
    run_followup_cycle,
    scan_inbox_for_interview_invites,
    get_default_resume_path,
    save_uploaded_resume,
    list_available_resumes,
    get_pdf_base64,
    generate_gmail_compose_url,
    generate_mailto_url,
    authenticate_gmail_credentials,
    RESUMES_DIR
)

# ==============================================================================
# PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="BD Job Finder — Bangladesh Recruitment Hub",
    page_icon="🇧🇩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Google Stitch AI Design System & Bangladesh Emerald Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans+Text:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Google Sans Text', 'Inter', -apple-system, sans-serif;
    }

    :root {
        --bd-green: #006a4e;
        --bd-emerald: #0b3b2c;
        --bd-red: #e11d48;
        --slate-bg: #f8fafc;
        --card-border: #e2e8f0;
    }

    /* Google Stitch Hero Banner */
    .stitch-hero-banner {
        background: linear-gradient(135deg, #092c20 0%, #0d3829 60%, #061c14 100%);
        border: 1px solid #164e39;
        padding: 22px 26px;
        border-radius: 14px;
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0, 44, 32, 0.15);
    }
    .stitch-hero-banner h1 {
        color: #ffffff !important;
        margin: 0;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .stitch-hero-banner p {
        color: #a7f3d0;
        margin-top: 6px;
        font-size: 14px;
        line-height: 1.5;
    }

    /* Google Stitch Feature Launcher Tiles */
    .stitch-launcher-card {
        background: #ffffff;
        border: 1.5px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: all 0.2s ease-in-out;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    }
    .stitch-launcher-card:hover {
        border-color: #006a4e;
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0, 106, 78, 0.1);
    }

    /* Stitch Card & Metric Boxes */
    .stitch-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    }
    .stitch-card-header {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .main-header {
        background: linear-gradient(135deg, #00563f 0%, #007a5a 100%);
        padding: 22px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 { color: #ffffff !important; margin: 0; font-size: 26px; }
    .main-header p { color: #d1fae5; margin-top: 6px; font-size: 14px; }
    
    .job-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .job-card:hover {
        border-color: #007a5a;
        box-shadow: 0 6px 12px rgba(0, 106, 78, 0.08);
    }
    .stat-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
    }
    .portal-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
    }
    .status-badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    .status-saved { background: #f1f5f9; color: #475569; }
    .status-applied { background: #dbeafe; color: #1d4ed8; }
    .status-followed-up { background: #ede9fe; color: #6d28d9; border: 1px solid #ddd6fe; }
    .status-interview { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .status-interview-scheduled { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .status-interview-received { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .status-offer { background: #fef08a; color: #854d0e; }
    .status-offer-received { background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
    .status-rejected { background: #fee2e2; color: #b91c1c; }
    .status-archived { background: #f1f5f9; color: #64748b; }

    /* Primary Action Coral/Red Button matching JobPilot & Stitch */
    button[kind="primary"] {
        background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(225, 29, 72, 0.25) !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #e11d48 0%, #be123c 100%) !important;
        box-shadow: 0 4px 8px rgba(225, 29, 72, 0.35) !important;
    }

    /* Streamlit Tab Bar Polish matching Stitch Navigation */
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #006a4e !important;
        border-bottom-color: #006a4e !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "ocr_result" not in st.session_state:
    st.session_state.ocr_result = None
if "drafts" not in st.session_state:
    st.session_state["drafts"] = {}
if "authenticated" not in st.session_state:
    st.session_state.authenticated = is_system_configured()

# Fetch active credentials
creds = get_credentials()

# ==============================================================================
# ONBOARDING & LOGIN GATEWAY
# ==============================================================================
if not st.session_state.authenticated:
    st.markdown("""
    <div class="main-header">
        <h1>🇧🇩 BD Job Finder — System Access & Candidate Login Gateway</h1>
        <p>Set up your candidate identity and software engine credentials to run autonomous search, circular OCR, and cold outreach engines across Bangladesh.</p>
    </div>
    """, unsafe_allow_html=True)

    all_registered_profiles = list_user_profiles()
    existing_profile = get_active_profile()

    # If user explicitly clicked "Add New Candidate", blank out the form fields
    if st.session_state.get("add_new_candidate"):
        st.session_state.login_name = ""
        st.session_state.login_email = ""
        st.session_state.login_phone = ""
        st.session_state.login_linkedin = ""
        st.session_state.login_edu = ""
        st.session_state.login_skills = ""
        st.session_state.login_industry = "IT & Software Engineering"
        st.session_state.cv_uploaded_id = None

    if all_registered_profiles and not st.session_state.get("add_new_candidate"):
        st.info("👥 **Registered Candidate Profiles:** Select your candidate identity below to load your personalized email drafts, phone, and resume:")
        p_cols = st.columns(min(len(all_registered_profiles), 3))
        for i, prof_item in enumerate(all_registered_profiles):
            with p_cols[i % len(p_cols)]:
                p_name = prof_item.get("full_name", "Candidate")
                p_email = prof_item.get("email", "No Email")
                p_phone = prof_item.get("phone", "No Phone")
                p_res = prof_item.get("resume_filename", "No Resume")
                is_curr = (existing_profile and existing_profile.get("id") == prof_item.get("id"))
                card_border = "#059669" if is_curr else "#cbd5e1"
                active_pill = " <span style='background: #ecfdf5; color: #065f46; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 700;'>Active</span>" if is_curr else ""
                
                st.markdown(f"""
                <div style="border: 1.5px solid {card_border}; border-radius: 8px; padding: 12px; margin-bottom: 8px; background: #ffffff;">
                    <div style="font-weight: 700; font-size: 14px; color: #0f172a;">👤 {p_name}{active_pill}</div>
                    <div style="font-size: 12px; color: #475569; margin-top: 4px;">📧 <code>{p_email}</code></div>
                    <div style="font-size: 12px; color: #475569;">📱 <code>{p_phone}</code></div>
                    <div style="font-size: 11px; color: #047857; margin-top: 4px;">📎 <i>{p_res}</i></div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🚀 Continue as {p_name.split()[0]}", key=f"btn_choose_prof_{prof_item['id']}", use_container_width=True, type="primary" if is_curr else "secondary"):
                    set_active_profile_id(prof_item["id"])
                    st.session_state["drafts"] = {}
                    st.session_state["search_results"] = []
                    for k in list(st.session_state.keys()):
                        if any(k.startswith(p) for p in ["subj_", "body_", "sender_", "email_", "proof_"]):
                            st.session_state.pop(k, None)
                    st.session_state.authenticated = True
                    st.rerun()

        st.markdown("---")
        st.caption("Or register a new candidate / upload a new resume below:")

    # Initialize form fields in session state for instant auto-fill
    if "login_name" not in st.session_state:
        st.session_state.login_name = existing_profile.get("full_name", "") if existing_profile and existing_profile.get("full_name") != "Job Seeker" else ""
    if "login_email" not in st.session_state:
        st.session_state.login_email = existing_profile.get("email", "") if existing_profile else ""
    if "login_phone" not in st.session_state:
        st.session_state.login_phone = existing_profile.get("phone", "") if existing_profile else ""
    if "login_linkedin" not in st.session_state:
        st.session_state.login_linkedin = existing_profile.get("linkedin", "") if existing_profile else ""
    if "login_edu" not in st.session_state:
        st.session_state.login_edu = existing_profile.get("education_summary", "") if existing_profile else ""
    if "login_skills" not in st.session_state:
        st.session_state.login_skills = existing_profile.get("skills_summary", "") if existing_profile else ""
    if "login_industry" not in st.session_state:
        st.session_state.login_industry = existing_profile.get("target_industry", "IT & Software Engineering") if existing_profile else "IT & Software Engineering"
    if "cv_uploaded_id" not in st.session_state:
        st.session_state.cv_uploaded_id = None
    if "social_auth_provider" not in st.session_state:
        st.session_state.social_auth_provider = None

    # ==============================================================================
    # 🌐 1. SOCIAL LOGIN OPTIONS (Google, LinkedIn, Facebook)
    # ==============================================================================
    st.markdown("### 🌐 Quick Sign-In with Social Accounts")
    st.caption("Authenticate or auto-import your verified identity instantly:")
    
    soc_c1, soc_c2, soc_c3 = st.columns(3)
    with soc_c1:
        if st.button("🔴 Continue with Google", use_container_width=True):
            st.session_state.social_auth_provider = "Google"
    with soc_c2:
        if st.button("🔵 Continue with LinkedIn", use_container_width=True):
            st.session_state.social_auth_provider = "LinkedIn"
    with soc_c3:
        if st.button("📘 Continue with Facebook", use_container_width=True):
            st.session_state.social_auth_provider = "Facebook"

    # Social Connect Modal Card
    if st.session_state.social_auth_provider:
        prov = st.session_state.social_auth_provider
        st.info(f"🔗 **Connect with {prov}**: Enter your verified credentials to authorize and launch your dashboard.")
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            soc_email_val = st.text_input(
                f"{prov} Account Email (Gmail) *",
                value=st.session_state.login_email or "",
                placeholder="your.email@gmail.com",
                key=f"s_email_{prov}",
                help="Your personal Gmail address required for logging in and automated application dispatch."
            )
        with s_c2:
            default_soc_name = st.session_state.login_name or ""
            soc_name_val = st.text_input(
                "Candidate Full Name *",
                value=default_soc_name,
                placeholder="e.g. Rahim Ahmed",
                key=f"s_name_{prov}"
            )
        
        st.markdown("""
        <div style="background: #fffbeb; border: 1.5px solid #f59e0b; border-radius: 8px; padding: 10px 14px; margin: 10px 0;">
            <div style="font-weight: 700; color: #b45309; font-size: 13px;">
                🔑 Where to find your App Password & How to paste it:
            </div>
            <div style="font-size: 12px; color: #92400e; line-height: 1.5; margin-top: 4px;">
                <b>1. Find it:</b> Open <a href="https://myaccount.google.com/apppasswords" target="_blank" style="color: #b45309; font-weight: 700; text-decoration: underline;">👉 Google App Passwords</a> (ensure 2-Step Verification is active).<br/>
                <b>2. Generate:</b> Enter App Name <code>BD Job Finder</code>, click <b>Create</b>, and copy the 16-letter code (e.g. <code>abcd efgh ijkl mnop</code>).<br/>
                <b>3. Paste it:</b> Click in the box below and press <b>Ctrl + V</b> (or Right-Click ➔ Paste).
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        soc_pw_val = st.text_input(
            "Gmail 16-Character App Password (Mandatory) *",
            type="password",
            placeholder="e.g. abcd efgh ijkl mnop (press Ctrl+V to paste here)",
            key=f"s_pw_{prov}",
            help="Mandatory: Required to enable direct application dispatch, recruiter email extraction, and automated delivery."
        )
        st.caption("🔒 *App Password is mandatory: without it, the app cannot directly dispatch applications or approve emails on your behalf.*")

        s_btn1, s_btn2 = st.columns([1.5, 1])
        with s_btn1:
            if st.button(f"🚀 Authorize & Launch as {prov} User", type="primary", use_container_width=True, key=f"btn_auth_{prov}"):
                clean_soc_pw = soc_pw_val.strip().replace(" ", "")
                if not soc_email_val.strip() or "@" not in soc_email_val:
                    st.error("Please provide a valid Gmail address to log in.")
                elif not soc_name_val.strip():
                    st.error("Please provide your full name.")
                elif not clean_soc_pw or len(clean_soc_pw) < 16:
                    st.error("⚠️ Gmail 16-Character App Password is MANDATORY! Without this access, the app cannot directly dispatch applications or verify email delivery.")
                else:
                    prof = existing_profile or {}
                    prof["full_name"] = soc_name_val.strip()
                    prof["email"] = soc_email_val.strip()
                    if prov == "LinkedIn" and not prof.get("linkedin"):
                        prof["linkedin"] = f"https://linkedin.com/in/{soc_name_val.lower().replace(' ', '-')}"
                    save_active_profile(prof)
                    save_credentials(
                        gemini_api_key=DEFAULT_GEMINI_KEY,
                        sender_email=soc_email_val.strip(),
                        app_password=clean_soc_pw
                    )
                    st.session_state.authenticated = True
                    st.session_state.social_auth_provider = None
                    st.success(f"Connected with {prov}! Launching dashboard...")
                    st.rerun()
        with s_btn2:
            if st.button("✖️ Cancel", key=f"btn_cancel_{prov}"):
                st.session_state.social_auth_provider = None
                st.rerun()

    st.markdown("<div style='text-align: center; color: #94a3b8; margin: 16px 0;'>─── OR AUTO-FILL FROM CV / FILL DETAILS BELOW ───</div>", unsafe_allow_html=True)

    # ==============================================================================
    # 📄 2. AUTO-READ FROM CV & FILL FORM (Drag & Drop)
    # ==============================================================================
    st.subheader("📄 Auto-Read from CV (Drag & Drop)")
    st.caption("Upload your resume (PDF) — Gemini AI will automatically extract your name, contact details, education, and skills into the form below!")
    
    login_cv_file = st.file_uploader("Upload CV / Resume (PDF) to Auto-Fill All Form Fields", type=["pdf"], key="login_cv_uploader")
    if login_cv_file:
        file_signature = f"{login_cv_file.name}_{login_cv_file.size}"
        if st.session_state.cv_uploaded_id != file_signature:
            with st.spinner("⚡ AI reading and auto-extracting all candidate details from your CV..."):
                save_uploaded_resume(login_cv_file.getvalue(), login_cv_file.name)
                extracted_text = extract_text_from_pdf(login_cv_file.getvalue())
                parsed = deep_parse_cv_with_ai(extracted_text)
                
                if parsed.get("full_name") and parsed["full_name"].lower() != "job seeker":
                    st.session_state.login_name = parsed["full_name"]
                if parsed.get("email"):
                    st.session_state.login_email = parsed["email"]
                if parsed.get("phone"):
                    st.session_state.login_phone = parsed["phone"]
                if parsed.get("linkedin"):
                    st.session_state.login_linkedin = parsed["linkedin"]
                if parsed.get("education_summary"):
                    st.session_state.login_edu = parsed["education_summary"]
                if parsed.get("skills_summary"):
                    st.session_state.login_skills = parsed["skills_summary"]
                if parsed.get("target_industry") and parsed["target_industry"] in BD_JOB_TAXONOMY:
                    st.session_state.login_industry = parsed["target_industry"]
                    
                st.session_state["raw_cv_extracted"] = extracted_text
                st.session_state["active_resume_filename"] = login_cv_file.name
                st.session_state.cv_uploaded_id = file_signature

                # Persist uploaded CV directly into database profile
                curr_prof = get_active_profile() or {}
                curr_prof["resume_filename"] = login_cv_file.name
                curr_prof["raw_cv_text"] = extracted_text
                if parsed.get("full_name") and parsed["full_name"].lower() != "job seeker":
                    curr_prof["full_name"] = parsed["full_name"]
                if parsed.get("email"):
                    curr_prof["email"] = parsed["email"]
                save_active_profile(curr_prof)
                set_active_resume_filename(login_cv_file.name)

                st.success(f"🎉 CV auto-read complete! Name: **{st.session_state.login_name}**, Email: **{st.session_state.login_email}**. Attached CV set to: **{login_cv_file.name}**!")
                st.rerun()

    # ==============================================================================
    # 📋 3. CANDIDATE PROFILE & CREDENTIALS FORM
    # ==============================================================================
    st.subheader("📋 Candidate Profile & Engine Setup")
    st.caption("Review your auto-filled fields and click 'Launch BD Job Finder'. All data is stored locally in SQLite (`data/jobs.db`).")

    with st.form("login_gateway_form"):
        st.markdown("##### 👤 1. Candidate Identity")
        c1, c2 = st.columns(2)
        with c1:
            name_input = st.text_input("Full Name *", value=st.session_state.login_name, placeholder="e.g. Rahim Ahmed")
            email_input = st.text_input("Candidate Email Address (Required to Login & Apply) *", value=st.session_state.login_email, placeholder="e.g. your_email@gmail.com")
            phone_input = st.text_input("Phone Number (+880) *", value=st.session_state.login_phone, placeholder="+8801831731294")
        with c2:
            ind_options = list(BD_JOB_TAXONOMY.keys())
            def_idx = ind_options.index(st.session_state.login_industry) if st.session_state.login_industry in ind_options else 0
            ind_input = st.selectbox("Primary Career Sector *", ind_options, index=def_idx)
            
            district_options = ["All Districts (সমগ্র বাংলাদেশ)"] + get_all_districts()
            loc_input = st.selectbox("Preferred Job Location / District", district_options)
            linkedin_input = st.text_input("LinkedIn Profile URL", value=st.session_state.login_linkedin, placeholder="https://linkedin.com/in/...")

        st.markdown("##### 🎓 2. Education & Core Skills (Auto-Populated from CV)")
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            edu_input = st.text_area("Education Summary", value=st.session_state.login_edu, placeholder="e.g. BBA in MIS / B.Sc in CSE / MBA in Supply Chain", height=80)
        with e_col2:
            skills_input = st.text_area("Skills & Competencies (comma-separated)", value=st.session_state.login_skills, placeholder="e.g. Python, Excel, Merchandising, Banking, Digital Marketing", height=80)

        st.markdown("##### 🔑 3. Software Engine Credentials")
        st.caption("The Gemini API key is pre-filled from your Desktop JobPilot configuration. Your Gmail address and 16-character App Password are required for direct application dispatch and recruiter extraction.")
        
        k_col1, k_col2 = st.columns(2)
        with k_col1:
            gemini_input = st.text_input(
                "Google Gemini API Key 🔒 (System Key - Unchangeable)",
                value=DEFAULT_GEMINI_KEY,
                type="password",
                disabled=True,
                help="Permanent system key configured for Gemini 2.5/Flash AI models. This key is permanent and cannot be modified."
            )
            st.caption("🔒 *Permanent System Key (`AQ.Ab8...`) — Locked & Unchangeable*")
        with k_col2:
            sender_email_input = st.text_input(
                "Outbound Application Sender (Gmail Address) *",
                value=st.session_state.login_email or creds.get("sender_email", ""),
                placeholder="your_email@gmail.com",
                help="The Gmail account used to authenticate and send applications directly to recruiters. Can be edited if different from your candidate contact email."
            )
            app_pw_input = st.text_input(
                "Gmail 16-Character App Password (Mandatory) *",
                value=creds.get("app_password", ""),
                type="password",
                placeholder="e.g. abcd efgh ijkl mnop (press Ctrl+V to paste here)",
                help="Mandatory: Required to enable direct application dispatch, recruiter email extraction, and automated delivery."
            )

        st.markdown("""
        <div style="background: #fffbeb; border: 2px solid #f59e0b; border-radius: 10px; padding: 16px; margin: 12px 0;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="font-size: 20px;">🔑</span>
                <span style="font-weight: 700; font-size: 15px; color: #b45309;">
                    WHERE TO FIND YOUR APP PASSWORD & HOW TO PASTE IT:
                </span>
            </div>
            <div style="font-size: 13px; color: #92400e; line-height: 1.6;">
                <b>📍 PART 1 — WHERE TO FIND IT:</b>
                <ol style="margin: 4px 0 10px 0; padding-left: 20px;">
                    <li>Ensure <b>2-Step Verification</b> is turned ON in your <a href="https://myaccount.google.com/signinoptions/two-step-verification" target="_blank" style="color: #b45309; font-weight: 700; text-decoration: underline;">Google Security Settings</a>.</li>
                    <li>Directly open Google's password page: <a href="https://myaccount.google.com/apppasswords" target="_blank" style="color: #b45309; font-weight: 700; text-decoration: underline;">👉 Open Google App Passwords Page (Click Here)</a>.</li>
                    <li>In the <b>App name</b> box, type <code>BD Job Finder</code> and click <b>Create</b>.</li>
                    <li>Google will display a pop-up modal showing your unique <b>16-letter password</b> (for example: <code>abcd efgh ijkl mnop</code>).</li>
                </ol>
                <b>📋 PART 2 — HOW TO COPY & PASTE IT:</b>
                <ol style="margin: 4px 0 0 0; padding-left: 20px;">
                    <li><b>Copy:</b> Highlight the 16 letters in Google's pop-up and press <b>Ctrl + C</b> (or right-click ➔ Copy).</li>
                    <li><b>Paste:</b> Click inside the <b>Gmail 16-Character App Password</b> box above and press <b>Ctrl + V</b> (or right-click ➔ Paste).</li>
                    <li><i>Note: Spaces between the letters are automatically cleaned and handled for you!</i></li>
                </ol>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        btn_submit, btn_demo = st.columns([2, 1])
        with btn_submit:
            submit_login = st.form_submit_button("🚀 Save Profile & Launch BD Job Finder", type="primary", use_container_width=True)
        with btn_demo:
            demo_login = st.form_submit_button("⚡ Demo / Guest Access", use_container_width=True)

    if submit_login:
        clean_pw = app_pw_input.strip().replace(" ", "")
        outbound_email = sender_email_input.strip() if sender_email_input.strip() else email_input.strip()
        if not name_input.strip():
            st.error("Please provide your Full Name to continue.")
        elif not email_input.strip() or "@" not in email_input:
            st.error("Please provide a valid Candidate Email Address. This email will be used as your contact email on applications.")
        elif not outbound_email or "@" not in outbound_email:
            st.error("Please provide a valid Outbound Application Sender Gmail Address.")
        elif not clean_pw:
            st.error("⚠️ Gmail 16-Character App Password is MANDATORY! Without it, the application cannot dispatch emails directly, deep-extract recruiter emails, or approve submissions.")
        elif len(clean_pw) < 16:
            st.error(f"⚠️ Gmail App Password must be 16 characters (currently {len(clean_pw)}). Please copy the exact 16-letter code from Google.")
        else:
            with st.spinner(f"🔒 Connecting to Google SMTP (smtp.gmail.com:587) and authenticating '{outbound_email}'..."):
                is_auth, auth_msg = authenticate_gmail_credentials(outbound_email, clean_pw)

            if not is_auth:
                st.error(f"❌ {auth_msg}")
            else:
                updated_prof = existing_profile or {}
                updated_prof["full_name"] = name_input.strip()
                updated_prof["email"] = email_input.strip()
                updated_prof["phone"] = phone_input.strip()
                updated_prof["target_industry"] = ind_input
                updated_prof["preferred_locations"] = [loc_input]
                updated_prof["linkedin"] = linkedin_input.strip()
                updated_prof["education_summary"] = edu_input.strip()
                updated_prof["skills_summary"] = skills_input.strip()
                if "raw_cv_extracted" in st.session_state:
                    updated_prof["raw_cv_text"] = st.session_state["raw_cv_extracted"]

                # Ensure uploaded CV is permanently designated as the active attachment
                uploaded_resume_name = (
                    st.session_state.get("active_resume_filename") or
                    (login_cv_file.name if login_cv_file else None) or
                    (existing_profile.get("resume_filename") if existing_profile else None)
                )
                if uploaded_resume_name:
                    updated_prof["resume_filename"] = uploaded_resume_name
                elif not updated_prof.get("resume_filename"):
                    def_p = get_default_resume_path()
                    if def_p:
                        updated_prof["resume_filename"] = os.path.basename(def_p)
                
                save_active_profile(updated_prof)
                if updated_prof.get("resume_filename"):
                    set_active_resume_filename(updated_prof["resume_filename"])
                save_credentials(
                    gemini_api_key=gemini_input.strip() or DEFAULT_GEMINI_KEY,
                    sender_email=outbound_email,
                    app_password=clean_pw
                )
                st.session_state.authenticated = True
                st.success(f"🎉 {auth_msg} Welcome, {name_input}! Launching dashboard...")
                st.rerun()

    if demo_login:
        demo_prof = {
            "full_name": "Rahim Ahmed (Demo Candidate)",
            "email": "candidate.demo.bd@gmail.com",
            "phone": "+8801700000000",
            "target_industry": "IT & Software Engineering",
            "target_roles": ["Junior Software Engineer"],
            "preferred_locations": ["Dhaka (Gulshan / Banani / Mohakhali)"],
            "education_summary": "B.Sc in Computer Science & Engineering",
            "skills_summary": "Python, Django, PostgreSQL, REST API, Git, Docker, Problem Solving",
            "raw_cv_text": "Sample CSE Graduate CV with Python and web development competencies."
        }
        save_active_profile(demo_prof)
        save_credentials(gemini_api_key=DEFAULT_GEMINI_KEY, sender_email="candidate.demo.bd@gmail.com")
        st.session_state.authenticated = True
        st.rerun()

    # Stop rendering remainder of dashboard until authenticated
    st.stop()

# Load Authenticated Profile
active_profile = get_active_profile() or {
    "full_name": "Job Seeker",
    "email": "",
    "phone": "",
    "linkedin": "",
    "target_industry": "IT & Software Engineering",
    "target_roles": [],
    "preferred_locations": ["Dhaka (Gulshan / Banani / Mohakhali)"],
    "education_summary": "Bachelor / Master Degree",
    "skills_summary": "Communication, Problem Solving, Analytical Skills",
    "raw_cv_text": ""
}

# Candidate identity signature verification: immediately purges drafts if candidate changes
active_cand_id = active_profile.get("id", 1)
active_cand_sig = (
    f"{active_cand_id}::{active_profile.get('full_name', '')}::{active_profile.get('email', '')}::"
    f"{active_profile.get('phone', '')}::{active_profile.get('resume_filename', '')}::{active_profile.get('skills_summary', '')}"
)

if st.session_state.get("current_active_candidate_sig") != active_cand_sig:
    st.session_state["drafts"] = {}
    for k in list(st.session_state.keys()):
        if any(k.startswith(p) for p in ["subj_", "body_", "sender_", "email_", "proof_"]):
            st.session_state.pop(k, None)
    st.session_state["current_active_candidate_sig"] = active_cand_sig

# Check AI Mode
has_ai_key = bool(get_gemini_client())

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f9/Flag_of_Bangladesh.svg", width=60)
    st.title("BD Job Finder")
    st.caption("Bangladesh Public Employment & Circular Hub")

    # Mode Indicator
    if has_ai_key:
        st.success("✨ **AI Mode Active** (Gemini Vision + Smart Match)")
    else:
        st.info("⚡ **Free Keyless Mode** (Standard search & templates)")

    st.markdown("---")
    
    # Candidate Summary & Switcher
    all_profiles = list_user_profiles()
    st.subheader("👤 Candidate Identity")
    if len(all_profiles) > 1:
        prof_options = {p["id"]: f"{p['full_name']} ({p.get('email', 'No Email')})" for p in all_profiles}
        curr_p_id = active_profile.get("id")
        p_keys = list(prof_options.keys())
        p_idx = p_keys.index(curr_p_id) if curr_p_id in p_keys else 0
        selected_p_id = st.selectbox(
            "Active Candidate Profile",
            options=p_keys,
            format_func=lambda pid: prof_options[pid],
            index=p_idx,
            key="sb_candidate_profile_selector"
        )
        if selected_p_id != curr_p_id:
            set_active_profile_id(selected_p_id)
            st.session_state["drafts"] = {}
            st.session_state["search_results"] = []
            st.session_state["search_has_run"] = False
            for k in list(st.session_state.keys()):
                if any(k.startswith(p) for p in ["subj_", "body_", "sender_", "email_", "proof_"]):
                    st.session_state.pop(k, None)
            st.rerun()

    st.write(f"**{active_profile.get('full_name', 'Not set')}**")
    if active_profile.get("email"):
        st.caption(f"📧 <code>{active_profile['email']}</code>", unsafe_allow_html=True)
    if active_profile.get("phone"):
        st.caption(f"📱 <code>{active_profile['phone']}</code>", unsafe_allow_html=True)
    st.caption(f"🏢 {active_profile.get('target_industry', 'General')}")
    active_cand_creds = get_credentials()
    cand_has_pw = bool(active_cand_creds.get("app_password"))
    if cand_has_pw:
        st.markdown("<span style='font-size: 11px; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 10px; font-weight: 600;'>🟢 In-App SMTP Ready</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='font-size: 11px; background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 10px; font-weight: 600;'>🟡 1-Click Gmail Mode (No App PW)</span>", unsafe_allow_html=True)
    
    col_sw1, col_sw2 = st.columns(2)
    with col_sw1:
        if st.button("🚪 Log Out", use_container_width=True):
            logout_and_wipe_all_user_data()
            st.session_state.clear()
            st.session_state["authenticated"] = False
            st.rerun()
    with col_sw2:
        if st.button("➕ Add User", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state["add_new_candidate"] = True
            st.session_state["drafts"] = {}
            st.session_state["search_results"] = []
            for k in list(st.session_state.keys()):
                if any(k.startswith(p) for p in ["subj_", "body_", "sender_", "email_", "proof_", "login_", "s_email_", "s_name_", "s_pw_"]):
                    st.session_state.pop(k, None)
            st.rerun()
    
    st.markdown("---")

    # ==============================================================================
    # 📄 MASTER RESUME ATTACHMENT (Embedded Viewer matching JobPilot)
    # ==============================================================================
    st.subheader("Master Resume Attachment")
    sidebar_resume_path = get_default_resume_path(active_profile)
    
    if sidebar_resume_path and os.path.exists(sidebar_resume_path):
        st.success(f"Attached:\n\n`{os.path.basename(sidebar_resume_path)}`")
        pdf_b64 = get_pdf_base64(sidebar_resume_path)
        
        with open(sidebar_resume_path, "rb") as f:
            st.download_button(
                label="📥 Download Master Resume",
                data=f.read(),
                file_name=os.path.basename(sidebar_resume_path),
                mime="application/pdf",
                use_container_width=True,
                key="sidebar_download_master_resume"
            )
            
        with st.expander("📄 View Embedded Resume", expanded=True):
            if pdf_b64:
                pdf_html = f'<iframe src="data:application/pdf;base64,{pdf_b64}" width="100%" height="450" type="application/pdf" style="border: 1px solid #cbd5e1; border-radius: 6px;"></iframe>'
                st.markdown(pdf_html, unsafe_allow_html=True)
            else:
                st.caption("Unable to load embedded preview.")
    else:
        st.warning("⚠️ No resume found. Upload your PDF resume in Candidate Profile.")
        
    st.markdown("---")
    
    # Tracker Summary Stats
    st.subheader("📊 Tracker Overview")
    stats = get_application_stats()
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.metric("Applied", stats["Applied"])
        st.metric("Followed Up", stats["Followed Up"])
    with col_s2:
        st.metric("Interviews", stats["Interviews"])
        st.metric("Offers", stats["Offer Received"])
        
    st.markdown("---")
    st.subheader("🛡️ Dispatch Safety Guard")
    dry_run_toggle = st.toggle("Dry-Run Safety Mode", value=st.session_state.get("dry_run_mode", False), help="When enabled, email applications are simulated without sending actual messages.")
    st.session_state["dry_run_mode"] = dry_run_toggle
    if dry_run_toggle:
        st.info("🛡️ Mode: **PREVIEW ONLY**")
    else:
        st.warning("⚡ Mode: **LIVE EMAIL DISPATCH**")

    st.markdown("---")
    st.caption("Developed for all 64 districts in Bangladesh 🇧🇩")

# ==============================================================================
# ZONE 1: TOP RECRUITMENT ANALYTICS & FOLLOW-UP COCKPIT (MATCHING DESKTOP JOBPILOT)
# ==============================================================================
due_followups = stats.get("Due Followups", 0)
applied_count = stats.get("Applied", 0)
followed_up_count = stats.get("Followed Up", 0)
interviews_count = stats.get("Interviews", 0)
offers_count = stats.get("Offer Received", 0)
rejected_count = stats.get("Rejected", 0)

today_str = datetime.now().strftime("%Y-%m-%d")
apps_all = get_applications(status="All")
sent_today = sum(1 for a in apps_all if str(a.get("applied_date", "")).startswith(today_str))
DAILY_LIMIT = 50

# ==============================================================================
# TOP PERSISTENT BRAND BAR (GOOGLE STITCH HEADER)
# ==============================================================================
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 4px 14px 4px; border-bottom: 1.5px solid #e2e8f0; margin-bottom: 14px; flex-wrap: wrap;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 26px;">🇧🇩</span>
        <div>
            <span style="font-size: 20px; font-weight: 800; color: #006a4e; letter-spacing: -0.4px;">BD Job Finder</span>
            <span style="background: #e0f2fe; color: #0369a1; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; margin-left: 6px;">STITCH AI OS</span>
        </div>
        <div style="color: #64748b; font-size: 13px; margin-left: 12px; border-left: 1.5px solid #cbd5e1; padding-left: 12px;">
            🟢 <b>Online:</b> Targeting active circulars & verified direct recruiter routes across Bangladesh
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 10px; margin-top: 4px;">
        <span style="background: #f1f5f9; color: #334155; font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 20px; border: 1px solid #cbd5e1;">
            👤 {active_profile.get('full_name', 'Active Candidate')}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# MAIN NAVIGATION TABS (MATCHING GOOGLE STITCH CANVAS SCREENS)
# ==============================================================================
tab_cockpit, tab_search, tab_tracker, tab_ocr, tab_profile, tab_directory, tab_settings = st.tabs([
    "🏠 Recruitment Cockpit",
    "🔍 Unified Job Search",
    f"📊 Application CRM Tracker ({stats['Total']})",
    "📸 Circular Scanner (OCR)",
    "👤 Candidate Profile & CV",
    "🌐 18+ BD Job Portals Directory",
    "⚙️ Settings & Credentials"
])

# ==============================================================================
# SCREEN 1: 🏠 RECRUITMENT COCKPIT (GOOGLE STITCH SCREEN 1)
# ==============================================================================
with tab_cockpit:
    # 1. Hero Candidate Banner
    resume_file_p = get_default_resume_path()
    res_display_name = os.path.basename(resume_file_p) if resume_file_p else "None Attached"
    
    st.markdown(f"""
    <div class="stitch-hero-banner">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div style="max-width: 76%;">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <h1 style="margin: 0; font-size: 26px; color: #ffffff;">{active_profile.get('full_name', 'Active Candidate')}</h1>
                    <span style="background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); color: #ecfdf5; font-size: 12px; font-weight: 700; padding: 3px 12px; border-radius: 20px;">
                        Target: {active_profile.get('target_industry', 'IT & Software Engineering')} (Senior / Lead)
                    </span>
                </div>
                <p style="margin: 6px 0 0 0; color: #a7f3d0; font-size: 13.5px; line-height: 1.5;">
                    Autonomous telemetry monitoring 18 national job exchanges, autonomous BPSC/BDJobs circular trackers, and verified direct corporate recruitment inboxes across 64 districts nationwide.
                </p>
            </div>
            <div style="text-align: right; margin-top: 6px;">
                <span style="background: #006a4e; color: #ffffff; padding: 4px 12px; border-radius: 14px; font-size: 11.5px; font-weight: 700; display: inline-block;">
                    ✨ AI Match Engine Active
                </span><br/>
                <span style="color: #6ee7b7; font-size: 12px; margin-top: 5px; display: inline-block;">
                    📎 Active CV: <b>{res_display_name}</b>
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Top Analytics Telemetry Grid
    bar_col1, bar_col2, bar_col3, bar_col4 = st.columns([1.2, 1.3, 2.3, 1.2])

    with bar_col1:
        st.metric(
            label="Daily Sent Quota",
            value=f"{sent_today} / {DAILY_LIMIT}",
            delta=f"{max(0, DAILY_LIMIT - sent_today)} remaining today",
            delta_color="normal"
        )
        st.progress(min(1.0, sent_today / max(1, DAILY_LIMIT)))

    with bar_col2:
        badge_label = "🟢 0 Pending" if due_followups == 0 else f"🔔 {due_followups} Due Now!"
        st.metric(
            label="Day-4 Follow-ups Due",
            value=due_followups,
            delta=badge_label,
            delta_color="inverse" if due_followups > 0 else "off"
        )
        if due_followups > 0:
            if st.button("⚡ Dispatch Due Follow-ups", type="primary", use_container_width=True, key="cockpit_dispatch_due"):
                with st.spinner("Executing automated Day-4 follow-up cycle with resume attachments..."):
                    cycle_res = run_followup_cycle(dry_run=st.session_state.get("dry_run_mode", False))
                if cycle_res.get("success"):
                    st.balloons()
                    st.success(cycle_res.get("message"))
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(cycle_res.get("message"))

    with bar_col3:
        st.write("**Pipeline Overview**")
        p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5)
        p_col1.metric("Applied", applied_count)
        p_col2.metric("Followed Up", followed_up_count)
        p_col3.metric("Interviews", interviews_count)
        p_col4.metric("Offers", offers_count)
        p_col5.metric("Rejected", rejected_count)

    with bar_col4:
        st.write("**Safety Dispatch Switch**")
        cockpit_dry_toggle = st.toggle("Dry-Run Safety Mode", value=st.session_state.get("dry_run_mode", False), key="cockpit_dry_toggle", help="When enabled, applications and follow-ups are simulated without sending actual emails.")
        st.session_state["dry_run_mode"] = cockpit_dry_toggle
        if cockpit_dry_toggle:
            st.info("🛡️ Mode: **PREVIEW ONLY**")
        else:
            st.warning("⚡ Mode: **LIVE EMAIL DISPATCH**")

    # 3. Four Feature Launchers (matching Google Stitch Screen 1 Row 2)
    st.markdown("""
    <div style="margin: 14px 0 10px 0;">
        <span style="font-size: 13px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Core Engine Launchers</span>
    </div>
    """, unsafe_allow_html=True)
    
    l_c1, l_c2, l_c3, l_c4 = st.columns(4)
    with l_c1:
        st.markdown("""
        <div class="stitch-launcher-card" style="border-top: 3px solid #006a4e;">
            <div style="font-size: 24px; margin-bottom: 4px;">🔍</div>
            <div style="font-weight: 700; font-size: 14px; color: #0f172a;">Unified Job Search</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 2px;">Multi-portal live scraper across BDJobs, AllJobs & Portals</div>
        </div>
        """, unsafe_allow_html=True)
    with l_c2:
        st.markdown("""
        <div class="stitch-launcher-card" style="border-top: 3px solid #0284c7;">
            <div style="font-size: 24px; margin-bottom: 4px;">🌐</div>
            <div style="font-weight: 700; font-size: 14px; color: #0f172a;">Multi-Portal Sync</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 2px;">18+ automated Bangladesh portals & carrier gateways</div>
        </div>
        """, unsafe_allow_html=True)
    with l_c3:
        st.markdown("""
        <div class="stitch-launcher-card" style="border-top: 3px solid #7c3aed;">
            <div style="font-size: 24px; margin-bottom: 4px;">📸</div>
            <div style="font-weight: 700; font-size: 14px; color: #0f172a;">Circular OCR Flyer</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 2px;">Gemini Vision multimodal parser for Bangla & English flyers</div>
        </div>
        """, unsafe_allow_html=True)
    with l_c4:
        st.markdown("""
        <div class="stitch-launcher-card" style="border-top: 3px solid #e11d48;">
            <div style="font-size: 24px; margin-bottom: 4px;">📊</div>
            <div style="font-weight: 700; font-size: 14px; color: #0f172a;">Intelligence CRM Ledger</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 2px;">Crash-proof application tracking, follow-ups & interview radar</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 4. Main 2-Column Cockpit Workspace (matching Google Stitch Screen 1 Row 3)
    c_left, c_right = st.columns([1.7, 1.1])

    with c_left:
        # Card 1: Autonomous Recruiter Polling Telemetry
        st.markdown("""
        <div class="stitch-card">
            <div class="stitch-card-header">
                <div>
                    <span style="font-size: 16px;">📡 Autonomous Recruiter Polling Telemetry</span>
                    <span style="background: #ecfdf5; color: #059669; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; border: 1px solid #a7f3d0; margin-left: 6px;">
                        LIVE CHANNELS
                    </span>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <b style="color: #0f172a; font-size: 13.5px;">BPSC Govt Public Sector Sync</b>
                        <div style="font-size: 12px; color: #64748b;">AllJobs Teletalk & Non-Cadre Gazette Tracker</div>
                    </div>
                    <span style="background: #dbeafe; color: #1e40af; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;">Crawled 15m ago</span>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <b style="color: #0f172a; font-size: 13.5px;">Walton Enterprise Lead Recruiter Contact</b>
                        <div style="font-size: 12px; color: #64748b;">Direct Corporate Route: <code>career@waltonbd.com</code></div>
                    </div>
                    <span style="background: #dcfce7; color: #166534; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;">Email Verified</span>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <b style="color: #0f172a; font-size: 13.5px;">Pathao / Foodpanda Tech Lead Recruiter</b>
                        <div style="font-size: 12px; color: #64748b;">Supply Chain, Operations & Engineering Radar</div>
                    </div>
                    <span style="background: #dcfce7; color: #166534; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;">Active Route</span>
                </div>
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <b style="color: #0f172a; font-size: 13.5px;">Brain Station 23 / Enosis Solutions</b>
                        <div style="font-size: 12px; color: #64748b;">Software Export & Enterprise Cloud Systems</div>
                    </div>
                    <span style="background: #dcfce7; color: #166534; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;">Direct HR Open</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card 2: Urgent Recruiter Follow-ups Queue (Day 4 Cycle)
        cockpit_due_list = get_due_followups()
        st.markdown(f"""
        <div class="stitch-card">
            <div class="stitch-card-header">
                <div>
                    <span style="font-size: 16px;">🔔 Urgent Recruiter Follow-ups Queue (Day 4 Cycle)</span>
                    <span style="background: {'#fee2e2' if cockpit_due_list else '#ecfdf5'}; color: {'#991b1b' if cockpit_due_list else '#047857'}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; margin-left: 6px;">
                        {len(cockpit_due_list)} PENDING
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if cockpit_due_list:
            for d_app in cockpit_due_list[:4]:
                da_id = d_app["id"]
                st.markdown(f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 3.5px solid #e11d48; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <b style="font-size: 14px; color: #0f172a;">{d_app['job_title']}</b>
                            <div style="font-size: 12px; color: #006a4e; font-weight: 600;">{d_app['company']} &nbsp;•&nbsp; 📍 {d_app.get('location', 'Dhaka')}</div>
                            <div style="font-size: 11.5px; color: #64748b; margin-top: 2px;">Applied: {d_app.get('applied_date', 'Earlier')} &nbsp;|&nbsp; Recipient: <code>{d_app.get('hr_email') or 'Portal'}</code></div>
                        </div>
                        <div>
                            <span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 6px; font-size: 11.5px; font-weight: 700;">
                                {d_app.get('days_pending', 4)} Days Ago
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                cd_c1, cd_c2 = st.columns([1, 1])
                with cd_c1:
                    is_c_prev = st.session_state.get(f"cockpit_prev_{da_id}", False)
                    btn_txt = "✖️ Close" if is_c_prev else "👁️ Preview Pitch & Send"
                    if st.button(btn_txt, key=f"c_prev_btn_{da_id}", use_container_width=True):
                        st.session_state[f"cockpit_prev_{da_id}"] = not is_c_prev
                        st.rerun()
                with cd_c2:
                    if st.button("✅ Mark Followed Up", key=f"c_mark_btn_{da_id}", use_container_width=True):
                        mark_followed_up(da_id, notes="Marked followed up from Cockpit")
                        st.success(f"Updated {d_app['company']} to Followed Up!")
                        st.rerun()

                if st.session_state.get(f"cockpit_prev_{da_id}", False):
                    p_lang = st.radio("Language", ["English", "Bangla (বাংলা)"], horizontal=True, key=f"c_lang_{da_id}")
                    f_pitch = generate_followup_pitch(d_app, active_profile, language="Bangla" if "Bangla" in p_lang else "English")
                    c_f_to = st.text_input("HR Email", value=d_app.get("hr_email") or "", key=f"c_to_{da_id}")
                    c_f_body = st.text_area("Follow-up Message", value=f_pitch["body"], height=120, key=f"c_body_{da_id}")
                    
                    if c_f_to and "@" in c_f_to:
                        c_compose_url = generate_gmail_compose_url(c_f_to, f_pitch["subject"], c_f_body)
                        st.link_button("🚀 Open in My Gmail ➔", c_compose_url, type="primary", use_container_width=True)
        else:
            st.markdown("""
            <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 12px 14px;">
                <span style="color: #15803d; font-weight: 600;">🟢 0 Urgent Follow-ups:</span>
                <span style="color: #166534; font-size: 13px;"> All applications are within the 4-day grace window. System is actively monitoring deadlines.</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        # Card 1: Master Resume Attachment Card
        cockpit_res_p = get_default_resume_path()
        cockpit_res_name = os.path.basename(cockpit_res_p) if cockpit_res_p else "No CV Uploaded"
        cockpit_res_size = round(os.path.getsize(cockpit_res_p) / 1024, 1) if (cockpit_res_p and os.path.exists(cockpit_res_p)) else 0
        
        st.markdown(f"""
        <div class="stitch-card">
            <div class="stitch-card-header">
                <div>
                    <span style="font-size: 16px;">📎 Master Resume & ATS</span>
                </div>
                <span style="background: #ecfdf5; color: #047857; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;">
                    {cockpit_res_size} KB
                </span>
            </div>
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                <div style="font-weight: 700; color: #0f172a; font-size: 13px; word-break: break-all;">
                    📄 {cockpit_res_name}
                </div>
                <div style="font-size: 11.5px; color: #16a34a; font-weight: 600; margin-top: 2px;">
                    🟢 Pre-attached to all Outbound Emails & Playwright ATS Autopilot
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if cockpit_res_p and os.path.exists(cockpit_res_p):
            with open(cockpit_res_p, "rb") as f:
                st.download_button(
                    label="📥 Download Master Resume",
                    data=f.read(),
                    file_name=cockpit_res_name,
                    mime="application/pdf",
                    use_container_width=True,
                    key="cockpit_download_cv"
                )
            pdf_b64_c = get_pdf_base64(cockpit_res_p)
            with st.expander("👁️ View Embedded Resume Preview", expanded=False):
                if pdf_b64_c:
                    st.markdown(f'<iframe src="data:application/pdf;base64,{pdf_b64_c}#toolbar=0" width="100%" height="360" style="border: 1px solid #cbd5e1; border-radius: 6px;" type="application/pdf"></iframe>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Card 2: Upcoming Interviews Radar
        cockpit_interviews = get_interview_opportunities()
        st.markdown(f"""
        <div class="stitch-card">
            <div class="stitch-card-header">
                <div>
                    <span style="font-size: 16px;">🎉 Upcoming Interviews Radar</span>
                    <span style="background: #dcfce7; color: #15803d; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; margin-left: 6px;">
                        {len(cockpit_interviews)} ACTIVE
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if cockpit_interviews:
            for ci_app in cockpit_interviews[:3]:
                st.markdown(f"""
                <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <b style="color: #166534; font-size: 13.5px;">{ci_app['job_title']}</b>
                    <div style="color: #006a4e; font-weight: 600; font-size: 12px;">{ci_app['company']} &nbsp;•&nbsp; 📍 {ci_app.get('location', 'Dhaka')}</div>
                    <div style="font-size: 11.5px; color: #475569; margin-top: 3px;">
                        🎯 <b>Round:</b> {ci_app.get('interview_type') or 'Technical Screening'}<br/>
                        📅 <b>Date:</b> {ci_app.get('interview_date') or 'Pending Schedule'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if ci_app.get("meeting_link"):
                    m_lnk = ci_app["meeting_link"]
                    if not m_lnk.startswith("http"):
                        m_lnk = f"https://{m_lnk}"
                    st.link_button("🌐 Join Video Meeting (Google Meet)", m_lnk, type="primary", use_container_width=True, key=f"c_join_{ci_app['id']}")
        else:
            st.markdown("""
            <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 12px; text-align: center; color: #64748b; font-size: 12.5px;">
                No interviews scheduled yet. As recruiters respond to your cold applications and ATS submissions, interview dates and Google Meet links will appear here.
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==============================================================================
# SCREEN 2: 🔍 UNIFIED JOB SEARCH (GOOGLE STITCH SCREEN 2)
# ==============================================================================
with tab_search:
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Bangladesh Unified Job Search</h1>
        <p>Search across BDJobs, AllJobs Teletalk, Skill.jobs, Careerjet, and leading employers nationwide.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🎯 Filter by Industry, Title, District & Portal", expanded=True):
        col1, col2, col3 = st.columns([1.5, 1.5, 1.2])
        
        with col1:
            industry_options = list(BD_JOB_TAXONOMY.keys())
            default_ind_idx = industry_options.index(active_profile.get("target_industry")) if active_profile.get("target_industry") in industry_options else 0
            selected_industry = st.selectbox("Industry Sector (শিল্প খাত)", industry_options, index=default_ind_idx)
            
            roles_in_industry = BD_JOB_TAXONOMY.get(selected_industry, [])
            selected_role = st.selectbox("Standard Job Title (পদের নাম)", roles_in_industry)
            
        with col2:
            custom_keyword = st.text_input("Custom Keyword or Skill (ঐচ্ছিক কিওয়ার্ড)", placeholder="e.g. Django, Merchandiser, Branch Manager")
            
            district_list = ["All Districts (সমগ্র বাংলাদেশ)"] + get_all_districts()
            selected_district = st.selectbox("Location / District (জেলা / অঞ্চল)", district_list)
            
        with col3:
            portal_choices = [
                "All Portals",
                "Careerjet Bangladesh",
                "Facebook Jobs",
                "Instagram Hiring",
                "LinkedIn Jobs",
                "Skill Jobs",
                "Nextjobz",
                "eJobs Bangladesh",
                "BDJobs Live",
                "BDJobs"
            ] + [p["name"] for p in BD_JOB_PORTALS.values() if p["name"] not in [
                "Careerjet Bangladesh", "Skill Jobs", "BDJobs", "Nextjobz", "LinkedIn Jobs", "Facebook Jobs"
            ]]
            selected_portal = st.selectbox("Search Source Portal (উৎস পোর্টাল)", portal_choices, index=0)
            batch_limit = st.slider("Results Limit (ফলাফলের সংখ্যা)", 5, 25, 8)

        search_est_portal = get_estimated_search_metrics(source="portals", portal_filter=selected_portal, batch_size=batch_limit)
        search_est_ai = get_estimated_search_metrics(source="ai", portal_filter=selected_portal, batch_size=batch_limit)

        st.info(
            f"⏱️ **Estimated Search Time:** **{search_est_portal['range_label']}** for Live Multi-Portal Crawling "
            f"({search_est_portal['phase_summary']}) | **{search_est_ai['range_label']}** for AI Strategic Discovery"
        )
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            scour_btn = st.button("🌐 Scour Live Job Portals (Real-Time)", type="primary", use_container_width=True)
        with btn_col2:
            ai_btn = st.button("🤖 AI Strategic Target Discovery", use_container_width=True)

    query_term = custom_keyword.strip() if custom_keyword.strip() else (selected_role if not selected_role.startswith("All ") else "")
    loc_term = selected_district.split(" ")[0] if "All" not in selected_district else "Dhaka"

    # Execute Search via Live Scour
    if scour_btn:
        crawl_start_time = time.time()
        with st.status(f"🌐 Scouring Bangladesh Job Portals for '{query_term or selected_industry}'...", expanded=True) as status:
            st.write(f"📡 **Step 1/3:** Scouring live vacancies across {selected_portal} in {selected_district}...")
            results = search_bangladesh_jobs(
                query=query_term,
                industry=selected_industry,
                district=loc_term if "All" not in selected_district else "All",
                portal_filter=selected_portal,
                limit=batch_limit
            )
            st.write(f"   ↳ Scraped **{len(results)}** active vacancy announcements.")
            
            st.write(f"🔓 **Step 2/3:** Deep-extracting corporate HR emails & direct apply links...")
            emails_resolved = sum(1 for t in results if t.get("hr_email"))
            st.write(f"   ↳ Resolved **{emails_resolved}/{len(results)}** verified contact channels!")
            
            st.write(f"✍️ **Step 3/3:** Synthesizing ATS match scores & tailored pitch drafts...")
            st.session_state["search_has_run"] = True
            st.session_state.search_results = results
            elapsed_sec = round(time.time() - crawl_start_time, 1)
            status.update(
                label=f"✅ Portal Scour complete in {elapsed_sec}s! Found {len(results)} opportunities ({emails_resolved} direct inboxes).",
                state="complete",
                expanded=False
            )
        st.rerun()

    # Execute Search via AI Strategic Target Discovery
    if ai_btn:
        ai_start_time = time.time()
        with st.status(f"🤖 Discovering Strategic Targets with Gemini AI...", expanded=True) as status:
            st.write(f"🏢 **Step 1/3:** Querying corporate hiring intelligence across {selected_district} for {selected_industry}...")
            results = discover_ai_strategic_targets(
                candidate_profile=active_profile,
                limit=batch_limit,
                industry=selected_industry,
                locations=[selected_district]
            )
            st.write(f"   ↳ Discovered **{len(results)}** verified corporate leads matching profile competencies.")
            
            st.write(f"🔓 **Step 2/3:** Matching verified corporate recruitment inboxes...")
            emails_resolved = sum(1 for t in results if t.get("hr_email"))
            st.write(f"   ↳ Resolved **{emails_resolved}/{len(results)}** corporate HR inboxes!")
            
            st.write(f"✍️ **Step 3/3:** Synthesizing personalized application pitches for {active_profile.get('full_name', 'candidate')}...")
            st.session_state["search_has_run"] = True
            st.session_state.search_results = results
            elapsed_sec = round(time.time() - ai_start_time, 1)
            status.update(
                label=f"✅ AI Discovery complete in {elapsed_sec}s! Found {len(results)} targets ({emails_resolved} direct inboxes).",
                state="complete",
                expanded=False
            )
        st.rerun()

    # Render Results according to filters
    has_searched = st.session_state.get("search_has_run", False)
    result_count = len(st.session_state.search_results)
    
    st.subheader(f"📋 Verified Opportunities ({result_count} Available)")
    
    if not st.session_state.search_results:
        if has_searched:
            st.info("🔍 No vacancies found matching your specific filter criteria. As requested, the results area is left blank. You can broaden your keywords or select 'All Districts'.")
        else:
            st.markdown("""
            <div style="background: #f8fafc; border: 1.5px dashed #cbd5e1; border-radius: 10px; padding: 28px 20px; text-align: center; margin: 12px 0;">
                <span style="font-size: 28px;">🎯</span>
                <div style="font-weight: 700; font-size: 15px; color: #1e293b; margin-top: 6px;">Filters Ready for Targeted Job Search</div>
                <div style="font-size: 13px; color: #64748b; margin-top: 4px;">
                    Select your Industry Sector, Job Title, District, and Portal above, then click <b>🌐 Scour Live Job Portals</b> or <b>🤖 AI Strategic Target Discovery</b> to display matching opportunities.
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        if "drafts" not in st.session_state:
            st.session_state["drafts"] = {}

        candidate_cv_text = active_profile.get("raw_cv_text") or active_profile.get("skills_summary", "")

        # 1. Pre-calculate Trajectory Fit Score & Salary for un-scored live opportunities
        for job in st.session_state.search_results:
            if "trajectory_score" not in job:
                # Fast heuristic trajectory score matching candidate skills
                sk = candidate_cv_text.lower()
                jt = job.get("job_title", "").lower()
                base_s = 75
                if any(w in jt for w in ["lead", "senior", "architect"]):
                    base_s += 12
                if any(w in sk for w in ["python", "software", "engineer", "lead"]):
                    base_s += 8
                job["trajectory_score"] = min(98, base_s)

            if "salary_info" not in job:
                sal_res = resolve_job_salary(job, default_industry=selected_industry)
                job["salary_info"] = sal_res
                job["salary"] = sal_res.get("display", "Negotiable")

        # 2. STRICT SORT: HIGHEST TRAJECTORY FIRST ➔ LOWEST TRAJECTORY FIT
        st.session_state.search_results.sort(
            key=lambda j: j.get("trajectory_score", 0),
            reverse=True
        )

        top_score = st.session_state.search_results[0].get("trajectory_score", 0) if st.session_state.search_results else 0
        min_score = st.session_state.search_results[-1].get("trajectory_score", 0) if st.session_state.search_results else 0

        exact_count = sum(1 for j in st.session_state.search_results if j.get("salary_info", {}).get("is_exact_company"))
        expected_count = len(st.session_state.search_results) - exact_count

        # Trajectory Fit Ranking Banner
        st.markdown(f"""
        <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 10px 16px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">📈</span>
                <span style="font-weight: 700; font-size: 14px; color: #166534;">
                    Ranked by Trajectory Fit: <b>Highest Trajectory First ({top_score}%) ➔ Lowest Fit ({min_score}%)</b>
                </span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 600;">
                <span style="color: #065f46; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 3px 8px; border-radius: 4px;">
                    🏢 {exact_count} Exact Company Offered
                </span>
                <span style="color: #92400e; background: #fefce8; border: 1px solid #fef08a; padding: 3px 8px; border-radius: 4px;">
                    🇧🇩 {expected_count} Expected (BD Context)
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for idx, job in enumerate(list(st.session_state.search_results)):
            tid = f"target_{idx}_{abs(hash(job.get('company', '') + job.get('job_title', ''))) % 1000000}"
            job["_id"] = tid
            score = job.get("trajectory_score", 50)
            sal_info = job.get("salary_info") or resolve_job_salary(job, default_industry=selected_industry)
            is_exact = sal_info.get("is_exact_company", False)
            sal_disp = sal_info.get("display", "Negotiable")
            sal_badge = sal_info.get("badge", "Expected Salary (BD Context)")
            rank_num = idx + 1
            rank_badge_text = f"#{rank_num} Highest Trajectory Fit" if rank_num == 1 else f"#{rank_num} Trajectory Fit"

            cand_id = active_profile.get("id", 1)
            draft_key = f"c_{cand_id}_{tid}"

            # Initialize candidate-tailored draft pitch if not present
            if draft_key not in st.session_state["drafts"]:
                initial_lang = job.get("language", "English")
                cand_name = active_profile.get("full_name", "Job Seeker")
                cand_phone = active_profile.get("phone", "")
                cand_email = active_profile.get("email", "")
                cand_edu = active_profile.get("education_summary", "")
                cand_skills = active_profile.get("skills_summary") or active_profile.get("target_industry") or "Communication, Leadership, Problem Solving"
                cand_ind = active_profile.get("target_industry", "the industry")
                cand_res_p = get_default_resume_path(active_profile)
                cand_res_name = os.path.basename(cand_res_p) if cand_res_p else (active_profile.get("resume_filename") or "Master_Resume.pdf")

                if initial_lang == "Bangla":
                    p_subj = f"আবেদনপত্র: {job.get('job_title', 'পদ')} — {cand_name}"
                    p_body = (
                        f"সম্মানিত নিয়োগকারী কর্তৃপক্ষ ({job.get('company')}),\n\n"
                        f"আমি আপনার প্রতিষ্ঠানে সম্প্রতি প্রকাশিত \"{job.get('job_title')}\" পদে অত্যন্ত আগ্রহের সাথে আবেদন করছি।\n\n"
                        f"{cand_edu}-এ আমার শিক্ষাগত যোগ্যতা এবং {cand_skills}-এ বিশেষ দক্ষতা উক্ত পদের দায়িত্বসমূহ নিষ্ঠা ও পেশাদারিত্বের সাথে পালনে কার্যকর ভূমিকা রাখবে বলে আমি বিশ্বাস করি। {cand_name} হিসেবে সততা ও অধ্যাবসায়ের সাথে আমি আপনার প্রতিষ্ঠানের অগ্রযাত্রায় সরাসরি অবদান রাখতে প্রস্তুত।\n\n"
                        f"আমার পূর্ণাঙ্গ জীবনবৃত্তান্ত ({cand_res_name}) এই পত্রের সাথে সংযুক্ত করা হলো। একটি সাক্ষাৎকারের মাধ্যমে আমার অভিজ্ঞতা বিস্তারিত তুলে ধরার সুযোগ প্রত্যাশা করছি।\n\n"
                        f"বিনীত,\n"
                        f"{cand_name}\n"
                        f"মোবাইল: {cand_phone}\n"
                        f"ইমেইল: {cand_email}"
                    )
                else:
                    p_subj = f"Application: {job.get('job_title', 'Position')} — {cand_name}"
                    p_body = (
                        f"Dear Hiring Team at {job.get('company')},\n\n"
                        f"I am writing to express my strong enthusiasm for the {job.get('job_title')} position currently available at {job.get('company')}.\n\n"
                        f"With my academic background in {cand_edu} and proven competencies in {cand_skills}, I am well-prepared to contribute immediately to your team's objectives. As a dedicated professional in {cand_ind}, I look forward to applying my problem-solving abilities and strategic thinking to deliver high-impact results.\n\n"
                        f"Please find my master resume ({cand_res_name}) attached for your review. I would welcome the opportunity to discuss how my qualifications align with {job.get('company')}'s goals during an interview.\n\n"
                        f"Sincerely,\n"
                        f"{cand_name}\n"
                        f"Phone: {cand_phone}\n"
                        f"Email: {cand_email}"
                    )

                st.session_state["drafts"][draft_key] = {
                    "subject": p_subj,
                    "body": p_body,
                    "hr_email": job.get("hr_email", ""),
                    "language": initial_lang
                }

            draft_info = st.session_state["drafts"][draft_key]
            current_subject = draft_info.get("subject", f"Application: {job['job_title']} — {active_profile.get('full_name', 'Job Seeker')}")
            current_body = draft_info.get("body", "")
            current_email = draft_info.get("hr_email", job.get("hr_email", ""))
            
            portal_url = job.get("portal_url") or job.get("apply_url") or job.get("website") or ""
            is_portal_required = job.get("is_portal_required", False) or (not current_email and bool(portal_url))
            is_site_form = job.get("is_site_form", False) or bool(job.get("site_form"))
            site_form_info = job.get("site_form")

            with st.container(border=True):
                # 1. Header & Relevance Metric
                head_col1, head_col2 = st.columns([3, 1])
                with head_col1:
                    st.markdown(f"### **{job['job_title']}** — <span style='color: #22c55e; font-weight: 700;'>{job['company']}</span>", unsafe_allow_html=True)
                    
                    # Prominent Salary & Trajectory Badges
                    sal_bg = "#ecfdf5" if is_exact else "#fffbeb"
                    sal_border = "#10b981" if is_exact else "#f59e0b"
                    sal_color = "#065f46" if is_exact else "#92400e"

                    badge_bg = "#f0fdf4" if is_exact else "#fef3c7"
                    badge_border = "#86efac" if is_exact else "#fcd34d"
                    badge_color = "#15803d" if is_exact else "#b45309"

                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 4px 0 10px 0;">
                        <span style="background: {sal_bg}; border: 1px solid {sal_border}; color: {sal_color}; font-weight: 700; font-size: 13px; padding: 4px 10px; border-radius: 6px;">
                            💰 {sal_disp}
                        </span>
                        <span style="background: {badge_bg}; border: 1px solid {badge_border}; color: {badge_color}; font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 6px;">
                            {sal_badge}
                        </span>
                        <span style="background: #eff6ff; border: 1px solid #93c5fd; color: #1d4ed8; font-size: 11px; font-weight: 700; padding: 4px 8px; border-radius: 6px;">
                            🏆 {rank_badge_text}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                    source_badge = job.get("source_portal", "BDJobs")
                    icon_badge = "✈️ " if "careerjet" in source_badge.lower() else ("📘 " if "facebook" in source_badge.lower() else ("📸 " if "instagram" in source_badge.lower() else ("💼 " if "linkedin" in source_badge.lower() else "📡 ")))
                    role_scope = job.get("job_desc") or f"Verified corporate circular tracked on {source_badge} for {job['job_title']} at {job['company']}."
                    st.caption(f"{icon_badge}Tracked via: **{source_badge}** | 🏢 Role Scope: {role_scope[:130]}...")

                    if is_exact:
                        st.caption(f"🏢 *Exact salary specified on website by company:* `{sal_info.get('website_stated', sal_disp)}`")
                    else:
                        st.caption(f"🇧🇩 *Company did not offer any salary range on circular ({sal_info.get('website_stated', 'Negotiable')}). Expected salary calculated according to Bangladesh employment context.*")
                with head_col2:
                    match_delta = "🎯 High Alignment" if score >= 85 else ("✨ Solid Match" if score >= 75 else ("↑ Trajectory Fit" if score >= 60 else "↔ Standard Fit"))
                    st.metric("Profile Match", f"{score}%", delta=match_delta)
                    st.caption(f"💵 **{sal_info.get('short', sal_disp)}**")

                # 2. Status Banners
                if is_site_form:
                    form_link = site_form_info.get("form_page", job.get("website", "")) if site_form_info else job.get("website", "")
                    st.info(
                        f"🌐 **Official Company Web Form Detected**: `{form_link}`\n\n"
                        f"✨ Applications submitted here trigger an internal server-side email to corporate leadership. This bypasses external cold email bounce issues!"
                    )
                elif current_email:
                    ext_source = job.get("extraction_source", "Verified Corporate Registry")
                    st.success(
                        f"🔓 **Verified Corporate HR Destination**: `{current_email}`\n\n"
                        f"✨ Extracted via: *{ext_source}* — **Bypassed Portal Login Requirement!** You can dispatch directly to this recruiter inbox without signing into any job portal."
                    )
                elif is_portal_required:
                    st.warning(
                        f"⚠️ **Mandatory ATS Portal Employer**: `{job['company']}` strictly manages recruitment via its own ATS portal ({portal_url}). Unsolicited cold emails are rejected. Use **ATS Autopilot** below to apply directly."
                    )

                # Strict Anti-Duplicate Ledger Verification
                is_dup, dup_msg, dup_date, dup_status = check_duplicate_application(
                    company=job.get("company", ""),
                    title=job.get("job_title", ""),
                    email=current_email
                )

                if is_dup:
                    st.error(
                        f"🛑 **APPLICATION ALREADY DISPATCHED (DUPLICATE PROTECTED)**\n\n"
                        f"{dup_msg}\n\n"
                        f"📅 **First Dispatched:** `{dup_date}` | 🏷️ **CRM Status:** `{dup_status}`\n\n"
                        f"🔒 *Dispatch is locked by default to prevent sending duplicate applications to this employer.*"
                    )

                # 3. Two-Column Application Cockpit
                card_left, card_right = st.columns([2.2, 1])

                with card_left:
                    cand_resume_p = get_default_resume_path(active_profile)
                    cand_res_disp = os.path.basename(cand_resume_p) if cand_resume_p else (active_profile.get("resume_filename") or "None")
                    
                    # Prominent Applicant Identity Bar
                    st.markdown(f"""
                    <div style="background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 12px; margin-bottom: 10px; font-size: 13px;">
                        <span style="font-weight: 700; color: #0f172a;">👤 Applicant:</span> <b style="color: #00563f;">{active_profile.get('full_name')}</b> &nbsp;|&nbsp;
                        <span style="font-weight: 700; color: #0f172a;">📱 Phone:</span> <code style="color: #0369a1;">{active_profile.get('phone')}</code> &nbsp;|&nbsp;
                        <span style="font-weight: 700; color: #0f172a;">📧 Email:</span> <code style="color: #0369a1;">{active_profile.get('email')}</code> &nbsp;|&nbsp;
                        <span style="font-weight: 700; color: #0f172a;">📎 Attached CV:</span> <code>{cand_res_disp}</code>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("**✉️ Cold Outreach Email Preview & Editor**")
                    if draft_info.get("language") == "Bangla" or "বাংলা" in current_subject:
                        st.info("🇧🇩 **বাংলা আবেদন (Bangla Application)**: সার্কুলারটি বাংলায় শনাক্ত হওয়ায় আবেদনপত্র ও বিষয় প্রমিত বাংলায় প্রস্তুত করা হয়েছে।")

                    if job.get("circular_image_path") and os.path.exists(job["circular_image_path"]):
                        with st.expander("🖼️ View Original Scanned Brochure / Flyer", expanded=False):
                            st.image(job["circular_image_path"], caption=f"Circular Flyer: {job['company']} - {job['job_title']}")

                    edit_subject = st.text_input("Subject Line", value=current_subject, key=f"subj_{cand_id}_{tid}")
                    edit_email = st.text_input("Target HR Destination", value=current_email, key=f"email_{cand_id}_{tid}", placeholder="Direct corporate HR email (e.g. career@company.com)")
                    
                    cand_default_sender = (active_profile.get("email") or creds.get("sender_email") or "").strip()
                    with st.expander("📤 Outbound Application Sender (Editable)", expanded=False):
                        edit_sender = st.text_input(
                            "Sender Email Account",
                            value=cand_default_sender,
                            key=f"sender_{cand_id}_{tid}",
                            help=f"The authenticated Gmail account used to dispatch this application. Defaults to the email in Active Candidate Profile ({active_profile.get('email', '')}). Can be edited if desired."
                        )

                    edit_body = st.text_area("Email Body", value=current_body, height=180, key=f"body_{cand_id}_{tid}")

                    # Sync state
                    st.session_state["drafts"][draft_key]["subject"] = edit_subject
                    st.session_state["drafts"][draft_key]["body"] = edit_body
                    st.session_state["drafts"][draft_key]["hr_email"] = edit_email

                with card_right:
                    st.markdown("**⚡ 1-Click Direct Application**")
                    st.write("")

                    master_resume_path = get_default_resume_path(active_profile)
                    resume_disp_name = os.path.basename(master_resume_path) if master_resume_path else "None"
                    if master_resume_path and os.path.exists(master_resume_path):
                        st.markdown(f"<div style='font-size: 12px; background: #ecfdf5; border: 1px solid #10b981; border-radius: 6px; padding: 5px 8px; margin-bottom: 8px; color: #065f46;'>📎 <b>Attached CV:</b> <code>{resume_disp_name}</code><br/><span style='font-size: 11px; color: #047857;'>✓ Auto-attached from {active_profile.get('full_name')} CV</span></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size: 12px; background: #fff1f2; border: 1px solid #f43f5e; border-radius: 6px; padding: 5px 8px; margin-bottom: 8px; color: #9f1239;'>⚠️ <b>No CV Attached:</b> Upload resume in Candidate Profile</div>", unsafe_allow_html=True)

                    # Primary Action: Run ATS Form Autopilot (Playwright)
                    if is_portal_required or portal_url:
                        if st.button("🔴 Run ATS Form Autopilot (Playwright)", key=f"btn_ats_{cand_id}_{tid}", type="primary", use_container_width=True):
                            with st.spinner(f"🤖 Dispatching Autonomous ATS Agent to apply on {job.get('company')} portal..."):
                                cand_locs = active_profile.get("preferred_locations", [])
                                cand_address = cand_locs[0] if cand_locs else "Dhaka, Bangladesh"
                                ats_res = launch_ats_autopilot_session(
                                    portal_url=portal_url,
                                    candidate_name=active_profile.get("full_name", "Candidate"),
                                    candidate_email=active_profile.get("email", ""),
                                    candidate_phone=active_profile.get("phone", ""),
                                    candidate_address=cand_address,
                                    candidate_linkedin=active_profile.get("linkedin", ""),
                                    job_title=job.get("job_title", ""),
                                    company=job.get("company", ""),
                                    cover_letter=edit_body,
                                    resume_path=master_resume_path,
                                    candidate_profile=active_profile,
                                    headless=True
                                )
                                shot = ats_res.get("screenshot")
                                if shot:
                                    st.session_state[f"proof_{tid}"] = shot

                                # Log to SQLite CRM with guaranteed screenshot proof
                                job_app_record = dict(job)
                                job_app_record["status"] = "Applied via ATS Autopilot"
                                job_app_record["application_mode"] = "ATS Autopilot (Playwright)"
                                job_app_record["match_score"] = score
                                job_app_record["applied_date"] = time.strftime("%Y-%m-%d")
                                job_app_record["screenshot_path"] = shot or ""
                                job_app_record["notes"] = f"Autonomous ATS Agent applied on {portal_url}. {ats_res.get('message', '')} Screenshot: {shot}"
                                add_application(job_app_record)

                                if ats_res.get("success"):
                                    st.balloons()
                                    st.success(f"🎉 {ats_res.get('message')}")
                                else:
                                    st.warning(f"ATS notice: {ats_res.get('message')}")
                                st.rerun()

                    # Primary Action: Direct Email Dispatch (if HR email is available)
                    if current_email:
                        force_resend = False
                        if is_dup:
                            force_resend = st.checkbox("⚠️ Force Re-send Application", key=f"force_{cand_id}_{tid}", value=False)

                        out_disp = edit_sender.strip() if 'edit_sender' in locals() and edit_sender.strip() else cand_default_sender
                        st.caption(f"📤 Outbound Sender: **{out_disp}**")

                        send_label = "🧪 Preview & Simulate" if st.session_state.get("dry_run_mode", False) else "🚀 Approve & Dispatch to HR"
                        if st.button(send_label, key=f"send_btn_{cand_id}_{tid}", type="primary" if not is_portal_required else "secondary", use_container_width=True):
                            if is_dup and not force_resend:
                                st.error(f"❌ Dispatch locked: Already sent on {dup_date}.")
                            else:
                                with st.spinner(f"Dispatching directly to {edit_email} from {out_disp}..."):
                                    res = dispatch_application_email(
                                        recipient_email=edit_email,
                                        subject=edit_subject,
                                        body=edit_body,
                                        attachment_path=master_resume_path,
                                        sender_email=out_disp,
                                        company=job.get("company", ""),
                                        title=job.get("job_title", ""),
                                        allow_duplicate=force_resend,
                                        dry_run=st.session_state.get("dry_run_mode", False)
                                    )
                                    if res.get("success"):
                                        job_app_record = dict(job)
                                        job_app_record["status"] = "Applied"
                                        job_app_record["hr_email"] = edit_email
                                        job_app_record["application_mode"] = f"SMTP ({out_disp})"
                                        job_app_record["match_score"] = score
                                        job_app_record["applied_date"] = time.strftime("%Y-%m-%d")
                                        job_app_record["notes"] = f"Dispatched to {edit_email}. Subject: {edit_subject}"
                                        add_application(job_app_record)
                                        st.balloons()
                                        st.success(f"Dispatched & logged {job['company']} to Tracker!")
                                        st.session_state.search_results = [t for t in st.session_state.search_results if (t.get("_id") or t.get("job_title")) != tid]
                                        st.session_state["drafts"].pop(draft_key, None)
                                        st.rerun()
                                    else:
                                        err_msg = res.get('message', 'Unknown dispatch error')
                                        st.error(f"❌ In-App Dispatch Failed: {err_msg}")
                                        if "@" in edit_email:
                                            g_fallback_url = generate_gmail_compose_url(edit_email, edit_subject, edit_body)
                                            st.markdown(f"""
                                            <div style="background: #eff6ff; border: 1.5px solid #3b82f6; border-radius: 8px; padding: 10px 14px; margin: 8px 0;">
                                                <div style="font-weight: 700; color: #1e40af; font-size: 13px;">
                                                    💡 Instant 1-Click Solution (Send from Browser):
                                                </div>
                                                <div style="font-size: 12px; color: #1e3a8a; margin-top: 3px;">
                                                    You can dispatch this application right now directly through your logged-in Gmail tab without configuring an SMTP App Password!
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            st.link_button("🚀 Click Here to Open & Send in My Gmail", g_fallback_url, type="primary", use_container_width=True)

                        # 1-Click Gmail browser fallback
                        if "@" in edit_email:
                            gmail_url = generate_gmail_compose_url(edit_email, edit_subject, edit_body)
                            st.link_button("🌐 Open in My Gmail (Pre-filled)", gmail_url, use_container_width=True)

                    # Action: Send via Website Form (Internal Mailer)
                    if is_site_form or site_form_info:
                        if st.button("🌐 Send via Website Form (Internal Mailer)", key=f"site_btn_{cand_id}_{tid}", type="primary", use_container_width=True):
                            with st.spinner(f"Dispatching application through {job['company']} web form..."):
                                form_target_url = site_form_info.get("form_page", job.get("website", "")) if site_form_info else job.get("website", "")
                                sf_res = submit_to_site_form_playwright(
                                    form_page_url=form_target_url,
                                    candidate_name=active_profile.get("full_name", "Candidate"),
                                    candidate_email=active_profile.get("email", ""),
                                    candidate_phone=active_profile.get("phone", ""),
                                    subject=edit_subject,
                                    message_body=edit_body,
                                    attachment_path=master_resume_path,
                                    headless=True
                                )
                                shot = sf_res.get("screenshot")
                                if shot:
                                    st.session_state[f"proof_{tid}"] = shot
                                job_app_record = dict(job)
                                job_app_record["status"] = "Applied via Site Form"
                                job_app_record["application_mode"] = "Website Form (Playwright)"
                                job_app_record["match_score"] = score
                                job_app_record["applied_date"] = time.strftime("%Y-%m-%d")
                                job_app_record["screenshot_path"] = shot or ""
                                job_app_record["notes"] = f"Application submitted via official site form ({form_target_url}). Screenshot: {shot}"
                                add_application(job_app_record)
                                if sf_res.get("success"):
                                    st.success(f"Dispatched via website form! {sf_res.get('message')}")
                                else:
                                    st.error(f"Notice: {sf_res.get('message')}")
                                st.rerun()

                    # Action: Scan Website for Form
                    if not is_site_form and job.get("website"):
                        if st.button("🔎 Scan Website for Form", key=f"scan_site_{cand_id}_{tid}", use_container_width=True):
                            with st.spinner(f"Scanning {job['website']} for contact / career inquiry form..."):
                                found_f = detect_company_contact_form(job["website"])
                                if found_f.get("found"):
                                    job["is_site_form"] = True
                                    job["site_form"] = found_f
                                    st.success(f"Web form detected at {found_f.get('form_page')}!")
                                    st.rerun()
                                else:
                                    st.info("No standard web form identified on company website.")

                    # Action: Re-Extract HR Inbox
                    if st.button("🔄 Re-Extract HR Inbox", key=f"deep_ext_{cand_id}_{tid}", use_container_width=True):
                        with st.spinner(f"Querying corporate directories for {job['company']}..."):
                            res = deep_extract_company_recruitment_email(
                                job["company"],
                                job["job_title"],
                                portal_url
                            )
                            if res.get("email"):
                                job["hr_email"] = res["email"]
                                job["extraction_source"] = res.get("source", "Deep Corporate Extraction")
                                st.session_state["drafts"][draft_key]["hr_email"] = res["email"]
                                st.session_state[f"email_{cand_id}_{tid}"] = res["email"]
                                st.success(f"Extracted direct HR email: {res['email']}!")
                                st.rerun()
                            elif res.get("is_site_form"):
                                job["is_site_form"] = True
                                job["site_form"] = res.get("site_form")
                                st.success("Detected website form!")
                                st.rerun()
                            else:
                                st.info("No public HR email found in corporate registry.")

                    # Action: Open ATS Portal
                    if portal_url:
                        st.link_button("🌐 Open ATS Portal", portal_url, use_container_width=True)

                    # Action: Mark Applied via Portal
                    if st.button("📋 Mark Applied via Portal", key=f"portal_btn_{cand_id}_{tid}", use_container_width=True):
                        job_app_record = dict(job)
                        job_app_record["status"] = "Applied via Portal"
                        job_app_record["application_mode"] = f"Portal ({job.get('source_portal', 'Web')})"
                        job_app_record["match_score"] = score
                        job_app_record["applied_date"] = time.strftime("%Y-%m-%d")
                        job_app_record["notes"] = f"Application submitted online via {portal_url}"
                        add_application(job_app_record)
                        st.success(f"Logged {job['company']} to Tracker under 'Applied via Portal'!")
                        st.session_state.search_results = [t for t in st.session_state.search_results if (t.get("_id") or t.get("job_title")) != tid]
                        st.session_state["drafts"].pop(draft_key, None)
                        st.rerun()

                    # Action: Original Circular Reference Link
                    if portal_url:
                        st.caption(f"🔗 [Original Circular on {source_badge}]({portal_url}) *(Optional reference)*")

                    # Action: Language Toggle (Bangla / English)
                    if draft_info.get("language") == "Bangla" or "বাংলা" in current_subject:
                        if st.button("🇬🇧 Switch to English Pitch", key=f"lang_en_{cand_id}_{tid}", use_container_width=True):
                            with st.spinner("Drafting pitch in English..."):
                                new_pitch = generate_application_pitch(job, active_profile, language="English")
                                st.session_state["drafts"][draft_key]["subject"] = new_pitch["subject"]
                                st.session_state["drafts"][draft_key]["body"] = new_pitch["body"]
                                st.session_state["drafts"][draft_key]["language"] = "English"
                                st.session_state[f"subj_{cand_id}_{tid}"] = new_pitch["subject"]
                                st.session_state[f"body_{cand_id}_{tid}"] = new_pitch["body"]
                            st.success("Converted pitch to English!")
                            st.rerun()
                    else:
                        if st.button("🇧🇩 বাংলায় আবেদন তৈরি করুন (Bangla)", key=f"lang_bn_{cand_id}_{tid}", use_container_width=True):
                            with st.spinner("প্রমিত বাংলায় আবেদনপত্র প্রস্তুত করা হচ্ছে..."):
                                new_pitch = generate_application_pitch(job, active_profile, language="Bangla")
                                st.session_state["drafts"][draft_key]["subject"] = new_pitch["subject"]
                                st.session_state["drafts"][draft_key]["body"] = new_pitch["body"]
                                st.session_state["drafts"][draft_key]["language"] = "Bangla"
                                st.session_state[f"subj_{cand_id}_{tid}"] = new_pitch["subject"]
                                st.session_state[f"body_{cand_id}_{tid}"] = new_pitch["body"]
                            st.success("বাংলায় আবেদনপত্র প্রস্তুত সম্পন্ন হয়েছে!")
                            st.rerun()

                    # Action: Regenerate Draft
                    if st.button("🔄 Regenerate Draft", key=f"regen_{cand_id}_{tid}", use_container_width=True):
                        with st.spinner("Regenerating tailored pitch with AI..."):
                            curr_lang = draft_info.get("language", "English")
                            new_pitch = generate_application_pitch(job, active_profile, language=curr_lang)
                            st.session_state["drafts"][draft_key]["subject"] = new_pitch["subject"]
                            st.session_state["drafts"][draft_key]["body"] = new_pitch["body"]
                            st.session_state[f"subj_{cand_id}_{tid}"] = new_pitch["subject"]
                            st.session_state[f"body_{cand_id}_{tid}"] = new_pitch["body"]
                        st.success("Refreshed draft generated!")
                        st.rerun()

                    # Action: Dismiss Target
                    if st.button("❌ Dismiss Target", key=f"dismiss_{cand_id}_{tid}", use_container_width=True):
                        st.session_state.search_results = [t for t in st.session_state.search_results if (t.get("_id") or t.get("job_title")) != tid]
                        st.session_state["drafts"].pop(draft_key, None)
                        st.rerun()

                    # Screenshot Proof Viewer (Guaranteed Proof)
                    proof_shot = st.session_state.get(f"proof_{tid}") or job.get("screenshot_path")
                    if proof_shot and os.path.exists(proof_shot):
                        with st.expander("🖼️ View Submission Screenshot Proof", expanded=True):
                            st.image(proof_shot, caption=f"Proof of Application for {job['company']}", use_container_width=True)


# ==============================================================================
# TAB 2: CIRCULAR FLYER SCANNER (MULTIMODAL OCR)
# ==============================================================================
with tab_ocr:
    st.markdown("""
    <div class="main-header">
        <h1>📸 Bangladesh Circular Flyer Scanner (Multimodal OCR)</h1>
        <p>Scan newspaper clippings, Facebook hiring circulars, or flyers in English & Bengali with Gemini Vision.</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_image = st.file_uploader(
        "Upload Job Circular Photo / Flyer (JPG, PNG, WEBP)",
        type=["png", "jpg", "jpeg", "webp"]
    )
    
    if uploaded_image:
        col_img, col_data = st.columns([1, 1.4])
        with col_img:
            st.image(uploaded_image, caption="Uploaded Circular Flyer", use_column_width=True)
            scan_action = st.button("⚡ Extract Circular Details with AI", type="primary", use_container_width=True)
            
        with col_data:
            if scan_action:
                with st.spinner("Analyzing circular flyer (reading Bangla & English text)..."):
                    img_bytes = uploaded_image.getvalue()
                    mime = uploaded_image.type or "image/png"
                    res = scan_circular_image(img_bytes, mime)
                    
                    if res["success"]:
                        st.session_state.ocr_result = res["data"]
                        st.success("Successfully extracted circular information!")
                    else:
                        st.error(res["error"])
                        
            if st.session_state.ocr_result:
                ocr = st.session_state.ocr_result
                st.subheader("📋 Extracted Circular Specifications")
                
                c_tab1, c_tab2 = st.columns(2)
                with c_tab1:
                    st.write(f"🏢 **Hiring Entity:** {ocr.get('company', 'Unknown')}")
                    st.write(f"💼 **Job Title:** {ocr.get('job_title', 'Not specified')}")
                    st.write(f"👥 **Vacancies:** {ocr.get('vacancies', 'Not specified')}")
                    st.write(f"🎓 **Education:** {ocr.get('education_req', 'As per circular')}")
                with c_tab2:
                    st.write(f"⏳ **Deadline:** {ocr.get('deadline', 'Not stated')}")
                    st.write(f"💰 **Salary / Grade:** {ocr.get('salary', 'Negotiable')}")
                    st.write(f"📌 **Method:** {ocr.get('application_process', 'Portal')}")
                    st.write(f"🌐 **Language:** {'Bengali (বাংলা)' if ocr.get('is_bangla') else 'English'}")
                    
                st.markdown(f"**Description & Responsibilities:**\n{ocr.get('summary', '')}")
                
                if ocr.get("hr_email"):
                    st.caption(f"📧 Contact Email: `{ocr['hr_email']}`")
                if ocr.get("portal_url"):
                    st.caption(f"🔗 Portal Link: [{ocr['portal_url']}]({ocr['portal_url']})")
                    
                if st.button("💾 Add Extracted Circular to Application Tracker", type="secondary", use_container_width=True):
                    add_application({
                        "job_title": ocr.get("job_title", "Circular Opening"),
                        "company": ocr.get("company", "Employer"),
                        "location": "Bangladesh",
                        "source_portal": "Scanned Circular Flyer",
                        "salary": ocr.get("salary", "Negotiable"),
                        "deadline": ocr.get("deadline", "Check flyer"),
                        "apply_url": ocr.get("portal_url", ""),
                        "hr_email": ocr.get("hr_email", ""),
                        "application_mode": ocr.get("application_process", "Portal"),
                        "job_desc": ocr.get("summary", ""),
                        "status": "Saved"
                    })
                    st.success("Added circular directly to your Kanban Application Tracker!")
                    st.rerun()

# ==============================================================================
# TAB 3: APPLICATION TRACKER (KANBAN / CRM)
# ==============================================================================
with tab_tracker:
    st.markdown("""
    <div class="main-header">
        <h1>📊 Application Tracker & Kanban Pipeline</h1>
        <p>Monitor your job pipeline across all stages. Crash-proof SQLite storage with 1-click Excel/CSV export.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter Controls
    t_c1, t_c2, t_c3 = st.columns([1.5, 1.5, 1.2])
    with t_c1:
        status_filter = st.selectbox("Filter Status", ["All"] + VALID_STATUSES)
    with t_c2:
        search_filter = st.text_input("Search Company / Role", placeholder="Filter tracked applications...")
    with t_c3:
        view_mode = st.radio("View Format", ["Card View", "Table View"], horizontal=True)
        
    apps = get_applications(status=status_filter, search=search_filter)
    
    # Export Options
    col_exp1, col_exp2 = st.columns([1, 1])
    with col_exp1:
        df_export = export_applications_dataframe()
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Applications to CSV", data=csv_data, file_name="bd_job_applications.csv", mime="text/csv")
    with col_exp2:
        excel_buffer = io.BytesIO()
        df_export.to_excel(excel_buffer, index=False, engine="openpyxl")
        st.download_button("📊 Export Applications to Excel (.xlsx)", data=excel_buffer.getvalue(), file_name="bd_job_applications.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    st.markdown("---")
    
    # ==============================================================================
    # 🔔 1. DAY-4 AUTOMATED FOLLOW-UP OPERATIONS DESK (JOBPILOT PARITY)
    # ==============================================================================
    due_apps_list = get_due_followups()
    
    if due_apps_list:
        st.markdown(f"""
        <div style="background: #fef2f2; border: 1.5px solid #f87171; border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 16px; font-weight: 800; color: #991b1b;">🔔 Day-4 Follow-up Operations Desk ({len(due_apps_list)} Due Now)</span>
                    <p style="margin: 4px 0 0 0; color: #7f1d1d; font-size: 13px;">
                        These applications were dispatched 4+ days ago with no follow-up. Politeness and persistence double interview callbacks in Bangladesh.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        f_b1, f_b2 = st.columns([1.5, 2])
        with f_b1:
            if st.button("⚡ Batch Dispatch All Due Follow-ups (with Master CV)", type="primary", use_container_width=True, key="tracker_batch_followups"):
                with st.spinner("Executing automated follow-up cycle..."):
                    cycle_res = run_followup_cycle(dry_run=st.session_state.get("dry_run_mode", False))
                if cycle_res.get("success"):
                    st.balloons()
                    st.success(cycle_res.get("message"))
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(cycle_res.get("message"))
        with f_b2:
            st.caption(f"📎 **Attached to Follow-ups:** `{os.path.basename(get_default_resume_path() or 'Master_Resume.pdf')}` &nbsp;|&nbsp; 🛡️ Safe Dispatch Active")

        with st.expander(f"📋 Review Due Follow-ups Queue ({len(due_apps_list)} Pending)", expanded=True):
            for due_app in due_apps_list:
                d_id = due_app["id"]
                st.markdown(f"""
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <b>{due_app['job_title']}</b> at <span style="color: #006a4e; font-weight: 600;">{due_app['company']}</span>
                        <div style="font-size: 12px; color: #64748b; margin-top: 2px;">
                            Applied: <b>{due_app.get('applied_date', 'N/A')}</b> &nbsp;|&nbsp; 
                            Pending: <span style="background: #fee2e2; color: #991b1b; padding: 1px 6px; border-radius: 6px; font-weight: bold;">{due_app.get('days_pending', 4)} Days Ago</span> &nbsp;|&nbsp;
                            Recipient: <code>{due_app.get('hr_email') or 'No email recorded'}</code>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                f_col1, f_col2, f_col3 = st.columns([1.2, 1.2, 1.6])
                with f_col1:
                    is_f_preview = st.session_state.get(f"show_followup_preview_{d_id}", False)
                    p_label = "✖️ Close Preview" if is_f_preview else "👁️ Customize Pitch & Send"
                    if st.button(p_label, key=f"btn_prev_{d_id}", use_container_width=True):
                        st.session_state[f"show_followup_preview_{d_id}"] = not is_f_preview
                        st.rerun()
                with f_col2:
                    if st.button("✅ Mark Followed Up Manually", key=f"btn_mark_f_{d_id}", use_container_width=True):
                        mark_followed_up(d_id, notes="Manually marked as followed up")
                        st.success(f"Marked {due_app['company']} as Followed Up!")
                        st.rerun()
                with f_col3:
                    if due_app.get("hr_email"):
                        st.caption("Ready for 1-click email or Gmail dispatch")
                    else:
                        st.caption("⚠️ No HR email on record; portal application")
                
                # Individual Follow-up Pitch Console
                if st.session_state.get(f"show_followup_preview_{d_id}", False):
                    st.markdown(f"""
                    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; margin: 8px 0;">
                        <b>⚡ Day-4 Follow-up Dispatcher: {due_app['job_title']} ({due_app['company']})</b>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    lang_choice = st.radio("Follow-up Language", ["English", "Bangla (বাংলা)"], horizontal=True, key=f"f_lang_{d_id}")
                    lang_key = "Bangla" if "Bangla" in lang_choice else "English"
                    pitch = generate_followup_pitch(due_app, active_profile, language=lang_key)
                    
                    f_subj = st.text_input("Subject", value=pitch["subject"], key=f"f_subj_{d_id}")
                    f_body = st.text_area("Body", value=pitch["body"], height=160, key=f"f_body_{d_id}")
                    f_to = st.text_input("Recipient Email", value=due_app.get("hr_email") or "", key=f"f_to_{d_id}")
                    
                    f_snd1, f_snd2 = st.columns(2)
                    with f_snd1:
                        if f_to and "@" in f_to:
                            g_url = generate_gmail_compose_url(f_to, f_subj, f_body)
                            st.link_button("🚀 Open in My Gmail ➔", g_url, type="primary", use_container_width=True)
                    with f_snd2:
                        if st.button("📨 In-App Dispatch via SMTP", type="primary", key=f"btn_f_send_{d_id}", use_container_width=True):
                            if not f_to or "@" not in f_to:
                                st.error("Please provide a valid recipient email address.")
                            else:
                                with st.spinner(f"Sending follow-up to {f_to}..."):
                                    res = dispatch_followup_email(
                                        app_id=d_id,
                                        recipient_email=f_to,
                                        subject=f_subj,
                                        body=f_body,
                                        sender_email=active_profile.get("email"),
                                        dry_run=st.session_state.get("dry_run_mode", False)
                                    )
                                if res.get("success"):
                                    st.balloons()
                                    st.success(res.get("message"))
                                    st.session_state[f"show_followup_preview_{d_id}"] = False
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(res.get("message"))
    else:
        st.markdown("""
        <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 10px 16px; margin-bottom: 14px;">
            <span style="color: #15803d; font-weight: 600;">🟢 0 Day-4 Follow-ups Pending:</span>
            <span style="color: #166534; font-size: 13px;"> All applications are either recent (< 4 days) or have already had their follow-up cycle completed.</span>
        </div>
        """, unsafe_allow_html=True)

    # ==============================================================================
    # 🎉 2. RECRUITER INTERVIEW OPPORTUNITIES & INBOX LOOKUPS
    # ==============================================================================
    interview_apps = get_interview_opportunities()
    
    st.markdown("""
    <div style="background: #f0fdf4; border: 1.5px solid #22c55e; border-radius: 10px; padding: 14px 18px; margin: 16px 0 12px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <span style="font-size: 17px; font-weight: 800; color: #15803d;">🎉 Recruiter Interview Opportunities & Inbox Lookups</span>
                <span style="background: #27ae60; color: white; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; margin-left: 8px;">
                    """ + str(len(interview_apps)) + """ ACTIVE
                </span>
                <p style="margin: 4px 0 0 0; color: #166534; font-size: 13px;">
                    Scan your recruiter communications or log interview invitations across written tests, technical screenings, and management rounds.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    int_b1, int_b2 = st.columns(2)
    with int_b1:
        if st.button("🔍 Scan Recruiter Inbox for Interview Invites (IMAP / Gmail)", type="primary", use_container_width=True, key="scan_inbox_interviews_btn"):
            with st.spinner("Connecting securely to your Gmail inbox via IMAP SSL and scanning recent recruiter replies for interview signals..."):
                scan_res = scan_inbox_for_interview_invites(
                    sender_email=active_profile.get("email"),
                    days_back=21
                )
            st.session_state["inbox_interview_scan_results"] = scan_res
            st.rerun()

    with int_b2:
        is_manual_open = st.session_state.get("show_manual_interview_form", False)
        m_lbl = "✖️ Close Manual Entry" if is_manual_open else "➕ Record Interview Chance (Call / SMS / WhatsApp / Portal)"
        if st.button(m_lbl, use_container_width=True, key="toggle_manual_interview_form"):
            st.session_state["show_manual_interview_form"] = not is_manual_open
            st.rerun()

    # Render Inbox Scan Results if available
    if "inbox_interview_scan_results" in st.session_state:
        scan_data = st.session_state["inbox_interview_scan_results"]
        if not scan_data.get("success"):
            st.warning(f"⚠️ Inbox lookup notice: {scan_data.get('message')}")
        elif scan_data.get("count", 0) == 0:
            st.info(scan_data.get("message"))
        else:
            st.success(f"🎉 **{scan_data['count']} Potential Interview Opportunities Detected in Inbox!** Review below:")
            for idx, inv in enumerate(scan_data.get("interviews", [])):
                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border: 1.5px solid #16a34a; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <div>
                                <b style="font-size: 15px; color: #166534;">{inv['subject']}</b><br/>
                                <span style="font-size: 13px; color: #334155;">From: <code>{inv['from']}</code> &nbsp;|&nbsp; Date: {inv['date']}</span>
                            </div>
                            <div>
                                <span style="background: #dcfce7; color: #15803d; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                                    Confidence: {inv['confidence']}
                                </span>
                            </div>
                        </div>
                        <div style="background: #f8fafc; border-left: 3px solid #16a34a; padding: 8px 12px; margin: 8px 0; font-size: 13px; color: #475569;">
                            "{inv['snippet']}..."
                        </div>
                        <div style="font-size: 12px; color: #64748b;">
                            Matched Company: <b>{inv['company']}</b> &nbsp;|&nbsp; Role: <b>{inv['role']}</b>
                            {f' &nbsp;|&nbsp; 🔗 <a href="{inv["meeting_link"]}" target="_blank">Meeting Link Detected</a>' if inv.get("meeting_link") else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_act1, c_act2 = st.columns([1.5, 2])
                    with c_act1:
                        if st.button(f"✅ Add '{inv['company']}' to Interview CRM Pipeline", key=f"add_inv_crm_{idx}", type="primary", use_container_width=True):
                            # Check if matched app exists
                            if inv.get("matched_app"):
                                target_id = inv["matched_app"]["id"]
                                record_interview_chance(
                                    app_id=target_id,
                                    interview_date=datetime.now().strftime("%Y-%m-%d"),
                                    interview_type="Recruiter Screening / Interview",
                                    meeting_link=inv.get("meeting_link", ""),
                                    notes=f"Detected via Inbox: {inv['subject']} on {inv['date']}"
                                )
                            else:
                                target_id = add_application({
                                    "job_title": inv.get("role", "Applicant"),
                                    "company": inv.get("company", "Employer"),
                                    "location": "Bangladesh",
                                    "status": "Interview Scheduled",
                                    "source_portal": "Direct Recruiter Reply",
                                    "notes": f"Detected from Recruiter Email: {inv['subject']}"
                                })
                                record_interview_chance(
                                    app_id=target_id,
                                    interview_date=datetime.now().strftime("%Y-%m-%d"),
                                    interview_type="Recruiter Screening",
                                    meeting_link=inv.get("meeting_link", "")
                                )
                            st.balloons()
                            st.success(f"Recorded interview opportunity with {inv['company']}!")
                            st.rerun()
                    with c_act2:
                        if inv.get("meeting_link"):
                            st.link_button("🌐 Open Meeting Link", inv["meeting_link"], use_container_width=True)

    # Render Manual Interview Logger Form if expanded
    if st.session_state.get("show_manual_interview_form", False):
        st.markdown("""
        <div style="background: #f8fafc; border: 1.5px dashed #006a4e; border-radius: 8px; padding: 14px; margin: 10px 0;">
            <b style="color: #006a4e; font-size: 15px;">➕ Record Direct Interview Invitation (Phone / SMS / WhatsApp / Portal)</b>
        </div>
        """, unsafe_allow_html=True)
        
        all_app_choices = [f"{a['company']} — {a['job_title']} (ID: {a['id']})" for a in apps_all]
        all_app_choices.insert(0, "+ Create New Company Record")
        
        sel_app_str = st.selectbox("Select Tracked Opportunity", all_app_choices, key="manual_inv_app_sel")
        
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            if sel_app_str == "+ Create New Company Record":
                m_comp = st.text_input("Company Name *", key="man_inv_comp")
                m_role = st.text_input("Job Title *", key="man_inv_role")
            else:
                m_comp = ""
                m_role = ""
            m_stage = st.selectbox(
                "Interview Round / Type",
                [
                    "Technical Interview",
                    "HR Screening Call",
                    "Written Test / Examination",
                    "Take-Home Coding / Business Assessment",
                    "Final Management Round",
                    "On-site Office Interview"
                ],
                key="man_inv_stage"
            )
        with m_c2:
            m_date = st.date_input("Scheduled Interview Date", value=datetime.now() + timedelta(days=2), key="man_inv_date")
            m_time = st.time_input("Scheduled Time (BST)", value=datetime.now().time(), key="man_inv_time")
            m_link = st.text_input("Meeting Link (Google Meet / Zoom / MS Teams) or Office Location", placeholder="e.g. https://meet.google.com/xyz-abcd-efg or Gulshan-1 office", key="man_inv_link")
        
        m_notes = st.text_area("Recruiter Instructions / Preparation Notes", placeholder="e.g. Bring hardcopy CV, prepare 10-minute presentation on supply chain MIS...", key="man_inv_notes")
        
        if st.button("💾 Record Interview Opportunity into CRM", type="primary", use_container_width=True, key="save_manual_inv_btn"):
            if sel_app_str == "+ Create New Company Record":
                if not m_comp or not m_role:
                    st.error("Please enter both company name and job title.")
                else:
                    new_id = add_application({
                        "job_title": m_role,
                        "company": m_comp,
                        "location": "Bangladesh",
                        "status": "Interview Scheduled",
                        "notes": m_notes
                    })
                    record_interview_chance(
                        app_id=new_id,
                        interview_date=f"{m_date} {m_time.strftime('%H:%M')}",
                        interview_type=m_stage,
                        meeting_link=m_link,
                        notes=m_notes
                    )
                    st.session_state["show_manual_interview_form"] = False
                    st.balloons()
                    st.success(f"Successfully recorded interview with {m_comp}!")
                    st.rerun()
            else:
                import re
                m = re.search(r'\(ID: (\d+)\)', sel_app_str)
                if m:
                    target_id = int(m.group(1))
                    record_interview_chance(
                        app_id=target_id,
                        interview_date=f"{m_date} {m_time.strftime('%H:%M')}",
                        interview_type=m_stage,
                        meeting_link=m_link,
                        notes=m_notes
                    )
                    st.session_state["show_manual_interview_form"] = False
                    st.balloons()
                    st.success("Interview opportunity recorded!")
                    st.rerun()

    # Active Interview Opportunities List
    if interview_apps:
        st.markdown(f"#### 📅 Active Interview Pipeline ({len(interview_apps)})")
        for int_app in interview_apps:
            i_id = int_app["id"]
            with st.container():
                st.markdown(f"""
                <div style="background: white; border: 1.5px solid #22c55e; border-radius: 8px; padding: 14px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(34, 197, 94, 0.08);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #15803d;">{int_app['job_title']} — {int_app['company']}</h4>
                            <div style="font-size: 13px; color: #475569; margin-top: 4px;">
                                🎯 <b>Round:</b> {int_app.get('interview_type') or 'Technical Screening'} &nbsp;|&nbsp;
                                📅 <b>Date:</b> {int_app.get('interview_date') or 'Pending Schedule'} &nbsp;|&nbsp;
                                📍 <b>Location:</b> {int_app.get('location', 'Bangladesh')}
                            </div>
                        </div>
                        <div>
                            <span class="status-badge status-interview-scheduled">{int_app['status']}</span>
                        </div>
                    </div>
                    {f'<div style="margin-top: 6px; font-size: 13px; color: #334155;"><b>Notes:</b> {int_app.get("notes")}</div>' if int_app.get("notes") else ''}
                </div>
                """, unsafe_allow_html=True)
                
                i_col1, i_col2, i_col3, i_col4 = st.columns([1.5, 1.5, 1.2, 0.8])
                with i_col1:
                    if int_app.get("meeting_link"):
                        m_url = int_app["meeting_link"]
                        if not m_url.startswith("http"):
                            m_url = f"https://{m_url}"
                        st.link_button("🌐 Join Video Meeting", m_url, type="primary", use_container_width=True)
                    else:
                        st.caption("No video link attached")
                with i_col2:
                    is_prep_open = st.session_state.get(f"show_prep_{i_id}", False)
                    p_lbl = "✖️ Hide Prep" if is_prep_open else "🤖 AI Interview Prep"
                    if st.button(p_lbl, key=f"btn_prep_{i_id}", use_container_width=True):
                        st.session_state[f"show_prep_{i_id}"] = not is_prep_open
                        st.rerun()
                with i_col3:
                    if st.button("🏆 Mark Offer Received", key=f"btn_offer_{i_id}", use_container_width=True):
                        update_application_status(i_id, "Offer Received", notes=f"Offer received on {time.strftime('%Y-%m-%d')}!")
                        st.balloons()
                        st.success(f"Congratulations on the offer from {int_app['company']}!")
                        st.rerun()
                with i_col4:
                    if st.button("❌ Rejected", key=f"btn_rej_{i_id}", help="Mark as Rejected", use_container_width=True):
                        update_application_status(i_id, "Rejected")
                        st.rerun()

                # Show AI Interview Prep if open
                if st.session_state.get(f"show_prep_{i_id}", False):
                    with st.spinner("Synthesizing custom Bangladesh interview preparation strategy and model answers..."):
                        prep_res = generate_interview_prep(
                            job_title=int_app["job_title"],
                            company=int_app["company"],
                            job_desc=int_app.get("job_desc", ""),
                            candidate_profile=active_profile
                        )
                    st.markdown(f"""
                    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; margin-top: 6px;">
                        {prep_res.get('prep_content', '')}
                    </div>
                    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 📋 All Applications Ledger")
    if not apps:
        st.info("No applications found in this view. Use the '🔍 Unified Job Search' or '📸 Circular Scanner' to track roles.")
    elif view_mode == "Table View":
        display_df = pd.DataFrame(apps)[["id", "job_title", "company", "location", "source_portal", "status", "applied_date", "deadline", "salary"]]
        st.dataframe(display_df, use_container_width=True)
    else:
        for app in apps:
            app_id = app["id"]
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <h4 style="margin: 0 0 4px 0;">{app['job_title']}</h4>
                            <div style="font-weight: 600; color: #006a4e;">{app['company']} &nbsp;•&nbsp; 📍 {app['location']}</div>
                        </div>
                        <div>
                            <span class="status-badge status-{app['status'].lower().replace(' ', '-')}">{app['status']}</span>
                        </div>
                    </div>
                    <div style="margin: 8px 0; font-size: 13px; color: #64748b;">
                        <b>Portal:</b> {app['source_portal']} &nbsp;|&nbsp; 
                        <b>Applied:</b> {app['applied_date'] or 'Not yet'} &nbsp;|&nbsp; 
                        <b>Deadline:</b> {app['deadline']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Management row
                m_c1, m_c2, m_c3, m_c4 = st.columns([1.3, 1.8, 1.1, 0.6])
                with m_c1:
                    current_idx = VALID_STATUSES.index(app['status']) if app['status'] in VALID_STATUSES else 0
                    new_st = st.selectbox("Change Status", VALID_STATUSES, index=current_idx, key=f"st_sel_{app_id}")
                    if new_st != app['status']:
                        update_application_status(app_id, new_st)
                        st.success(f"Updated status to {new_st}")
                        st.rerun()
                with m_c2:
                    notes_input = st.text_input("Notes / Interview Date", value=app.get("notes") or "", key=f"notes_{app_id}")
                    if st.button("Save Note", key=f"save_note_{app_id}"):
                        update_application_status(app_id, app['status'], notes=notes_input)
                        st.success("Note saved!")
                with m_c3:
                    if app['status'] == "Saved":
                        is_t_open = st.session_state.get(f"show_track_apply_{app_id}", False)
                        t_label = "✖️ Close" if is_t_open else "🚀 Apply from App"
                        if st.button(t_label, key=f"t_apply_btn_{app_id}", type="primary", use_container_width=True):
                            st.session_state[f"show_track_apply_{app_id}"] = not is_t_open
                            st.rerun()
                    elif app.get("apply_url"):
                        st.link_button("🌐 Open Listing", app["apply_url"], use_container_width=True)
                with m_c4:
                    if st.button("🗑️", key=f"del_{app_id}", help="Delete from Tracker", use_container_width=True):
                        delete_application(app_id)
                        st.rerun()

                # Tracker Apply Console (if expanded)
                if st.session_state.get(f"show_track_apply_{app_id}", False):
                    st.markdown(f"""
                    <div style="background: #f0fdf4; border: 1.5px solid #16a34a; border-radius: 10px; padding: 14px; margin: 10px 0;">
                        <div style="font-weight: 700; color: #166534; margin-bottom: 6px;">
                            🚀 Quick In-App Application Dispatch: {app['job_title']} at {app['company']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    t_em1, t_em2 = st.columns(2)
                    with t_em1:
                        track_dest_email = st.text_input("Recruiter Email *", value=app.get("hr_email") or "", key=f"track_em_{app_id}")
                    with t_em2:
                        track_subject = st.text_input("Subject", value=f"Application for {app['job_title']} - {active_profile.get('full_name')}", key=f"track_sub_{app_id}")
                    
                    track_pitch = generate_application_pitch(app, active_profile)
                    track_body = st.text_area("Cover Email Body", value=track_pitch["body"], height=140, key=f"track_body_{app_id}")
                    
                    t_user_email = active_profile.get("email") or ""
                    st.caption(f"Sender: **{t_user_email}** (Your Logged-In Candidate Email)")

                    t_btn_col1, t_btn_col2 = st.columns(2)
                    with t_btn_col1:
                        if track_dest_email and "@" in track_dest_email:
                            t_compose_url = generate_gmail_compose_url(track_dest_email, track_subject, track_body)
                            st.link_button("🚀 Open in My Gmail ➔", t_compose_url, type="primary", use_container_width=True)
                        if st.button("✅ I Sent via Gmail — Mark as Applied", key=f"t_mark_g_{app_id}", use_container_width=True):
                            update_application_status(
                                app_id,
                                "Applied",
                                notes=f"Sent via Gmail from {t_user_email} on {time.strftime('%Y-%m-%d')}"
                            )
                            st.session_state[f"show_track_apply_{app_id}"] = False
                            st.balloons()
                            st.success("Updated to Applied!")
                            st.rerun()
                    with t_btn_col2:
                        t_dry = st.checkbox("Simulate Only (Dry Run)", value=False, key=f"track_dry_{app_id}")
                        if st.button("📨 In-App SMTP Send", key=f"track_send_{app_id}", use_container_width=True):
                            if not track_dest_email or "@" not in track_dest_email:
                                st.error("Please provide a valid recipient email address.")
                            else:
                                with st.spinner(f"Dispatching application from {t_user_email}..."):
                                    t_res = dispatch_application_email(
                                        recipient_email=track_dest_email,
                                        subject=track_subject,
                                        body=track_body,
                                        sender_email=t_user_email,
                                        dry_run=t_dry
                                    )
                                    if t_res.get("success"):
                                        update_application_status(
                                            app_id,
                                            "Applied",
                                            notes=f"Dispatched from Tracker on {time.strftime('%Y-%m-%d %H:%M')}"
                                        )
                                        st.session_state[f"show_track_apply_{app_id}"] = False
                                        st.balloons()
                                        st.success(f"Dispatched application! Status moved to 'Applied'.")
                                        st.rerun()
                                    else:
                                        st.error(t_res.get("message"))

                # View submission screenshot proof if available for this tracked application
                app_shot = app.get("screenshot_path")
                if not app_shot and app.get("notes") and ".png" in str(app.get("notes")):
                    import re
                    m = re.search(r'([A-Za-z]:\\[^\s]+\.png)', str(app.get("notes")))
                    if m:
                        app_shot = m.group(1)

                if app_shot and os.path.exists(app_shot):
                    with st.expander("🖼️ View Submission Screenshot Proof", expanded=False):
                        st.image(app_shot, caption=f"Proof of Submission for {app['company']} ({app['job_title']})", use_container_width=True)

# ==============================================================================
# TAB 4: CANDIDATE PROFILE & RESUME
# ==============================================================================
with tab_profile:
    st.markdown("""
    <div class="main-header">
        <h1>👤 Candidate Profile & CV Intelligence</h1>
        <p>Upload your resume to extract skills and enable automated ATS matching across all Bangladesh openings.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Multi-Candidate Profile Switcher & Manager
    all_profiles_tab = list_user_profiles()
    if len(all_profiles_tab) > 1:
        st.markdown("### 👥 Candidate Profiles Management")
        st.caption("Switch between saved candidates or manage individual profile credentials:")
        
        prof_c1, prof_c2 = st.columns([2.5, 1])
        with prof_c1:
            prof_dict = {p["id"]: f"{p['full_name']} — {p.get('email', 'No Email')} ({p.get('target_industry', 'General')})" for p in all_profiles_tab}
            cur_p_id = active_profile.get("id")
            p_list = list(prof_dict.keys())
            cur_p_idx = p_list.index(cur_p_id) if cur_p_id in p_list else 0
            
            selected_mgr_id = st.selectbox(
                "Active Candidate Profile",
                p_list,
                format_func=lambda pid: prof_dict[pid],
                index=cur_p_idx,
                key="tab4_profile_selector"
            )
            if selected_mgr_id != cur_p_id:
                set_active_profile_id(selected_mgr_id)
                st.session_state["drafts"] = {}
                st.session_state["search_results"] = []
                for k in list(st.session_state.keys()):
                    if any(k.startswith(p) for p in ["subj_", "body_", "sender_", "email_", "proof_"]):
                        st.session_state.pop(k, None)
                st.success(f"Switched active candidate to: **{prof_dict[selected_mgr_id].split('—')[0].strip()}**!")
                st.rerun()
        with prof_c2:
            st.write("")
            st.write("")
            if st.button("➕ Create New Candidate", key="tab4_add_new_cand", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state["add_new_candidate"] = True
                st.session_state["drafts"] = {}
                st.session_state["search_results"] = []
                for k in list(st.session_state.keys()):
                    if any(k.startswith(p) for p in ["subj_", "body_", "sender_", "email_", "proof_", "login_"]):
                        st.session_state.pop(k, None)
                st.rerun()

        st.markdown("---")

    # Stored Resume Status Banner
    avail_res = list_available_resumes()
    if avail_res:
        active_res_p = get_default_resume_path(active_profile)
        active_res_name = os.path.basename(active_res_p) if active_res_p else (active_profile.get("resume_filename") or avail_res[0]["filename"])
        res_names = [r["filename"] for r in avail_res]
        cur_idx = res_names.index(active_res_name) if active_res_name in res_names else 0
        
        c_res1, c_res2 = st.columns([3, 1])
        with c_res1:
            chosen_res = st.selectbox(
                f"📎 Selected Active CV for {active_profile.get('full_name')} (Attached to all Email & ATS applications)",
                res_names,
                index=cur_idx,
                help="This is the PDF file attached to every email application and submitted via Playwright ATS Autopilot."
            )
            if chosen_res != active_res_name:
                set_active_resume_filename(chosen_res, profile_id=active_profile.get("id"))
                active_profile["resume_filename"] = chosen_res
                save_active_profile(active_profile)
                st.session_state["drafts"] = {}
                st.success(f"Switched active application CV to: `{chosen_res}`")
                st.rerun()
        with c_res2:
            active_meta = next((r for r in avail_res if r["filename"] == active_res_name), avail_res[0])
            st.metric("CV File Size", f"{active_meta['size_kb']} KB")
        st.info(f"📎 **Currently Attached to Applications for {active_profile.get('full_name')}:** `{active_res_name}` — *Pre-configured for 1-Click Application Dispatch & ATS Autopilot*")
        
        # Embedded Document Viewer in Profile Tab
        if active_res_p and os.path.exists(active_res_p):
            pdf_b64_prof = get_pdf_base64(active_res_p)
            with st.expander("📄 View Embedded Resume Document", expanded=False):
                if pdf_b64_prof:
                    prof_pdf_html = f'<iframe src="data:application/pdf;base64,{pdf_b64_prof}#toolbar=0" width="100%" height="520" style="border: 1px solid #cbd5e1; border-radius: 8px;" type="application/pdf"></iframe>'
                    st.markdown(prof_pdf_html, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No resume found. Upload your PDF resume below to enable 1-Click Application Dispatch.")
    
    cv_upload = st.file_uploader(f"Upload New / Updated Resume for {active_profile.get('full_name')} (PDF)", type=["pdf"], key="tab_profile_cv_up")
    if cv_upload:
        with st.spinner("Saving resume and extracting competencies with AI..."):
            save_uploaded_resume(cv_upload.getvalue(), cv_upload.name, profile_id=active_profile.get("id"))
            extracted_text = extract_text_from_pdf(cv_upload.getvalue())
            parsed_summary = summarize_profile_from_cv(extracted_text)
            
            # Auto populate profile fields
            active_profile["full_name"] = parsed_summary["full_name"] or active_profile["full_name"]
            if parsed_summary.get("email"):
                active_profile["email"] = parsed_summary["email"].strip()
                c_now = get_credentials(active_profile.get("id"))
                save_credentials(
                    gemini_api_key=c_now.get("gemini_api_key", DEFAULT_GEMINI_KEY),
                    sender_email=parsed_summary["email"].strip(),
                    app_password=c_now.get("app_password", ""),
                    profile_id=active_profile.get("id")
                )
            if parsed_summary.get("phone"):
                active_profile["phone"] = parsed_summary["phone"]
            if parsed_summary.get("linkedin"):
                active_profile["linkedin"] = parsed_summary["linkedin"]
            if parsed_summary.get("github_portfolio"):
                active_profile["github_portfolio"] = parsed_summary["github_portfolio"]
            if parsed_summary.get("education_summary"):
                active_profile["education_summary"] = parsed_summary["education_summary"]
            if parsed_summary.get("skills_summary"):
                active_profile["skills_summary"] = parsed_summary["skills_summary"]
            active_profile["raw_cv_text"] = extracted_text
            active_profile["resume_filename"] = cv_upload.name
            
            save_active_profile(active_profile)
            set_active_resume_filename(cv_upload.name, profile_id=active_profile.get("id"))
            st.session_state["drafts"] = {}
            st.success(f"🎉 Resume `{cv_upload.name}` saved and set as active! Email auto-extracted: **{active_profile.get('email')}**.")
            st.rerun()

    with st.form("profile_form"):
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            name_val = st.text_input("Full Name", value=active_profile.get("full_name", ""))
            email_val = st.text_input("Email Address (Used for Login & Outgoing Applications)", value=active_profile.get("email", ""))
            phone_val = st.text_input("Phone Number (BD +880)", value=active_profile.get("phone", ""))
            linkedin_val = st.text_input("LinkedIn Profile URL", value=active_profile.get("linkedin", ""))
        with p_c2:
            ind_idx = list(BD_JOB_TAXONOMY.keys()).index(active_profile.get("target_industry")) if active_profile.get("target_industry") in BD_JOB_TAXONOMY else 0
            industry_val = st.selectbox("Primary Target Industry", list(BD_JOB_TAXONOMY.keys()), index=ind_idx)
            edu_val = st.text_area("Education Summary", value=active_profile.get("education_summary", ""), height=70)
            skills_val = st.text_area("Skills & Core Competencies (comma separated)", value=active_profile.get("skills_summary", ""), height=70)
            
        save_profile_btn = st.form_submit_button("💾 Save Profile Changes", type="primary", use_container_width=True)
        if save_profile_btn:
            active_profile["full_name"] = name_val.strip()
            active_profile["email"] = email_val.strip()
            active_profile["phone"] = phone_val.strip()
            active_profile["linkedin"] = linkedin_val.strip()
            active_profile["target_industry"] = industry_val
            active_profile["education_summary"] = edu_val
            active_profile["skills_summary"] = skills_val
            save_active_profile(active_profile)

            # Keep credentials sender_email in sync
            c_now = get_credentials(active_profile.get("id"))
            save_credentials(
                gemini_api_key=c_now.get("gemini_api_key", DEFAULT_GEMINI_KEY),
                sender_email=email_val.strip(),
                app_password=c_now.get("app_password", ""),
                profile_id=active_profile.get("id")
            )
            st.session_state["drafts"] = {}
            st.success("Profile saved and outbound sender email synchronized!")
            st.rerun()

# ==============================================================================
# TAB 5: 18+ BD JOB PORTALS DIRECTORY
# ==============================================================================
with tab_directory:
    st.markdown("""
    <div class="main-header">
        <h1>🌐 All 18+ Bangladesh Job Portals Directory</h1>
        <p>Access every major recruitment hub, government circular board, and NGO registry in Bangladesh.</p>
    </div>
    """, unsafe_allow_html=True)
    
    dir_query = st.text_input("Quick Direct Search Query", placeholder="Enter job title or skill (e.g., Software Engineer, MTO, Merchandiser)...")
    
    categories = get_portals_by_category()
    for cat_name, portal_items in categories.items():
        st.subheader(f"📌 {cat_name}")
        cols = st.columns(3)
        for i, (pkey, portal) in enumerate(portal_items):
            with cols[i % 3]:
                search_url = get_portal_search_url(pkey, dir_query if dir_query.strip() else "jobs")
                st.markdown(f"""
                <div class="job-card" style="height: 190px;">
                    <div style="font-size: 24px; margin-bottom: 4px;">{portal['icon']}</div>
                    <h4 style="margin: 0 0 4px 0; color: #006a4e;">{portal['name']}</h4>
                    <span class="portal-badge" style="background-color: #f1f5f9; color: #334155;">{portal['badge']}</span>
                    <p style="font-size: 13px; color: #64748b; margin: 8px 0 12px 0; line-height: 1.3;">
                        {portal['description'][:95]}...
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.link_button(f"Visit {portal['name']} ➔", search_url, use_container_width=True)
        st.markdown("---")

# ==============================================================================
# TAB 6: SETTINGS
# ==============================================================================
with tab_settings:
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ System Configuration & Credentials</h1>
        <p>Configure your Gemini API key and optional email dispatch credentials to power full automation.</p>
    </div>
    """, unsafe_allow_html=True)
    
    current_creds = get_credentials()
    
    st.subheader("🔑 Google Gemini AI Key")
    st.markdown("""
    * **Pre-configured Key:** Pre-loaded with the key from JobPilot Desktop (`AQ.Ab8...`).
    * **Capabilities:** Multimodal Bangla/English Circular Flyer OCR, ATS Semantic Fit Analysis, and Custom Pitch Synthesis.
    """)
    
    current_key = DEFAULT_GEMINI_KEY
    masked_preview = f"{current_key[:4]}...{current_key[-4:]}" if len(current_key) > 8 else "Not set"
    st.caption(f"Active Key Status: `{masked_preview}` 🔒 (Permanent System Key)")
    
    new_api_key = st.text_input("Gemini API Key 🔒 (System Key - Unchangeable)", value=DEFAULT_GEMINI_KEY, type="password", disabled=True, help="Permanent system key configured for Gemini 2.5/Flash AI models. This key cannot be modified.")
    st.caption("🔒 *Permanent System Key (`AQ.Ab8...`) — Locked & Unchangeable*")
    
    st.markdown("---")
    st.subheader("📧 Candidate Gmail Dispatch Credentials (Mandatory)")
    st.caption("Mandatory: Required to directly dispatch applications, deep-extract corporate recruiter emails, and approve outgoing submissions.")
    
    cur_em = active_profile.get("email") or current_creds.get("sender_email", "")
    cur_pw = current_creds.get("app_password", "")
    if cur_em and cur_pw:
        if "smtp_auth_checked" not in st.session_state:
            st.session_state["smtp_auth_checked"] = authenticate_gmail_credentials(cur_em, cur_pw)
        is_smtp_ok, smtp_stat_msg = st.session_state["smtp_auth_checked"]
        if is_smtp_ok:
            st.success(f"🟢 **Gmail SMTP Status: Authenticated & Connected** (`{cur_em}` via `smtp.gmail.com:587`)")
        else:
            st.warning(f"⚠️ **Gmail SMTP Status: Authentication Failed** ({smtp_stat_msg})")

    set_col1, set_col2 = st.columns(2)
    with set_col1:
        current_profile_email = cur_em
        new_sender_email = st.text_input("Sender Gmail Address (Your Account) *", value=current_profile_email, placeholder="your_email@gmail.com")
    with set_col2:
        new_app_pw = st.text_input("Gmail App Password (16-char) *", value=current_creds.get("app_password", ""), type="password", placeholder="e.g. abcd efgh ijkl mnop (press Ctrl+V to paste here)", help="Mandatory: Required for in-app application sending and recruiter extraction.")
        
    st.markdown("""
    <div style="background: #fffbeb; border: 1.5px solid #f59e0b; border-radius: 8px; padding: 12px 14px; margin: 8px 0 14px 0;">
        <div style="font-weight: 700; color: #b45309; font-size: 13px;">
            🔑 Where to find it & How to paste it:
        </div>
        <div style="font-size: 12px; color: #92400e; line-height: 1.5; margin-top: 4px;">
            <b>1. Find it:</b> Ensure 2-Step Verification is active in <a href="https://myaccount.google.com/signinoptions/two-step-verification" target="_blank" style="color: #b45309; font-weight: 700; text-decoration: underline;">Google Security</a>. Open <a href="https://myaccount.google.com/apppasswords" target="_blank" style="color: #b45309; font-weight: 700; text-decoration: underline;">👉 Google App Passwords</a>.<br/>
            <b>2. Generate:</b> Enter App Name <code>BD Job Finder</code>, click <b>Create</b>, and copy the 16-letter code (e.g. <code>abcd efgh ijkl mnop</code>).<br/>
            <b>3. Paste it:</b> Click in the box above and press <b>Ctrl + V</b> (or Right-Click ➔ Paste).
        </div>
    </div>
    """, unsafe_allow_html=True)
        
    col_save, col_test_auth = st.columns([1.5, 1])
    with col_save:
        save_btn = st.button("💾 Save Credentials & Authenticate", type="primary", use_container_width=True)
    with col_test_auth:
        test_auth_btn = st.button("🧪 Test SMTP Auth Only", use_container_width=True)

    if test_auth_btn:
        clean_set_pw = new_app_pw.strip().replace(" ", "")
        with st.spinner("Testing Google SMTP authentication..."):
            is_auth, auth_msg = authenticate_gmail_credentials(new_sender_email.strip(), clean_set_pw)
        if is_auth:
            st.success(f"✅ {auth_msg}")
        else:
            st.error(f"❌ {auth_msg}")

    if save_btn:
        clean_set_pw = new_app_pw.strip().replace(" ", "")
        if not new_sender_email.strip() or "@" not in new_sender_email:
            st.error("Please provide a valid Gmail address.")
        elif not clean_set_pw or len(clean_set_pw) < 16:
            st.error("⚠️ Gmail 16-Character App Password is MANDATORY! Without it, direct dispatch and email extraction cannot function.")
        else:
            with st.spinner("🔒 Connecting to smtp.gmail.com:587 and verifying your Google App Password..."):
                is_auth, auth_msg = authenticate_gmail_credentials(new_sender_email.strip(), clean_set_pw)
            if not is_auth:
                st.error(f"❌ {auth_msg}")
            else:
                save_credentials(
                    gemini_api_key=new_api_key.strip() or DEFAULT_GEMINI_KEY,
                    sender_email=new_sender_email.strip(),
                    app_password=clean_set_pw
                )
                active_profile["email"] = new_sender_email.strip()
                save_active_profile(active_profile)
                st.balloons()
                st.success(f"🎉 {auth_msg} All credentials updated and saved to SQLite!")
                st.rerun()

    st.markdown("---")
    st.subheader("🧪 Verify Gmail SMTP Dispatch Connection")
    st.caption("Send a verification test email or run a simulated dispatch to ensure your outbound application system is operational.")

    t_col1, t_col2 = st.columns([2, 1])
    with t_col1:
        test_inbox = st.text_input(
            "Test Recipient Email",
            value=active_profile.get("email") or current_creds.get("sender_email") or "candidate@gmail.com",
            key="test_target_inbox"
        )
    with t_col2:
        test_is_dry = st.checkbox("Simulate Only (Dry Run)", value=False, key="test_dry_check_settings")

    if st.button("📨 Send Verification Test Email", key="btn_test_dispatch"):
        with st.spinner(f"Connecting to smtp.gmail.com:587 and verifying outbound dispatch..."):
            test_res = dispatch_application_email(
                recipient_email=test_inbox,
                subject="BD Job Finder — Gmail SMTP Dispatch Verified",
                body=f"Congratulations!\n\nYour Gmail SMTP outbound application pipeline is functioning successfully.\n\nSender: {current_creds.get('sender_email')}\nCandidate: {active_profile.get('full_name')}\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                dry_run=test_is_dry
            )
            if test_res.get("success"):
                st.balloons()
                st.success(f"✅ {test_res.get('message')}")
            else:
                st.error(f"❌ {test_res.get('message')}")
    st.subheader("🚪 Session & Profile Management")
    c_sess1, c_sess2 = st.columns(2)
    with c_sess1:
        if st.button("🚪 Log Out & Clear All Data", use_container_width=True):
            logout_and_wipe_all_user_data()
            st.session_state.clear()
            st.session_state["authenticated"] = False
            st.rerun()
    with c_sess2:
        st.caption("Database Location: `data/jobs.db` (SQLite)")
