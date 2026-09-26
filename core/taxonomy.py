"""
Bangladesh Job Taxonomy & Geographic Classifications.
Comprehensive catalog covering 14+ sectors, 150+ industry job titles,
and geographic distributions across all 8 divisions and 64 districts in Bangladesh.
"""

BD_DIVISIONS_AND_DISTRICTS = {
    "Dhaka": [
        "Dhaka (Gulshan / Banani / Mohakhali)",
        "Dhaka (Uttara / Tongi)",
        "Dhaka (Motijheel / Dilkusha / Paltan)",
        "Dhaka (Kawran Bazar / Tejgaon / Farmgate)",
        "Dhaka (Dhanmondi / Mohammadpur)",
        "Dhaka (Mirpur / Pallabi)",
        "Dhaka (Old Dhaka / Lalbagh / Sadarghat)",
        "Gazipur (Tongi / Board Bazar / Joydebpur)",
        "Narayanganj",
        "Narsingdi",
        "Munshiganj",
        "Manikganj",
        "Tangail",
        "Faridpur",
        "Gopalganj",
        "Madaripur",
        "Rajbari",
        "Shariatpur",
        "Kishoreganj"
    ],
    "Chattogram": [
        "Chattogram (Agrabad / GEC / Nasirabad)",
        "Chattogram (EPZ / Halishahar / Port Area)",
        "Cox's Bazar",
        "Cumilla",
        "Feni",
        "Brahmanbaria",
        "Noakhali",
        "Chandpur",
        "Lakshmipur",
        "Rangamati",
        "Khagrachhari",
        "Bandarban"
    ],
    "Rajshahi": [
        "Rajshahi",
        "Bogura",
        "Pabna",
        "Sirajganj",
        "Naogaon",
        "Natore",
        "Chapai Nawabganj",
        "Joypurhat"
    ],
    "Khulna": [
        "Khulna",
        "Jashore",
        "Kushtia",
        "Satkhira",
        "Bagerhat",
        "Jhenaidah",
        "Chuadanga",
        "Magura",
        "Meherpur",
        "Narail"
    ],
    "Sylhet": [
        "Sylhet (Zindabazar / Shahjalal / Subidbazar)",
        "Moulvibazar",
        "Habiganj",
        "Sunamganj"
    ],
    "Barishal": [
        "Barishal",
        "Patuakhali",
        "Bhola",
        "Pirojpur",
        "Jhalokati",
        "Barguna"
    ],
    "Rangpur": [
        "Rangpur",
        "Dinajpur",
        "Gaibandha",
        "Kurigram",
        "Lalmonirhat",
        "Nilphamari",
        "Panchagarh",
        "Thakurgaon"
    ],
    "Mymensingh": [
        "Mymensingh",
        "Jamalpur",
        "Netrokona",
        "Sherpur"
    ],
    "Remote / Work From Home": [
        "Remote (Bangladesh)",
        "Remote (Worldwide / International)",
        "Hybrid (Dhaka)",
        "Hybrid (Chattogram)"
    ]
}

