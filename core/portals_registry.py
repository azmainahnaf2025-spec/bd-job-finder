"""
Registry and Search URL Formatter for All Major Bangladesh Job Portals and Circular Hubs.
Includes private corporate portals, government/Teletalk boards, NGO registries,
and social recruiting networks.
"""

import urllib.parse

BD_JOB_PORTALS = {
    "bdjobs": {
        "name": "BDJobs",
        "category": "Corporate & General",
        "base_url": "https://www.bdjobs.com",
        "search_url_template": "https://jobs.bdjobs.com/jobsearch.asp?fcatId=0&txtsearch={query}",
        "description": "The pioneer and largest employment board in Bangladesh covering private, multinational, and NGO vacancies.",
        "icon": "💼",
        "color": "#1f77b4",
        "has_live_scraper": True,
        "badge": "Leading Portal"
    },
    "alljobs_teletalk": {
        "name": "AllJobs Teletalk",
        "category": "Government & Autonomous",
        "base_url": "https://alljobs.teletalk.com.bd",
        "search_url_template": "https://alljobs.teletalk.com.bd/jobs/all?keyword={query}",
        "description": "Official gateway for Government Ministries, Autonomous Directorates, Public Banks, and State Universities in Bangladesh.",
        "icon": "🏛️",
        "color": "#27ae60",
        "has_live_scraper": True,
        "badge": "Official Govt Gateway"
    },
    "chakri_com": {
        "name": "Chakri.com",
        "category": "Corporate & General",
        "base_url": "https://www.chakri.com",
        "search_url_template": "https://www.chakri.com/spotlight/search?q={query}",
        "description": "One of the longest-standing recruitment and job circular directories in Bangladesh.",
        "icon": "📄",
        "color": "#d35400",
        "has_live_scraper": True,
        "badge": "Pioneer Directory"
    },
    "skill_jobs": {
        "name": "Skill.jobs",
        "category": "Skills & Assessments",
        "base_url": "https://skill.jobs",
        "search_url_template": "https://skill.jobs/jobs?search={query}",
        "description": "Skill-first employment and talent matching platform for tech, corporate, and entry-level talent.",
        "icon": "⚡",
        "color": "#e67e22",
        "has_live_scraper": True,
        "badge": "Skills First"
    },
    "careerjet_bd": {
        "name": "Careerjet Bangladesh",
        "category": "Meta-Aggregator",
        "base_url": "https://www.careerjet.com.bd",
        "search_url_template": "https://www.careerjet.com.bd/search/jobs?s={query}&l={location}",
        "description": "Search aggregator scanning thousands of employer websites and career portals across Bangladesh.",
        "icon": "✈️",
        "color": "#2062af",
        "has_live_scraper": True,
        "badge": "Aggregator"
    },
    "ejobs_bd": {
        "name": "eJobs Bangladesh",
        "category": "Corporate & IT",
        "base_url": "https://www.ejobs.com.bd",
        "search_url_template": "https://www.ejobs.com.bd/jobs?keyword={query}",
        "description": "Corporate platform for executive, tech, sales, and management openings across Dhaka.",
        "icon": "🤖",
        "color": "#8e44ad",
        "has_live_scraper": True,
        "badge": "Smart Jobs"
    },
    "nextjobz": {
        "name": "Nextjobz",
        "category": "Corporate & Commercial",
        "base_url": "https://nextjobz.com.bd",
        "search_url_template": "https://nextjobz.com.bd/?s={query}",
        "description": "Regularly updated with corporate, private firm, and industrial vacancies.",
        "icon": "📈",
        "color": "#e74c3c",
        "has_live_scraper": True,
        "badge": "Corporate"
    },
    "myjobs_bd": {
        "name": "Myjobs Bangladesh",
        "category": "Corporate & Commercial",
        "base_url": "https://myjobs.com.bd",
        "search_url_template": "https://myjobs.com.bd/jobs?search={query}",
        "description": "Listings across Dhaka, Chattogram, and national commercial hubs.",
        "icon": "🎯",
        "color": "#2980b9",
        "has_live_scraper": True,
        "badge": "Commercial"
    },
    "bdjobs_live": {
        "name": "BDJobs Live",
        "category": "Daily Circulars",
        "base_url": "https://www.bdjobslive.com",
        "search_url_template": "https://www.bdjobslive.com/?s={query}",
        "description": "Daily feed of corporate, commercial, and enterprise hiring alerts.",
        "icon": "📡",
        "color": "#16a085",
        "has_live_scraper": True,
        "badge": "Live Alerts"
    },
    "morejobs_bd": {
        "name": "MoreJobs BD",
        "category": "Corporate & Technical",
        "base_url": "https://morejobsbd.com",
        "search_url_template": "https://morejobsbd.com/jobs?keywords={query}",
        "description": "Professional, technical, and engineering job listings across industrial zones.",
        "icon": "🔍",
        "color": "#c0392b",
        "has_live_scraper": True,
        "badge": "Technical"
    },
    "jobmedia_bd": {
        "name": "Job Media BD",
        "category": "Classified Circulars",
        "base_url": "https://www.jobmedia.com.bd",
        "search_url_template": "https://www.jobmedia.com.bd/?s={query}",
        "description": "Categorizes openings by healthcare, engineering, banking, education, and garments.",
        "icon": "📰",
        "color": "#34495e",
        "has_live_scraper": True,
        "badge": "Classifieds"
    },
    "ngojobs_bdesh": {
        "name": "NgoJobsBdesh",
        "category": "NGO & Development",
        "base_url": "https://ngojobsbdesh.com",
        "search_url_template": "https://ngojobsbdesh.com/?s={query}",
        "description": "Premier hub for NGO, INGO, UN Agencies, and development organizations (BRAC, icddr,b, UNDP, Save the Children).",
        "icon": "🤝",
        "color": "#27ae60",
        "has_live_scraper": True,
        "badge": "NGO Exclusive"
    },
    "bdjobs_today": {
        "name": "BDJobsToday",
        "category": "Newspaper Circulars",
        "base_url": "https://bdjobstoday.com",
        "search_url_template": "https://bdjobstoday.com/?s={query}",
        "description": "Aggregator of daily newspaper print circulars (Prothom Alo, Daily Star, Ittefaq) and bank recruitment ads.",
        "icon": "🗞️",
        "color": "#f39c12",
        "has_live_scraper": True,
        "badge": "Newspaper Feed"
    },
    "linkedin_bd": {
        "name": "LinkedIn Bangladesh",
        "category": "Multinational & Professional",
        "base_url": "https://www.linkedin.com/jobs",
        "search_url_template": "https://www.linkedin.com/jobs/search/?keywords={query}&location=Bangladesh",
        "description": "Primary professional network for tech startups, multinationals, FinTech, and executive positions in Dhaka.",
        "icon": "🌐",
        "color": "#0077b5",
        "has_live_scraper": False,
        "badge": "Multinational"
    },
    "indeed_bd": {
        "name": "Indeed Bangladesh",
        "category": "Global Meta-Search",
        "base_url": "https://bd.indeed.com",
        "search_url_template": "https://bd.indeed.com/jobs?q={query}&l=Bangladesh",
        "description": "Global job engine aggregating direct employer career pages and remote openings.",
        "icon": "📌",
        "color": "#003a9b",
        "has_live_scraper": False,
        "badge": "Global"
    },
    "glassdoor_bd": {
        "name": "Glassdoor Bangladesh",
        "category": "Salary & Reviews",
        "base_url": "https://www.glassdoor.com",
        "search_url_template": "https://www.glassdoor.com/Job/bangladesh-{query}-jobs-SRCH_IL.0,10_IN24_KO11,{query_len}.htm",
        "description": "Listings paired with employer ratings, interview reviews, and salary benchmarks.",
        "icon": "🟢",
        "color": "#0caa41",
        "has_live_scraper": False,
        "badge": "Salaries & Reviews"
    },
    "facebook_jobs_bd": {
        "name": "Facebook Recruitment BD",
        "category": "Social & Direct Hiring",
        "base_url": "https://www.facebook.com",
        "search_url_template": "https://www.facebook.com/search/posts/?q={query}+hiring+Bangladesh",
        "description": "Instant recruiter circulars, startup hiring announcements, and urgent SME openings posted directly on Facebook.",
        "icon": "📘",
        "color": "#1877f2",
        "has_live_scraper": False,
        "badge": "Social Hiring"
    },
    "prothomalo_jobs": {
        "name": "Prothom Alo Chakri",
        "category": "National Newspaper",
        "base_url": "https://www.prothomalo.com/chakri",
        "search_url_template": "https://www.prothomalo.com/search?q={query}+চাকরি",
        "description": "Daily verified job circulars, government notices, and corporate hiring in Bangladesh's leading newspaper.",
        "icon": "🔴",
        "color": "#e02020",
        "has_live_scraper": False,
        "badge": "National Press"
    }
}

def get_portal_search_url(portal_key: str, query: str, location: str = "Dhaka") -> str:
    """Generates a tailored direct search URL for a given Bangladesh job portal."""
    portal = BD_JOB_PORTALS.get(portal_key)
    if not portal:
        encoded = urllib.parse.quote_plus(f"{query} {location} Bangladesh")
        return f"https://www.google.com/search?q={encoded}"

    encoded_query = urllib.parse.quote_plus(query.strip())
    encoded_loc = urllib.parse.quote_plus(location.strip())

    template = portal["search_url_template"]
    if "{query_len}" in template:
        return template.format(
            query=encoded_query,
            location=encoded_loc,
            query_len=11 + len(query.strip())
        )
    return template.format(query=encoded_query, location=encoded_loc)

def get_portals_by_category():
    """Groups portals by category for structured UI rendering."""
    categories = {}
    for key, portal in BD_JOB_PORTALS.items():
        cat = portal["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((key, portal))
    return categories
