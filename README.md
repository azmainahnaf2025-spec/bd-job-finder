# BD Job Finder — Bangladesh Public Job Search & Circular Assistant

A modern, public-friendly recruitment assistant and circular tracking ecosystem designed specifically for job seekers across all 64 districts in Bangladesh.

---

## 🌟 Key Features

1. **Comprehensive Bangladesh Job Taxonomy**:
   - Covers 14+ distinct career sectors (IT/Software, Banking & NBFI, Garments/Textile RMG, Marketing, Supply Chain, Accounting, NGO, Government/Autonomous, Pharma, Education, etc.).
   - 150+ pre-cataloged standard Bangladeshi job titles.
   - All 8 divisions and 64 districts + Dhaka commercial zones (Gulshan, Banani, Motijheel, Uttara, Mirpur, Savar/EPZ) and Remote.

2. **All 18+ Bangladesh Job Portals Supported**:
   - BDJobs, AllJobs Teletalk, Chakri.com, Skill.jobs, Careerjet Bangladesh, eJobs, Nextjobz, Myjobs, BDJobs Live, MoreJobs, Job Media, NgoJobsBdesh, BDJobsToday, LinkedIn BD, Indeed BD, Glassdoor BD, Facebook Recruitment, Prothom Alo Jobs.

3. **Multimodal Circular Flyer OCR (Bangla & English)**:
   - Powered by Gemini Vision to extract job title, vacancies, educational criteria, age limit, deadline, and application instructions from scanned flyers, newspaper photos, and Facebook posts.

4. **ATS Resume Parser & Skill Gap Analyzer**:
   - Upload any PDF resume to extract skills, calculate an ATS match score (0–100%), and identify missing keywords required for the role.

5. **Bilingual Cover Letter & Cold Pitch Generator**:
   - One-click tailored application drafts in both professional English and natural Bengali (বাংলা).

6. **Crash-Proof SQLite Application Tracker (Kanban / CRM)**:
   - Replaces fragile Excel files with an embedded SQLite database (`data/jobs.db`).
   - Track application stages: `Saved`, `Applied`, `Interview Scheduled`, `Offer Received`, `Rejected`, `Archived`.
   - Export to CSV or Excel (`.xlsx`) anytime with one click.

7. **Zero-Setup Keyless Mode**:
   - Works immediately out of the box without requiring API keys or terminal configurations. Optional Gemini AI key can be added directly via the Web UI.

---

## 🚀 Quick Start (Windows)

1. Double-click `run.bat` (or run `run.ps1` in PowerShell).
2. The browser will open automatically at:
   ```
   http://localhost:8502
   ```

---

## 📂 Project Architecture

```
bd-job-finder/
├── app.py                     # Main Streamlit Dashboard (6 Executive Tabs)
├── core/
│   ├── taxonomy.py            # 14 sectors, 150+ job titles, 64 districts
│   ├── portals_registry.py    # Metadata & search URL engines for 18+ BD portals
│   ├── database.py            # SQLite database & Kanban application tracker
│   ├── scraper.py             # Multi-source scraper & opportunity aggregator
│   ├── cv_parser.py           # PDF resume parser & skill extractor
│   └── ai_engine.py           # Gemini Vision circular OCR & ATS match scoring
├── data/
│   └── jobs.db                # SQLite database (auto-generated)
├── requirements.txt           # Python dependencies
├── run.bat                    # One-click Windows launcher
└── run.ps1                    # PowerShell launcher
```