# Exhaustive industry-specific job taxonomy in Bangladesh
BD_JOB_TAXONOMY = {
    "IT & Software Engineering": [
        "All IT & Software Roles",
        "Junior Software Engineer",
        "Software Engineer (Full Stack)",
        "Backend Developer (Python / Django)",
        "Backend Developer (Node.js / Express)",
        "Backend Developer (Java / Spring Boot)",
        "Backend Developer (PHP / Laravel)",
        "Backend Developer (.NET / C#)",
        "Frontend Developer (React / Next.js)",
        "Frontend Developer (Vue.js / Angular)",
        "Mobile App Developer (Flutter / React Native)",
        "Android / iOS Native Developer",
        "Software Quality Assurance (SQA) Engineer",
        "Automation Test Engineer",
        "DevOps / Cloud Engineer (AWS / GCP / Docker)",
        "UI/UX Designer & Product Designer",
        "Data Analyst / BI Specialist",
        "Data Engineer / ETL Developer",
        "Machine Learning / AI Engineer",
        "Database Administrator (DBA / MySQL / PostgreSQL)",
        "Network & System Administrator",
        "Cybersecurity Specialist / SOC Analyst",
        "IT Support Engineer / Desktop Support",
        "Technical Project Manager / Scrum Master"
    ],
    "Banking, NBFI & FinTech": [
        "All Banking & FinTech Roles",
        "Management Trainee Officer (MTO)",
        "Probationary Officer (PO)",
        "Assistant Officer (General Banking)",
        "Cash Officer / Teller",
        "Credit Analyst / Underwriter",
        "Relationship Manager (Corporate Banking)",
        "SME & Retail Loan Officer",
        "Trade Finance / Foreign Exchange (Forex) Officer",
        "Risk Management Officer",
        "Internal Audit Officer (Banking)",
        "Compliance & AML/CFT Officer",
        "FinTech Operations Executive (MFS / Agent Banking)",
        "Cards & Digital Banking Executive",
        "Investment Banking / Equity Research Analyst",
        "Microfinance Field Officer"
    ],
    "Garments, Textile & RMG Sector": [
        "All Garments & RMG Roles",
        "Trainee Merchandiser",
        "Assistant Merchandiser (Woven / Knit / Sweater)",
        "Merchandiser (Woven / Knit)",
        "Senior Merchandiser / Team Leader",
        "Production Planning & Control (PPC) Officer",
        "Industrial Engineering (IE) Executive",
        "Quality Assurance (QA) Manager / Inspector",
        "Pattern Master / CAD Specialist",
        "Fabric & Accessories Sourcing Executive",
        "Textile Engineer (Dyeing / Printing / Finishing)",
        "Apparel Washing Specialist",
        "RMG Compliance Officer / Sustainability Executive",
        "Supply Chain & Commercial Executive (LC / Export-Import)",
        "Sample Section Coordinator"
    ],
    "Marketing, Sales & Business Development": [
        "All Marketing & Sales Roles",
        "Business Development Executive (BDE)",
        "Key Account Manager (KAM)",
        "Digital Marketing Specialist (SEO / SEM / Social)",
        "Content Writer & Copywriter",
        "Social Media Manager / Community Executive",
        "Brand Executive / Assistant Brand Manager",
        "Area Sales Manager (ASM)",
        "Territory Sales Officer (TSO / FMCG)",
        "Corporate Sales Executive (B2B)",
        "E-Commerce Operations Executive",
        "Growth Marketer / Performance Marketer",
        "Market Research & Insights Analyst"
    ],
    "Supply Chain, Procurement & Logistics": [
        "All Supply Chain Roles",
        "Supply Chain Management Trainee / Officer",
        "Procurement & Purchase Executive",
        "Inventory & Warehouse Manager",
        "Logistics & Distribution Coordinator",
        "Import-Export (Commercial) Executive",
        "Fleet & Transport Supervisor",
        "Freight Forwarding / Shipping Executive",
        "Customs Clearance (C&F) Coordinator"
    ],
    "Accounting, Finance & Audit": [
        "All Accounting & Finance Roles",
        "Accounts Executive / Officer",
        "Senior Accountant / Chief Accountant",
        "Finance Executive / Financial Analyst",
        "Internal Auditor",
        "Tax & VAT Consultant / Executive",
        "Cost & Management Accountant (CMA / CA CC)",
        "Billing & Collection Officer",
        "Payroll Specialist"
    ],
    "NGO, Development & Social Impact": [
        "All NGO & Development Roles",
        "Project Coordinator / Project Officer",
        "Monitoring, Evaluation & Learning (MEL / M&E) Officer",
        "Field Facilitator / Community Mobilizer",
        "Humanitarian Emergency Response Assistant",
        "WASH Specialist / Officer",
        "Livelihoods & Food Security Officer",
        "Child Protection & Gender Specialist",
        "Grant Management & Reporting Specialist",
        "Fundraising & Donor Relations Executive"
    ],
    "Government, Autonomous Bodies & Public Sector": [
        "All Government & Autonomous Roles",
        "9th Grade Officer (General / Cadre equivalent)",
        "10th Grade Sub-Assistant Engineer / Officer",
        "Assistant Director (Administration / Research)",
        "Administrative Officer (AO) / Section Officer",
        "Sub-Inspector / Armed Forces Officer Cadet",
        "Primary School Teacher / Assistant Teacher",
        "Data Entry Operator / Computer Typist",
        "Teletalk AllJobs Automated Circular Tracking"
    ],
    "Pharmaceuticals, Healthcare & Medical": [
        "All Pharmaceuticals & Healthcare Roles",
        "Medical Promotion Officer (MPO / Medical Representative)",
        "Product Executive / Brand Executive (Pharma)",
        "Quality Control (QC) Chemist",
        "Quality Assurance (QA) Officer (Pharma)",
        "Regulatory Affairs Officer",
        "Research & Development (R&D) Officer",
        "Hospital Administrator / Floor Supervisor",
        "Clinical Laboratory Technologist",
        "Registered Nurse / Healthcare Assistant"
    ],
    "Human Resources & Administration": [
        "All HR & Admin Roles",
        "HR Executive (Generalist)",
        "Talent Acquisition / Recruitment Specialist",
        "Training & Development Officer",
        "HR Operations & Payroll Executive",
        "Admin & Facilities Executive",
        "Executive Assistant to CEO / Director (EA)",
        "Office Manager / Receptionist"
    ],
    "Education, Training & Research": [
        "All Education & Teaching Roles",
        "University Lecturer (Engineering / Business / English)",
        "English Medium / Cambridge Curriculum Teacher",
        "Higher Secondary / College Teacher",
        "Academic Counselor / Student Advisor",
        "Educational Content Creator / Trainer",
        "Research Assistant (RA) / Research Associate"
    ],
    "Customer Support, BPO & Telemarketing": [
        "All Customer Support & BPO Roles",
        "Customer Service Representative (CSR)",
        "Call Center Agent (Inbound / Outbound)",
        "Telemarketing Executive (English / Bengali)",
        "Technical Support Executive",
        "Customer Success Executive (SaaS)",
        "Chat & Email Support Specialist"
    ],
    "Media, Creative Arts & Design": [
        "All Creative & Media Roles",
        "Graphic Designer (Print & Digital)",
        "Motion Graphics Artist & Animator",
        "Video Editor (Premiere Pro / After Effects)",
        "Journalist / Sub-Editor (Newsroom)",
        "Video Producer / Cinematographer",
        "Voiceover Artist / Scriptwriter"
    ],
    "Engineering (Civil, Electrical, Mechanical)": [
        "All Engineering Roles",
        "Site Engineer (Civil / Construction)",
        "Electrical Engineer (Substation / Generator)",
        "Mechanical Engineer (Maintenance & HVAC)",
        "AutoCAD / BIM Draftsman",
        "Project Engineer (EPC / Infrastructure)",
        "Safety & EHS Officer"
    ],
    "Fresh Graduate & Trainee Programs": [
        "All Fresh Graduate Roles",
        "Management Trainee Officer (Any Discipline)",
        "Graduate Trainee (Engineering / Sales / HR)",
        "Paid Intern (Full-time / Part-time)",
        "Executive Trainee (Fast-track Leadership)",
        "Entry-Level Junior Executive"
    ]
}

JOB_TYPES = [
    "Any Job Type",
    "Full Time (স্থায়ী)",
    "Contractual / Project-based (চুক্তিভিত্তিক)",
    "Part Time (খণ্ডকালীন)",
    "Internship (ইন্টার্নশিপ)",
    "Trainee Program (প্রশিক্ষণার্থী)",
    "Remote / Work From Home"
]

EXPERIENCE_LEVELS = [
    "Any Experience Level",
    "Fresh Graduate / No Experience Required (০ বছর)",
    "Entry Level (১ - ২ বছর)",
    "Mid Level (৩ - ৫ বছর)",
    "Senior Level (৫ - ৮ বছর)",
    "Executive / Leadership (৮+ বছর)"
]

def get_all_job_titles():
    """Returns a flattened, deduplicated list of all job titles across Bangladesh sectors."""
    titles = set()
    for category, role_list in BD_JOB_TAXONOMY.items():
        for role in role_list:
            if not role.startswith("All "):
                titles.add(role)
    return sorted(list(titles))

def get_all_districts():
    """Returns a flattened list of all Bangladesh districts and commercial zones."""
    districts = []
    for div, d_list in BD_DIVISIONS_AND_DISTRICTS.items():
        districts.extend(d_list)
    return districts
