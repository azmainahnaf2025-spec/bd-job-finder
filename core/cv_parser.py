"""
Resume and CV Parser for BD Job Finder.
Extracts text from PDF/DOCX files, normalizes contact details,
and analyzes skill sets against standard Bangladesh industry competencies.
"""

import io
import re
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Comprehensive keywords catalog for skill extraction
SKILL_CATALOG = [
    # Programming & Tech
    "python", "django", "fastapi", "flask", "javascript", "typescript", "react", "next.js",
    "vue.js", "angular", "node.js", "express", "java", "spring boot", "php", "laravel",
    "c#", ".net", "asp.net", "flutter", "react native", "android", "ios", "swift", "kotlin",
    "sql", "mysql", "postgresql", "mongodb", "redis", "docker", "kubernetes", "aws", "azure",
    "gcp", "git", "github", "ci/cd", "linux", "rest api", "graphql", "sqa", "selenium",
    "automation testing", "manual testing", "jira", "ui/ux", "figma", "adobe xd",
    # Data & AI
    "data analysis", "data science", "pandas", "numpy", "power bi", "tableau", "excel",
    "advanced excel", "machine learning", "deep learning", "nlp", "computer vision",
    # Banking, Accounting & Finance
    "financial analysis", "audit", "taxation", "vat", "cost accounting", "cma", "ca",
    "tally", "quickbooks", "sap", "oracle erp", "credit risk", "trade finance",
    "anti-money laundering", "aml", "kyc", "foreign exchange", "forex",
    # Garments, Textile & RMG
    "merchandising", "woven", "knit", "sweater", "fabric sourcing", "costing", "consumption",
    "cad", "pattern making", "quality assurance", "aql", "garments washing", "textile engineering",
    "lc documentation", "commercial", "export-import", "compliance", "bsci", "oeko-tex",
    # Marketing, Sales & BD
    "digital marketing", "seo", "sem", "google ads", "meta ads", "social media marketing",
    "content writing", "copywriting", "lead generation", "b2b sales", "cold outreach",
    "crm", "hubspot", "salesforce", "market research", "brand strategy",
    # Supply Chain & Operations
    "supply chain", "procurement", "vendor management", "inventory management", "warehouse",
    "logistics", "shipping", "distribution", "erp", "process optimization", "six sigma",
    # Soft & Management Skills
    "leadership", "project management", "scrum", "agile", "communication", "negotiation",
    "problem solving", "team management", "presentation", "analytical skills"
]

def extract_text_from_pdf(pdf_bytes_or_file) -> str:
    """Extracts raw text from a PDF file buffer or bytes."""
    if not HAS_PYPDF:
        print("Notice: pypdf is not installed. PDF text parsing unavailable.")
        return ""
    text = ""
    try:
        if isinstance(pdf_bytes_or_file, bytes):
            stream = io.BytesIO(pdf_bytes_or_file)
        else:
            stream = pdf_bytes_or_file
            
        reader = PdfReader(stream)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    except Exception as err:
        print(f"Error parsing PDF: {err}")
    return text.strip()

def parse_contact_info(text: str) -> dict:
    """Extracts email, phone, and linkedin from resume text."""
    contacts = {
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": ""
    }
    
    # Email
    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    if emails:
        contacts["email"] = emails[0]
        
    # Bangladesh Phone numbers (+8801... or 01...)
    phones = re.findall(r'(?:\+?880\s?1[3-9]\d{2}[-\s]?\d{6}|01[3-9]\d{2}[-\s]?\d{6})', text)
    if phones:
        contacts["phone"] = phones[0]
        
    # LinkedIn
    linkedin = re.findall(r'linkedin\.com/in/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    if linkedin:
        contacts["linkedin"] = f"https://{linkedin[0]}"
        
    # GitHub
    github = re.findall(r'github\.com/[a-zA-Z0-9_-]+', text, re.IGNORECASE)
    if github:
        contacts["github"] = f"https://{github[0]}"
        
    return contacts

def extract_skills_from_text(text: str) -> list[str]:
    """Identifies skills present in CV text matching the skill catalog."""
    lowered = text.lower()
    matched = []
    for skill in SKILL_CATALOG:
        # Match exact word boundaries or common representations
        pattern = r'(?:\b|_)' + re.escape(skill) + r'(?:\b|_)'
        if re.search(pattern, lowered):
            matched.append(skill.title())
    return sorted(list(set(matched)))

def summarize_profile_from_cv(text: str) -> dict:
    """Produces a structured profile draft from raw CV text."""
    contacts = parse_contact_info(text)
    skills = extract_skills_from_text(text)
    
    # Detect possible full name from the top 5 non-empty lines
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    candidate_name = ""
    for ln in lines[:5]:
        if len(ln) < 40 and not any(c in ln for c in ["@", "http", "+880", "Curriculum", "Resume", "CV", "Page"]):
            # Probable name
            candidate_name = ln
            break
            
    # Detect education lines
    edu_keywords = ["bachelor", "master", "b.sc", "bba", "mba", "m.sc", "hsc", "ssc", "university", "institute", "college"]
    education_lines = []
    for ln in lines:
        if any(ek in ln.lower() for ek in edu_keywords):
            education_lines.append(ln)
            if len(education_lines) >= 4:
                break
                
    return {
        "full_name": candidate_name or "Job Seeker",
        "email": contacts["email"],
        "phone": contacts["phone"],
        "linkedin": contacts["linkedin"],
        "github_portfolio": contacts["github"],
        "education_summary": " | ".join(education_lines[:3]),
        "skills_summary": ", ".join(skills),
        "raw_cv_text": text
    }

def deep_parse_cv_with_ai(cv_text: str) -> dict:
    """
    Uses Gemini AI to extract structured candidate details from CV text with high precision.
    Falls back to heuristic parser if AI is unavailable.
    """
    if not cv_text or not cv_text.strip():
        return {}

    from .ai_engine import get_gemini_client
    client = get_gemini_client()
    if client:
        prompt = f"""
        You are an expert HR talent analyst and executive recruiter in Bangladesh.
        Analyze this candidate resume / CV and extract their professional details.

        CV Text:
        {cv_text[:5000]}

        Extract and return strictly valid JSON with these exact keys:
        - "full_name": Candidate's official name
        - "email": Contact email address
        - "phone": Bangladesh phone number (+880...)
        - "linkedin": LinkedIn profile link if mentioned
        - "github_portfolio": GitHub, portfolio, or website link
        - "target_industry": Best matching sector from: ["IT & Software Engineering", "Banking, NBFI & FinTech", "Garments, Textile & RMG Sector", "Marketing, Sales & Business Development", "Supply Chain, Procurement & Logistics", "Accounting, Finance & Audit", "NGO, Development & Social Impact", "Government, Autonomous Bodies & Public Sector", "Pharmaceuticals, Healthcare & Medical", "Human Resources & Administration", "Education, Training & Research", "Customer Support, BPO & Telemarketing", "Media, Creative Arts & Design", "Engineering (Civil, Electrical, Mechanical)", "Fresh Graduate & Trainee Programs"]
        - "education_summary": 1-2 sentence summary of degrees, majors, and universities attended
        - "skills_summary": Comma-separated list of top 8-12 technical, domain, and management skills
        """
        try:
            import json
            res = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            data = json.loads(res.text)
            if data.get("full_name") and data.get("full_name").lower() != "job seeker":
                data["raw_cv_text"] = cv_text
                return data
        except Exception as e:
            print(f"AI CV parsing notice: {e}")

    # Fallback to rule-based parser
    return summarize_profile_from_cv(cv_text)
