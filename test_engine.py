"""
Automated Verification Test Suite for BD Job Finder.
Tests taxonomy catalogs, portal registry URL generators, database operations,
CV parser, and search aggregator.
"""

import os
import sys

# Ensure project root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def test_taxonomy():
    print("Testing Taxonomy...")
    from core.taxonomy import BD_JOB_TAXONOMY, BD_DIVISIONS_AND_DISTRICTS, get_all_job_titles, get_all_districts
    
    assert len(BD_JOB_TAXONOMY) >= 14, f"Expected at least 14 sectors, got {len(BD_JOB_TAXONOMY)}"
    titles = get_all_job_titles()
    assert len(titles) >= 100, f"Expected at least 100 job titles, got {len(titles)}"
    districts = get_all_districts()
    assert len(districts) >= 64, f"Expected at least 64 districts/regions, got {len(districts)}"
    print(f"  [OK] Sectors: {len(BD_JOB_TAXONOMY)}, Job Titles: {len(titles)}, Districts/Zones: {len(districts)}")

def test_portals_registry():
    print("Testing Portals Registry...")
    from core.portals_registry import BD_JOB_PORTALS, get_portal_search_url, get_portals_by_category
    
    assert len(BD_JOB_PORTALS) >= 18, f"Expected at least 18 portals, got {len(BD_JOB_PORTALS)}"
    url_bdj = get_portal_search_url("bdjobs", "Software Engineer")
    assert "bdjobs" in url_bdj
    url_teletalk = get_portal_search_url("alljobs_teletalk", "Officer")
    assert "alljobs.teletalk" in url_teletalk
    categories = get_portals_by_category()
    assert len(categories) >= 4, f"Expected at least 4 portal categories, got {len(categories)}"
    print(f"  [OK] Verified {len(BD_JOB_PORTALS)} Bangladesh Job Portals across {len(categories)} categories")

def test_database():
    print("Testing Database & Application Tracker...")
    from core.database import (
        init_db,
        save_active_profile,
        get_active_profile,
        add_application,
        get_applications,
        update_application_status,
        get_application_stats,
        export_applications_dataframe,
        delete_application
    )
    
    init_db()
    
    # Save profile
    test_prof = {
        "full_name": "Rahim Ahmed",
        "email": "rahim@example.com",
        "phone": "+8801712345678",
        "target_industry": "IT & Software Engineering",
        "education_summary": "B.Sc in CSE, Dhaka University",
        "skills_summary": "Python, Django, PostgreSQL, React",
        "raw_cv_text": "Experienced Python Developer with expertise in Django and REST APIs."
    }
    pid = save_active_profile(test_prof)
    assert pid is not None
    loaded = get_active_profile()
    assert loaded["full_name"] == "Rahim Ahmed"
    
    # Add application
    app_id = add_application({
        "job_title": "Junior Python Developer",
        "company": "Tech BD Ltd.",
        "location": "Banani, Dhaka",
        "source_portal": "BDJobs",
        "status": "Saved",
        "salary": "৳45,000",
        "deadline": "2026-10-01"
    })
    assert app_id is not None
    
    # Update status
    update_application_status(app_id, "Applied", notes="Submitted online portal form")
    apps = get_applications(status="Applied")
    assert len(apps) >= 1
    assert apps[0]["status"] == "Applied"
    assert apps[0]["notes"] == "Submitted online portal form"
    
    # Stats
    stats = get_application_stats()
    assert stats["Applied"] >= 1
    
    # Export DataFrame
    df = export_applications_dataframe()
    assert len(df) >= 1
    
    # Credentials & Default Key from Desktop JobPilot
    from core.database import get_credentials, save_credentials, DEFAULT_GEMINI_KEY
    creds = get_credentials()
    assert creds["gemini_api_key"] == DEFAULT_GEMINI_KEY or len(creds["gemini_api_key"]) > 0
    save_credentials(gemini_api_key=DEFAULT_GEMINI_KEY, sender_email="test@gmail.com")
    updated_creds = get_credentials()
    assert updated_creds["sender_email"] == "test@gmail.com"
    
    # Cleanup test app
    delete_application(app_id)
    print("  [OK] Database CRUD, credentials, profile management, and exports verified successfully")

def test_cv_parser():
    print("Testing CV Parser...")
    from core.cv_parser import summarize_profile_from_cv, extract_skills_from_text
    
    sample_cv = """
    Farhan Chowdhury
    Email: farhan.chowdhury@gmail.com
    Phone: +8801812345678
    LinkedIn: linkedin.com/in/farhan-chowdhury
    
    Education:
    Bachelor of Business Administration (BBA) in Marketing, North South University
    
    Skills & Competencies:
    Digital Marketing, SEO, Social Media Marketing, Content Writing, Advanced Excel, CRM
    """
    
    summary = summarize_profile_from_cv(sample_cv)
    assert summary["email"] == "farhan.chowdhury@gmail.com"
    assert "01812345678" in summary["phone"]
    assert "SEO" in summary["skills_summary"] or "Digital Marketing" in summary["skills_summary"]
    print(f"  [OK] Parsed contact and skills: {summary['skills_summary']}")

def test_scraper():
    print("Testing Search & Scraper...")
    from core.scraper import search_bangladesh_jobs
    
    results = search_bangladesh_jobs(query="Python", limit=5)
    assert len(results) >= 1
    assert "Python" in results[0]["job_title"] or "Software" in results[0]["job_title"]
    print(f"  [OK] Scraper returned {len(results)} verified opportunities for query 'Python'")

def test_ai_engine():
    print("Testing AI & Pitch Engine (Keyless Mode)...")
    from core.ai_engine import analyze_resume_match, generate_application_pitch
    
    match = analyze_resume_match(
        candidate_cv="Python, Django, PostgreSQL, REST API, Git",
        job_title="Python Backend Developer",
        job_desc="We need an engineer experienced with Python, Django, and Docker."
    )
    assert match["score"] >= 50
    assert "Python" in match["matched_skills"] or "Django" in match["matched_skills"]
    
    pitch = generate_application_pitch(
        job={"job_title": "Backend Developer", "company": "Brain Station 23"},
        candidate_profile={"full_name": "Rahim Ahmed", "education_summary": "B.Sc CSE", "skills_summary": "Python", "phone": "+8801700000000", "email": "rahim@test.com"},
        language="Bangla"
    )
    assert "আবেদনপত্র" in pitch["subject"]
    assert "Brain Station 23" in pitch["body"]
    print("  [OK] ATS Matcher & Bilingual Pitch generator functioning properly")

if __name__ == "__main__":
    print("==================================================")
    print("       BD JOB FINDER TEST SUITE STARTING          ")
    print("==================================================")
    test_taxonomy()
    test_portals_registry()
    test_database()
    test_cv_parser()
    test_scraper()
    test_ai_engine()
    print("==================================================")
    print("       ALL AUTOMATED VERIFICATION TESTS PASSED!   ")
    print("==================================================")
