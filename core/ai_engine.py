"""
AI Intelligence Engine for BD Job Finder.
Powers:
1. Multimodal OCR for Bangla and English circular images (Gemini Vision).
2. ATS Match Score & Missing Skill Gap Analysis.
3. Bilingual Cover Letter and Cold Outreach Generator (English & Bangla).
4. Zero-Setup Keyless Mode Fallback when no Gemini API key is configured.
"""

import os
import json
import re
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from .database import get_setting

# Default Gemini key matching JobPilot Desktop configuration
DEFAULT_GEMINI_KEY = "AQ.Ab8RN6KSV7C02uU5e97rlgHCyzGIEUpOSZZf3DcNFnNWCExqWw"
GEMINI_MODEL = "gemini-3.6-flash"

def get_gemini_client():
    """Initializes Gemini client using configured key, environment variable, or Desktop JobPilot default."""
    api_key = get_setting("gemini_api_key") or os.getenv("GEMINI_API_KEY") or DEFAULT_GEMINI_KEY
    if api_key and api_key.strip():
        try:
            return genai.Client(api_key=api_key.strip())
        except Exception as err:
            print(f"Gemini client initialization notice: {err}")
    return None

# ==============================================================================
# 1. MULTIMODAL CIRCULAR FLYER OCR
# ==============================================================================
class CircularStructuredData(BaseModel):
    company: str = Field(description="Name of the hiring organization, ministry, bank, or company")
    job_title: str = Field(description="Exact position or job title being advertised")
    vacancies: str = Field(default="Not specified", description="Number of vacancies / পদ সংখ্যা if stated")
    education_req: str = Field(default="", description="Educational qualification required (e.g. B.Sc in CSE, Masters, HSC, SSC)")
    experience_req: str = Field(default="", description="Experience required in years or roles")
    age_limit: str = Field(default="", description="Age limit mentioned (e.g., 18-30 years, max 35)")
    deadline: str = Field(default="Not specified", description="Application deadline date or time")
    salary: str = Field(default="Negotiable", description="Salary or pay scale grade mentioned")
    application_process: str = Field(default="Portal", description="How to apply: Email, Teletalk SMS, Google Form, Online Portal, or Physical Mail")
    hr_email: str = Field(default="", description="Email address to submit CV to, if any")
    portal_url: str = Field(default="", description="Application link or website URL if provided")
    summary: str = Field(description="Summary of key job requirements and responsibilities")
    is_bangla: bool = Field(default=False, description="True if the circular is written in Bengali, False if English")

def scan_circular_image(image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """
    Extracts structured job circular information from an image or scanned document.
    Works natively with bilingual Bengali and English circulars.
    """
    client = get_gemini_client()
    if not client:
        return {
            "success": False,
            "error": "Gemini API key not configured. Please enter your free API key in the '⚙️ Settings' tab to enable Multimodal Image OCR.",
            "data": None
        }

    prompt = """
    You are an expert HR and recruitment document analyst in Bangladesh.
    Carefully inspect this job circular flyer / newspaper announcement (which may be in Bengali, English, or mixed).
    
    Extract all essential application details accurately:
    - Company or Ministry Name (প্রতিষ্ঠানের নাম)
    - Position / Job Title (পদের নাম)
    - Vacancy Count (পদ সংখ্যা)
    - Educational Qualification (শিক্ষাগত যোগ্যতা)
    - Experience & Age Limit (অভিজ্ঞতা ও বয়স সীমা)
    - Application Deadline (আবেদনের শেষ তারিখ)
    - Salary or Pay Grade (বেতন স্কেল / গ্রেড)
    - Application Method (আবেদনের নিয়ম: Teletalk, Email, Google Form, Website, Hardcopy)
    - Contact Email or Application Link
    
    Return pure structured JSON conforming strictly to the CircularStructuredData schema.
    """

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CircularStructuredData,
                temperature=0.2
            )
        )
        data = json.loads(response.text)
        return {"success": True, "data": data, "error": None}
    except Exception as err:
        return {"success": False, "error": f"OCR Extraction failed: {str(err)}", "data": None}

# ==============================================================================
# 2. ATS RESUME MATCH & SKILL GAP ANALYZER
# ==============================================================================
_MATCH_CACHE: dict = {}

