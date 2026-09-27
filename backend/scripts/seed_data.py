"""Real ADAPPT 5.0 content shared by both scripts/seed.py (dev, adds demo
data on top) and scripts/bootstrap.py (production, real content only).

Keeping this in one place means the domain/problem-statement text — sourced
from ADAPPT_Final_3_Domains_3_Problems.pdf — is defined exactly once.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import CompetitionSettings, Domain, ProblemStatement
from app.models.enums import DomainStatus, PublishStatus

DOMAINS = [
    {
        "slug": "cybersecurity-smart-homes",
        "name": "Cybersecurity in Smart Homes",
        "description": (
            "Cybersecurity in Smart Homes focuses on protecting connected household devices, "
            "networks, and users from digital threats. As homes increasingly rely on smart "
            "cameras, locks, appliances, assistants, and other connected devices, vulnerabilities "
            "can arise from weak configurations, unauthorized access, insecure communication, and "
            "poor visibility of connected devices."
        ),
    },
    {
        "slug": "ai-foodtech",
        "name": "AI in FoodTech",
        "description": (
            "AI in FoodTech focuses on applying computational intelligence to challenges across "
            "the food ecosystem, from food quality and safety to consumption, waste, "
            "personalization, and resource efficiency. The domain allows participants to explore "
            "how data and AI can improve the way food is produced, assessed, distributed, "
            "consumed, and managed."
        ),
    },
    {
        "slug": "robotics-disaster-management",
        "name": "Robotics and Automation in Natural Disaster Management",
        "description": (
            "Robotics & Automation in Natural Disaster Management focuses on using intelligent "
            "robotic systems, autonomous technologies, and automated decision-making to improve "
            "disaster preparedness, response, and recovery. Natural disasters such as floods, "
            "earthquakes, cyclones, landslides, and wildfires often create environments that are "
            "dangerous, inaccessible, or rapidly changing, making it difficult for humans to "
            "continuously monitor conditions and carry out rescue and relief operations."
        ),
    },
]

# Three problem statements per domain, in display order — verbatim from
# ADAPPT_Final_3_Domains_3_Problems.pdf.
PROBLEM_STATEMENTS = {
    "cybersecurity-smart-homes": [
        {
            "title": "Unauthorized Access to Connected Devices",
            "description": (
                "Smart homes can contain dozens of connected devices, often managed through "
                "different applications and accounts. A compromised device, weak authentication "
                "mechanism, or poorly secured connection can allow unauthorized users to gain "
                "access to other devices or sensitive household information. The challenge is "
                "preventing one vulnerable point from becoming a pathway into the wider home "
                "environment."
            ),
        },
        {
            "title": "Lack of Visibility into Smart Home Security",
            "description": (
                "Homeowners often have limited understanding of which devices are connected to "
                "their network, what information those devices exchange, and whether unusual "
                "activity is taking place. This lack of visibility makes it difficult to "
                "recognize weak points, investigate suspicious behaviour, or identify potential "
                "security risks before they develop into serious threats."
            ),
        },
        {
            "title": "Vulnerabilities in Shared Smart Home Access",
            "description": (
                "Smart homes frequently allow access to family members, guests, domestic staff, "
                "or service providers. Managing different levels of access across multiple "
                "devices can be difficult, especially when permissions need to change over time. "
                "Users may retain access to devices or information they no longer need, creating "
                "avoidable security and privacy risks."
            ),
        },
    ],
    "ai-foodtech": [
        {
            "title": "Food Waste from Demand Uncertainty",
            "description": (
                "Food businesses such as restaurants, cafeterias, and retailers often struggle to "
                "accurately estimate daily demand. Demand can fluctuate because of day-to-day "
                "behaviour, events, weather, seasonality, and other factors. Overestimating "
                "demand can lead to significant food waste, while underestimating demand can "
                "result in shortages and reduced availability."
            ),
        },
        {
            "title": "Difficulty in Identifying Food Quality Issues",
            "description": (
                "Food quality can deteriorate due to storage conditions, handling, temperature, "
                "contamination risks, and time. Detecting quality problems early can be "
                "difficult, particularly when large quantities of food need to be monitored "
                "consistently. Delayed identification can increase the likelihood of unsafe or "
                "wasted food reaching the next stage of the supply chain."
            ),
        },
        {
            "title": "Limited Personalization of Food Choices",
            "description": (
                "People often make food choices without having an easy way to consider their "
                "individual preferences, dietary requirements, nutritional goals, and available "
                "food options together. This becomes more difficult when menus and food "
                "inventories change frequently, making it harder to identify choices that are "
                "suitable for a person's needs."
            ),
        },
    ],
    "robotics-disaster-management": [
        {
            "title": "Autonomous Operation in Unpredictable and Hazardous Environments",
            "description": (
                "Disaster sites are highly dynamic environments where roads may be blocked, "
                "buildings may collapse, terrain may become unstable, and visibility or "
                "communication can change rapidly. Robots may encounter debris, water, fire, "
                "unstable structures, or unexpected obstacles that make pre-planned routes and "
                "actions ineffective. The challenge is enabling autonomous systems to perceive "
                "changing surroundings, navigate safely, adapt their plans in real time, and "
                "continue useful operation despite uncertainty and limited human intervention."
            ),
        },
        {
            "title": "Automated Search, Rescue and Rapid Assessment of Affected Areas",
            "description": (
                "After a disaster, people may be trapped inside damaged buildings, stranded in "
                "flooded areas, isolated by landslides, or located in regions that are unsafe for "
                "emergency personnel to immediately enter. At the same time, responders need "
                "timely information about damaged buildings, blocked routes, infrastructure "
                "failures, and other hazards across large areas. The challenge is enabling "
                "robotic and automated systems to locate people, assess damage and risk, and "
                "provide actionable situational information quickly while reducing the need to "
                "expose human responders to dangerous environments."
            ),
        },
        {
            "title": "Intelligent Coordination of Robots, Responders and Critical Resources",
            "description": (
                "Disaster response can involve multiple robots, rescue teams, medical units, "
                "vehicles, shelters, communication systems, and essential supplies operating "
                "simultaneously across different locations. Communication networks may be "
                "damaged or unreliable, while priorities can change rapidly as new incidents are "
                "identified. Without effective coordination, robots may duplicate tasks, conflict "
                "with one another, take inefficient routes, or leave critical areas underserved. "
                "The challenge is to enable autonomous systems and human responders to share "
                "information, coordinate tasks and resources, and make appropriate decisions as "
                "the disaster situation evolves."
            ),
        },
    ],
}


def seed_domains_and_problem_statements(db: Session) -> dict[str, Domain]:
    domains_by_slug = {}
    for d in DOMAINS:
        domain = db.query(Domain).filter_by(slug=d["slug"]).one_or_none()
        if domain is None:
            domain = Domain(status=DomainStatus.ACTIVE, **d)
            db.add(domain)
            db.flush()
            print(f"Created domain: {domain.name}")
        else:
            domain.description = d["description"]
        domains_by_slug[d["slug"]] = domain
    db.commit()

    for slug, statements in PROBLEM_STATEMENTS.items():
        domain = domains_by_slug[slug]
        for order_index, ps_data in enumerate(statements, start=1):
            existing = (
                db.query(ProblemStatement)
                .filter_by(domain_id=domain.id, order_index=order_index)
                .one_or_none()
            )
            if existing is None:
                db.add(
                    ProblemStatement(
                        domain_id=domain.id,
                        order_index=order_index,
                        status=PublishStatus.PUBLISHED,
                        **ps_data,
                    )
                )
                print(f"Created problem statement {order_index} for: {domain.name}")
            else:
                existing.title = ps_data["title"]
                existing.description = ps_data["description"]
    db.commit()

    return domains_by_slug


def seed_round1_settings(db: Session) -> CompetitionSettings:
    """ADAPPT 5.0 — Round 1 (Idea Pitch) submission deadline is 17 Oct 2026,
    12:00 AM IST, per the official event description. submission_start is
    left at "already open" — an admin should adjust it from the Competition
    Settings page once the real opening date is decided.
    """
    ist = timezone(timedelta(hours=5, minutes=30))
    round1_deadline = datetime(2026, 10, 17, 0, 0, tzinfo=ist)

    settings_row = db.query(CompetitionSettings).filter_by(round_key="round_1").one_or_none()
    if settings_row is None:
        settings_row = CompetitionSettings(
            round_key="round_1",
            round_label="Round 1 — Idea Pitch",
            submission_start=datetime.now(timezone.utc) - timedelta(days=1),
            submission_end=round1_deadline,
            allow_replacement=True,
            max_document_size_mb=25,
            max_video_size_mb=300,
            allowed_document_extensions="pdf,ppt,pptx",
            allowed_video_extensions="mp4,mov,webm",
        )
        db.add(settings_row)
        print("Created Round 1 competition settings (deadline: 17 Oct 2026, 12:00 AM IST).")
    else:
        settings_row.round_label = "Round 1 — Idea Pitch"
        settings_row.submission_end = round1_deadline
    db.commit()
    return settings_row
