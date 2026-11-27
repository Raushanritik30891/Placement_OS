"""Seed an employer directory with career portals, not unverified hiring claims.

Company pages are starting points only. Eligibility, hiring tracks and assessment
patterns remain explicitly pending until a dated research source is added.
"""
from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models.entities import CompanyProfile

COMPANIES = [
    ("TCS", "tcs", "service", "https://www.tcs.com/careers", ["Graduate opportunities", "Campus hiring"], "Explore TCS career opportunities. Individual campus tracks and eligibility require cycle-specific verification."),
    ("Infosys", "infosys", "service", "https://www.infosys.com/careers.html", ["Graduate opportunities", "Specialist roles"], "Explore graduate and early-career opportunities. Assessment formats require cycle-specific verification."),
    ("Wipro", "wipro", "service", "https://careers.wipro.com/", ["Early careers", "Graduate roles"], "Explore Wipro's official career portal. Role eligibility and campus tracks require verification."),
    ("HCLTech", "hcltech", "service", "https://www.hcltech.com/careers", ["Early careers", "Graduate roles"], "Explore HCLTech career opportunities. Hiring patterns are not asserted here."),
    ("Accenture", "accenture", "service", "https://www.accenture.com/in-en/careers", ["Students and graduates", "Entry-level roles"], "Explore Accenture India student and graduate opportunities."),
    ("Cognizant", "cognizant", "service", "https://careers.cognizant.com/india-en/", ["Students and graduates", "Entry-level roles"], "Explore Cognizant India opportunities. Specific hiring criteria must be checked in each job posting."),
    ("Capgemini", "capgemini", "service", "https://www.capgemini.com/in-en/careers/", ["Students and graduates", "Graduate roles"], "Explore Capgemini India careers and graduate opportunities."),
    ("LTIMindtree", "ltimindtree", "service", "https://www.ltimindtree.com/careers/", ["Early careers", "Graduate roles"], "Explore LTIMindtree career opportunities. Role and assessment details remain pending research."),
    ("Tech Mahindra", "tech-mahindra", "service", "https://careers.techmahindra.com/", ["Campus opportunities", "Entry-level roles"], "Explore Tech Mahindra's official career portal."),
    ("Deloitte", "deloitte", "professional-services", "https://www.deloitte.com/in/en/careers.html", ["Students", "Graduate opportunities"], "Explore Deloitte India opportunities. Team, location and role eligibility vary by posting."),
    ("IBM", "ibm", "technology-services", "https://www.ibm.com/careers", ["Early careers", "Entry-level roles"], "Explore IBM careers and early-career roles."),
    ("DXC Technology", "dxc-technology", "technology-services", "https://careers.dxc.com/", ["Early careers", "Entry-level roles"], "Explore DXC Technology's official careers portal."),
    ("Persistent Systems", "persistent-systems", "technology-services", "https://careers.persistent.com/", ["Graduate roles", "Early careers"], "Explore Persistent Systems career opportunities."),
    ("Amazon", "amazon", "product", "https://www.amazon.jobs/en/locations/india", ["Students", "University talent", "Entry-level roles"], "Explore Amazon India roles. Qualification and interview process vary by role."),
    ("Microsoft", "microsoft", "product", "https://careers.microsoft.com/v2/global/en/locations/india", ["Students and graduates", "University roles"], "Explore Microsoft India career opportunities."),
    ("Google", "google", "product", "https://www.google.com/about/careers/applications/locations/india/", ["Students", "Early careers"], "Explore Google India roles. Role-specific requirements must be read from the official posting."),
    ("Adobe", "adobe", "product", "https://careers.adobe.com/us/en", ["Students and new graduates", "Entry-level"], "Explore Adobe careers and student opportunities."),
    ("Oracle", "oracle", "product", "https://www.oracle.com/in/careers/", ["Students and graduates", "Entry-level roles"], "Explore Oracle India career opportunities."),
    ("Walmart Global Tech", "walmart-global-tech", "product", "https://careers.walmart.com/", ["Early careers", "Technology roles"], "Explore Walmart careers. India technology roles and graduate eligibility must be checked per posting."),
    ("Flipkart", "flipkart", "product", "https://www.flipkartcareers.com/", ["Early careers", "Technology roles"], "Explore Flipkart's official careers portal."),
    ("Salesforce", "salesforce", "product", "https://careers.salesforce.com/en/", ["Students and graduates", "Entry-level roles"], "Explore Salesforce career opportunities."),
    ("Cisco", "cisco", "product", "https://jobs.cisco.com/", ["Early careers", "Internships", "Graduate roles"], "Explore Cisco's official jobs portal."),
    ("Qualcomm", "qualcomm", "product", "https://careers.qualcomm.com/careers", ["University opportunities", "Entry-level roles"], "Explore Qualcomm career opportunities."),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for name, slug, category, url, tracks, description in COMPANIES:
            company = db.scalar(select(CompanyProfile).where(CompanyProfile.slug == slug))
            if company is None:
                db.add(CompanyProfile(
                    name=name,
                    slug=slug,
                    category=category,
                    career_url=url,
                    hiring_tracks=tracks,
                    description=description,
                    research_status="pending",
                    last_verified_at=None,
                    is_published=True,
                ))
        db.commit()


if __name__ == "__main__":
    seed()