def analyze_resume_match(candidate_cv: str, job_title: str, job_desc: str) -> dict:
    """
    Evaluates fit between candidate's CV and job expectations.
    Provides match score (0-100%), matched skills, missing skills, and tailoring advice.
    Works in Keyless Mode (heuristic) or AI Mode (semantic).
    """
    if not candidate_cv or not candidate_cv.strip():
        return {
            "score": 50,
            "matched_skills": [],
            "missing_skills": ["Upload CV in '👤 Profile' tab for full analysis"],
            "tailoring_advice": "Upload your resume in the Candidate Profile tab to get an automated ATS match score and skill gap breakdown."
        }

    cache_key = f"{hash(candidate_cv[:1500])}_{job_title.strip()}_{job_desc[:100].strip()}"
    if cache_key in _MATCH_CACHE:
        return _MATCH_CACHE[cache_key]

    client = get_gemini_client()
    
    # AI Powered Deep Semantic Analysis
    if client:
        prompt = f"""
        You are an ATS (Applicant Tracking System) and senior recruiter in Bangladesh.
        Compare the Candidate Resume against the Target Job Description.

        Target Job: {job_title}
        Job Description: {job_desc}

        Candidate Resume:
        {candidate_cv[:4000]}

        Analyze:
        1. match_score (Integer 0 to 100 based on realistic job alignment in Bangladesh)
        2. matched_skills (List of skills/competencies present in both)
        3. missing_skills (List of skills/keywords required by the job but absent from CV)
        4. tailoring_advice (2-3 sentences of concrete advice to tailor the CV for this specific opening)

        Return strictly valid JSON with keys: "match_score", "matched_skills", "missing_skills", "tailoring_advice".
        """
        try:
            res = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            parsed = json.loads(res.text)
            out = {
                "score": int(parsed.get("match_score", 65)),
                "matched_skills": parsed.get("matched_skills", []),
                "missing_skills": parsed.get("missing_skills", []),
                "tailoring_advice": parsed.get("tailoring_advice", "Highlight relevant projects and industry keywords.")
            }
            _MATCH_CACHE[cache_key] = out
            return out
        except Exception:
            pass  # Fall through to keyless heuristic

    # Keyless Fallback Engine (Keyword & Token Overlap)
    cv_lower = candidate_cv.lower()
    target_lower = f"{job_title} {job_desc}".lower()
    
    # Extract words of 4+ characters
    job_keywords = set(re.findall(r'\b[a-zA-Z]{4,}\b', target_lower))
    stop_words = {"with", "that", "this", "from", "have", "will", "your", "team", "work", "role", "must", "able", "year", "years", "good"}
    job_keywords = [k for k in job_keywords if k not in stop_words]
    
    matched = [kw for kw in job_keywords if kw in cv_lower]
    missing = [kw for kw in job_keywords if kw not in cv_lower][:6]
    
    ratio = len(matched) / max(1, len(job_keywords))
    score = int(min(95, max(45, 50 + ratio * 45)))
    
    out = {
        "score": score,
        "matched_skills": [m.title() for m in matched[:8]],
        "missing_skills": [m.title() for m in missing],
        "tailoring_advice": f"Include keywords such as {', '.join([m.title() for m in missing[:3]])} in your experience summary to enhance ATS parsing."
    }
    _MATCH_CACHE[cache_key] = out
    return out

# ==============================================================================
# 3. BILINGUAL COVER LETTER & EMAIL PITCH GENERATOR
# ==============================================================================
def generate_application_pitch(
    job: dict,
    candidate_profile: dict,
    language: str = "English"
) -> dict:
    """
    Produces tailored cover letters and cold email outreach pitches in English or Bangla.
    Strictly uses the specified candidate's name, phone, email, skills, and resume attachment.
    """
    client = get_gemini_client()
    candidate_name = candidate_profile.get("full_name", "Job Seeker")
    candidate_phone = candidate_profile.get("phone", "")
    candidate_email = candidate_profile.get("email", "")
    candidate_edu = candidate_profile.get("education_summary", "")
    candidate_skills = candidate_profile.get("skills_summary", "")
    candidate_industry = candidate_profile.get("target_industry", "the industry")
    resume_name = candidate_profile.get("resume_filename") or "Master Resume.pdf"

    if language == "Bangla":
        subject = f"আবেদনপত্র: {job.get('job_title', 'পদ')} পদে আবেদনের জন্য — {candidate_name}"
    else:
        subject = f"Application: {job.get('job_title', 'Position')} — {candidate_name}"

    if client:
        lang_instruction = "Write in professional Bengali (বাংলা)" if language == "Bangla" else "Write in professional, compelling English"
        prompt = f"""
        You are a top career advisor and executive recruiter in Bangladesh.
        Write a tailored, high-converting job application cover letter / email pitch.
        {lang_instruction}.

        Target Role: {job.get('job_title', 'Position')}
        Hiring Organization: {job.get('company', 'Company')}
        Role Context: {job.get('job_desc', '')}

        MANDATORY CANDIDATE PROFILE (YOU MUST USE ONLY THIS CANDIDATE'S EXACT INFORMATION):
        - Full Name: {candidate_name}
        - Phone Number: {candidate_phone}
        - Contact Email: {candidate_email}
        - Education: {candidate_edu}
        - Core Competencies & Skills: {candidate_skills}
        - Primary Industry: {candidate_industry}
        - Attached Resume: {resume_name}

        CRITICAL RULES:
        1. Emphasize {candidate_name}'s specific competencies in {candidate_skills} and background in {candidate_edu}.
        2. Explicitly state that {candidate_name}'s master resume ({resume_name}) is attached to this email.
        3. Never invent other candidate details or mix information from any other applicant.
        4. Sign-off MUST strictly be:
           Sincerely,
           {candidate_name}
           Phone: {candidate_phone}
           Email: {candidate_email}
           (or in Bangla:
           বিনীত,
           {candidate_name}
           মোবাইল: {candidate_phone}
           ইমেইল: {candidate_email}
           )
        5. Output format:
           Subject: <subject line>
           Body:
           <email body>
        """
        try:
            res = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            raw = res.text.strip()
            if "Subject:" in raw and "Body:" in raw:
                parts = raw.split("Body:", 1)
                subject = parts[0].replace("Subject:", "").strip()
                body = parts[1].strip()
            elif raw.startswith("Subject:"):
                lines = raw.split("\n", 1)
                subject = lines[0].replace("Subject:", "").strip()
                body = lines[1].strip() if len(lines) > 1 else raw
            else:
                body = raw
            return {"subject": subject, "body": body}
        except Exception:
            pass

    # Keyless Deterministic Fallback Template
    if language == "Bangla":
        subject = f"আবেদনপত্র: {job.get('job_title', 'পদ')} পদে আবেদনের জন্য — {candidate_name}"
        body = f"""সম্মানিত নিয়োগকারী কর্তৃপক্ষ ({job.get('company')}),

আমি আপনার প্রতিষ্ঠানে সম্প্রতি প্রকাশিত "{job.get('job_title')}" পদে অত্যন্ত আগ্রহের সাথে আবেদন করছি। 

{candidate_edu}-এ আমার শিক্ষাগত পটভূমি এবং {candidate_skills}-এ বিশেষ দক্ষতা উক্ত পদের দায়িত্বসমূহ নিষ্ঠা ও পেশাদারিত্বের সাথে পালনে কার্যকর ভূমিকা রাখবে বলে আমি বিশ্বাস করি। {candidate_name} হিসেবে সততা, সময়ানুবর্তিতা এবং সমস্যা সমাধানের দক্ষতার মাধ্যমে আমি আপনার প্রতিষ্ঠানের অগ্রগতিতে অবদান রাখতে প্রস্তুত।

আমার বিস্তারিত জীবনবৃত্তান্ত ({resume_name}) এই পত্রের সাথে সংযুক্ত করা হলো। একটি সাক্ষাৎকারের মাধ্যমে আমার যোগ্যতা বিস্তারিত তুলে ধরার সুযোগ পেলে কৃতার্থ হব।

বিনীত,
{candidate_name}
মোবাইল: {candidate_phone}
ইমেইল: {candidate_email}"""
    else:
        subject = f"Application: {job.get('job_title', 'Position')} — {candidate_name}"
        body = f"""Dear Hiring Team at {job.get('company')},

I am writing to express my strong interest in the {job.get('job_title')} position currently available at your esteemed organization.

With my background in {candidate_edu} and proven competencies in {candidate_skills}, I am well-equipped to contribute immediately to your team's objectives. As an experienced professional in {candidate_industry}, I am committed to delivering high-quality, data-driven results.

Please find my master resume ({resume_name}) attached for your detailed review. I would welcome the opportunity to discuss how my qualifications align with {job.get('company')}'s goals during an interview.

Sincerely,
{candidate_name}
Phone: {candidate_phone}
Email: {candidate_email}"""

    return {"subject": subject, "body": body}

def generate_followup_pitch(
    job_or_app: dict,
    candidate_profile: dict,
    language: str = "auto"
) -> dict:
    """
    Produces tailored Day-4 follow-up pitches in English or Bangla,
    modeled directly after Desktop JobPilot's automated follow-up engine.
    """
    candidate_name = candidate_profile.get("full_name", "Candidate")
    candidate_phone = candidate_profile.get("phone", "")
    candidate_email = candidate_profile.get("email", "")
    candidate_linkedin = candidate_profile.get("linkedin", "")
    candidate_edu = candidate_profile.get("education_summary", "Degree")
    candidate_skills = candidate_profile.get("skills_summary", "Core skills")
    
    role = job_or_app.get("job_title", "Position")
    company = job_or_app.get("company", "Company")
    applied_val = job_or_app.get("applied_date") or "earlier this week"
    if str(applied_val).startswith("202"):
        try:
            dt = datetime.strptime(str(applied_val)[:10], "%Y-%m-%d")
            applied_str_en = dt.strftime("%B %d, %Y")
            applied_str_bn = dt.strftime("%d/%m/%Y")
        except Exception:
            applied_str_en = str(applied_val)[:10]
            applied_str_bn = str(applied_val)[:10]
    else:
        applied_str_en = str(applied_val)
        applied_str_bn = str(applied_val)

    # Auto detect language if requested
    if language == "auto":
        is_bn = any('\u0980' <= c <= '\u09ff' for c in f"{role} {company}")
        target_lang = "Bangla" if is_bn else "English"
    else:
        target_lang = language

    client = get_gemini_client()
    if client:
        lang_prompt = "Write in professional Bengali (বাংলা)" if target_lang == "Bangla" else "Write in polite, high-impact English"
        prompt = f"""
        You are an elite career strategist for corporate Bangladesh.
        Write a concise, polite, high-conversion Day-4 follow-up email for a previously submitted job application.
        {lang_prompt}.

        Application Details:
        Target Role: {role}
        Company: {company}
        Original Application Date: {applied_str_en}
        
        Candidate Info:
        Name: {candidate_name}
        Contact: {candidate_phone} | {candidate_email} | {candidate_linkedin}
        Key Qualifications: {candidate_edu} | {candidate_skills}

        Instructions:
        - Politely reference the application sent on {applied_str_en}.
        - Reiterate strong enthusiasm and cultural alignment for {company}.
        - Mention that the candidate's comprehensive resume/CV is re-attached to the email for immediate review.
        - Request an interview to discuss how candidate's skills will deliver immediate impact.
        - Output format:
        Subject: <subject line>
        Body:
        <email body>
        """
        try:
            res = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            raw = res.text.strip()
            subj = f"Following up: Application for {role} — {candidate_name}"
            body = raw
            if "Subject:" in raw and "Body:" in raw:
                parts = raw.split("Body:", 1)
                subj = parts[0].replace("Subject:", "").strip()
                body = parts[1].strip()
            elif raw.startswith("Subject:"):
                lines = raw.split("\n", 1)
                subj = lines[0].replace("Subject:", "").strip()
                body = lines[1].strip() if len(lines) > 1 else raw
            return {"subject": subj, "body": body}
        except Exception:
            pass

    # High-quality standard templates (JobPilot reference parity)
    if target_lang == "Bangla":
        subject = f"ফলো-আপ: {role} পদে আবেদনপত্র — {candidate_name}"
        body = (
            f"শ্রদ্ধেয় নিয়োগকারী কর্তৃপক্ষ, {company},\n\n"
            f"গত {applied_str_bn} তারিখে {company}-এ \"{role}\" পদে প্রেরিত আমার আবেদনপত্রের প্রেক্ষিতে "
            f"বিনীতভাবে এই ফলো-আপ ইমেইলটি প্রেরণ করছি। {candidate_edu} এবং {candidate_skills}-এ আমার পটভূমির আলোকে, "
            f"আপনার প্রতিষ্ঠানে অবদান রাখার ব্যাপারে আমি অত্যন্ত আগ্রহী ও প্রস্তুত।\n\n"
            f"আপনার সুবিধার্থে আমার পূর্ণাঙ্গ জীবনবৃত্তান্ত (CV) পুনরায় এই ইমেইলে সংযুক্ত করা হলো। একটি সাক্ষাৎকারের মাধ্যমে "
            f"কীভাবে আমি {company}-এর লক্ষ্য পূরণে সরাসরি সহায়তা করতে পারি তা নিয়ে আলোচনার সুযোগ পেলে কৃতজ্ঞ হব।\n\n"
            f"বিনীত,\n"
            f"{candidate_name}\n"
            f"ফোন: {candidate_phone}\n"
            f"ইমেইল: {candidate_email}" + (f"\nলিংকডইন: {candidate_linkedin}" if candidate_linkedin else "")
        )
    else:
        subject = f"Following up: Application for {role} — {candidate_name}"
        body = (
            f"Dear Hiring Team at {company},\n\n"
            f"I am writing to politely follow up on my application submitted on {applied_str_en} "
            f"for the {role} position. Given my background in {candidate_edu} and competencies in {candidate_skills}, "
            f"I remain deeply enthusiastic about contributing to your team's objectives.\n\n"
            f"Please find my resume attached once again for your convenience. I would welcome the opportunity "
            f"to discuss how my qualifications align with {company}'s vision in an interview.\n\n"
            f"Sincerely,\n"
            f"{candidate_name}\n"
            f"Phone: {candidate_phone}\n"
            f"Email: {candidate_email}" + (f"\nLinkedIn: {candidate_linkedin}" if candidate_linkedin else "")
        )

    return {"subject": subject, "body": body}

def generate_interview_prep(
    job_title: str,
    company: str,
    job_desc: str = "",
    candidate_profile: dict = None
) -> dict:
    """
    Generates comprehensive AI interview preparation tailored to the role,
    company, and Bangladesh employment context.
    """
    prof = candidate_profile or {}
    c_name = prof.get("full_name", "Candidate")
    c_skills = prof.get("skills_summary", "")
    
    client = get_gemini_client()
    if client:
        prompt = f"""
        Act as an elite interview coach in Dhaka, Bangladesh.
        Generate an actionable interview preparation guide for:
        Role: {job_title}
        Company: {company}
        Job Context: {job_desc}
        Candidate Profile: {c_name} (Skills: {c_skills})

        Provide:
        1. 🎯 Top 4 Likely Technical & Operational Interview Questions with model answers.
        2. 🇧🇩 Bangladesh Corporate Culture & Workplace Expectation tips for {company}.
        3. 💡 3 Smart Questions for the candidate to ask the interviewer.
        """
        try:
            res = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            return {"success": True, "prep_content": res.text.strip()}
        except Exception:
            pass

    # High quality fallback guide
    content = f"""### 🎯 Interview Preparation Guide: {job_title} at {company}

#### 1. Anticipated Technical & Role-Specific Questions:
1. **"Walk us through your hands-on experience relevant to {job_title}."**
   - *Strategy:* Structure your answer using the STAR method (Situation, Task, Action, Result). Highlight your background in {c_skills or 'core functional competencies'}.
2. **"How do you handle urgent deadlines and inter-departmental coordination under pressure?"**
   - *Strategy:* Bangladesh employers value ownership, reliability, and cross-functional collaboration. Cite an example from past projects.
3. **"What tools and methodologies do you utilize to ensure accuracy and continuous improvement?"**
   - *Strategy:* Mention practical tools (Excel, analytical software, ticketing/CRM, or coding frameworks).
4. **"Why do you want to join {company} specifically?"**
   - *Strategy:* Express awareness of {company}'s market position in Bangladesh and explain how this role represents your growth trajectory.

#### 2. 🇧🇩 Bangladesh Corporate Interview Etiquette:
- **Punctuality & Link Testing:** If Google Meet/Zoom, join 5 minutes early. Ensure your camera background is clean and audio is clear.
- **Formal Address:** Address panel members respectfully ("Sir/Ma'am" or appropriate professional address).
- **Salary Negotiation Guidance:** If asked for expected salary, reference prevailing market compensation for {job_title} in Dhaka/Chittagong.

#### 3. 💡 High-Impact Questions to Ask the Hiring Manager:
1. "What are the most critical deliverables for this {job_title} role in the first 90 days?"
2. "How does {company}'s leadership support professional development and team upskilling?"
3. "What are the immediate next steps in your recruitment timeline?"
"""
    return {"success": True, "prep_content": content}

# ==============================================================================
# 4. BANGLADESH SALARY INTELLIGENCE & EXPECTED SALARY ENGINE
# ==============================================================================
def resolve_job_salary(job: dict, default_industry: str = "") -> dict:
    """
    Resolves the salary for a job circular:
    1. EXACT SALARY OFFERED FROM WEBSITE:
       If the company provided a concrete numerical salary range on the website or circular
       (e.g., 'BDT 20,000 - BDT 25,000/monthly', '৳40,000 - ৳55,000', '18,000 - 24,000', 'Up to BDT 7,000/monthly'),
       preserves and standardizes the exact offer from the website, badging it with '🏢 Exact Company Offered'.
    2. EXPECTED SALARY ACCORDING TO BANGLADESH CONTEXT:
       If the company did NOT offer any salary range (marked 'Negotiable', 'Competitive', 'As per company policy',
       'Not Specified', or left blank), calculates the realistic expected salary according to Bangladesh
       employment context based on role scope, seniority, and industry corridor. Badged with '🇧🇩 Expected Salary (BD Context)'.
    """
    raw_salary = (job.get("salary") or "").strip()
    title = (job.get("job_title") or "").lower()
    desc = (job.get("job_desc") or "").lower()
    ind = (default_industry or job.get("industry") or "").lower()

    # Check if raw_salary contains actual numbers or digits
    has_digits = bool(re.search(r'\d', raw_salary))
    is_pure_placeholder = any(
        ph in raw_salary.lower() for ph in [
            "negotiable", "competitive", "as per company policy", 
            "not specified", "undisclosed", "attractive package",
            "n/a", "none", "check circular"
        ]
    ) and not has_digits

    is_exact_company = bool(raw_salary and has_digits and not is_pure_placeholder)

    if is_exact_company:
        # Standardize & clean the exact company offered salary from the website
        cleaned = raw_salary
        # Strip duplicate /monthly or / month or per month
        cleaned_no_suffix = re.sub(r'(\s*/\s*monthly|\s*/\s*month|\s*per\s*month|\s*monthly)$', '', cleaned, flags=re.I).strip()
        
        # Standardize currency symbols anywhere in the string
        display_amt = cleaned_no_suffix.replace("BDT", "৳").replace("bdt", "৳").replace("Tk.", "৳").replace("Tk", "৳").strip()
        display_amt = re.sub(r'৳\s+', '৳', display_amt)

        # If it's a range like 18,000 - 24,000 or ৳18,000 - 24,000, standardize to ৳18,000 - ৳24,000
        display_amt = re.sub(r'৳?\s*([\d,]{4,})\s*-\s*৳?\s*([\d,]{4,})', r'৳\1 - ৳\2', display_amt)

        # If no currency symbol exists anywhere in display_amt, add ৳
        if "৳" not in display_amt:
            if re.match(r'^(up to|approx\.?|around)\s+', display_amt, flags=re.I):
                display_amt = re.sub(r'^(up to|approx\.?|around)\s+', r'\1 ৳', display_amt, flags=re.I)
            else:
                display_amt = f"৳{display_amt}"

        return {
            "display": f"{display_amt} / month",
            "short": display_amt,
            "is_exact_company": True,
            "is_estimate": False,
            "source": "website_offered",
            "badge": "🏢 Exact Company Offered",
            "badge_short": "Company Offered",
            "website_stated": raw_salary,
            "label": "Exact Salary from Website (Company Offered)",
            "raw": raw_salary
        }

    # ==============================================================================
    # 2. EXPECTED SALARY ACCORDING TO BANGLADESH CONTEXT
    # (When company did not offer any salary range or marked Negotiable)
    # ==============================================================================
    # 1. Tech / Software / Architecture
    if any(k in title for k in ["lead", "architect", "principal", "engineering manager", "cto", "tech lead"]):
        approx_range = "৳90,000 - ৳150,000"
    elif any(k in title for k in ["senior software", "senior developer", "senior full", "senior backend", "senior frontend", "sr. software"]):
        approx_range = "৳80,000 - ৳125,000"
    elif any(k in title for k in ["devops", "cloud engineer", "sre", "machine learning", "data scientist", "ai engineer"]):
        approx_range = "৳65,000 - ৳105,000"
    elif any(k in title for k in ["software engineer", "developer", "programmer", "full stack", "fullstack", "backend", "frontend", "django", "react", "next.js", "node", "web developer"]):
        approx_range = "৳45,000 - ৳75,000"
    elif any(k in title for k in ["sqa", "qa engineer", "software tester", "quality assurance engineer", "automation tester"]):
        approx_range = "৳35,000 - ৳58,000"
    elif any(k in title for k in ["ui/ux", "product designer", "ux designer", "ui designer"]):
        approx_range = "৳40,000 - ৳68,000"
    elif any(k in title for k in ["video editor", "reels", "motion graphics", "animator", "multimedia", "cinematographer"]):
        approx_range = "৳32,000 - ৳50,000"
    elif any(k in title for k in ["graphic designer", "visual designer", "creative designer"]):
        approx_range = "৳28,000 - ৳44,000"

    # 2. Banking, Finance, FinTech & Operations
    elif any(k in title for k in ["mto", "management trainee"]):
        approx_range = "৳50,000 - ৳70,000"
    elif any(k in title for k in ["branch manager", "senior manager", "head of", "director"]):
        approx_range = "৳85,000 - ৳135,000"
    elif any(k in title for k in ["fintech", "product operations", "operations specialist", "operations executive"]):
        approx_range = "৳45,000 - ৳70,000"
    elif any(k in title for k in ["accountant", "accounts executive", "finance executive", "audit officer"]):
        approx_range = "৳32,000 - ৳52,000"

    # 3. Garments, Textile, Merchandising & Supply Chain
    elif any(k in title for k in ["senior merchandiser", "merchandising manager"]):
        approx_range = "৳70,000 - ৳110,000"
    elif any(k in title for k in ["assistant merchandiser", "asst. merchandiser"]):
        approx_range = "৳28,000 - ৳42,000"
    elif any(k in title for k in ["merchandiser", "woven", "knit", "apparel"]):
        approx_range = "৳40,000 - ৳65,000"
    elif any(k in title for k in ["supply chain", "procurement", "logistics executive"]):
        approx_range = "৳38,000 - ৳62,000"
    elif any(k in title for k in ["aql", "quality controller", "qa officer", "fabric inspector"]):
        approx_range = "৳30,000 - ৳45,000"

    # 4. Marketing, Sales & HR
    elif any(k in title for k in ["digital marketing", "seo specialist", "social media manager", "performance marketer"]):
        approx_range = "৳32,000 - ৳52,000"
    elif any(k in title for k in ["content writer", "copywriter"]):
        approx_range = "৳26,000 - ৳42,000"
    elif any(k in title for k in ["hr manager", "human resources manager"]):
        approx_range = "৳65,000 - ৳95,000"
    elif any(k in title for k in ["hr executive", "talent acquisition", "recruiter", "people operations"]):
        approx_range = "৳32,000 - ৳48,000"
    elif any(k in title for k in ["sales executive", "business development", "key account", "tele sales"]):
        approx_range = "৳28,000 - ৳45,000 + Incentive"

    # 5. Generic Levels
    elif any(k in title for k in ["intern", "internship", "apprentice"]):
        approx_range = "৳15,000 - ৳25,000"
    elif any(k in title for k in ["junior", "entry", "fresh", "trainee", "associate", "jr."]):
        approx_range = "৳28,000 - ৳42,000"
    elif any(k in title for k in ["senior", "sr."]):
        approx_range = "৳65,000 - ৳95,000"
    elif any(k in title for k in ["manager", "supervisor"]):
        approx_range = "৳55,000 - ৳85,000"
    else:
        # Default BD Corporate Benchmark
        if "it" in ind or "software" in ind:
            approx_range = "৳42,000 - ৳65,000"
        elif "bank" in ind or "finance" in ind:
            approx_range = "৳40,000 - ৳65,000"
        elif "garment" in ind or "textile" in ind:
            approx_range = "৳35,000 - ৳55,000"
        else:
            approx_range = "৳35,000 - ৳52,000"

    website_note = raw_salary if raw_salary else "Negotiable / Not Disclosed"
    return {
        "display": f"Expected: {approx_range} / month",
        "short": f"Expected: {approx_range}",
        "is_exact_company": False,
        "is_estimate": True,
        "source": "bangladesh_context",
        "badge": "🇧🇩 Expected Salary (BD Context)",
        "badge_short": "Expected (BD Context)",
        "website_stated": website_note,
        "label": "Expected Salary (Bangladesh Context)",
        "raw": raw_salary
    }

