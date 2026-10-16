import io
import json
import os
import time
from datetime import datetime
from typing import List, Optional

import requests
import streamlit as st
from fpdf import FPDF
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# Streamlit Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="FirstGig AI — Turn Skills into Side Hustles",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom Modern CSS
# ---------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
code, pre { font-family: 'JetBrains Mono', monospace !important; }

.hero-container {
    background: linear-gradient(135deg, rgba(30,27,75,0.7) 0%, rgba(15,23,42,0.8) 100%);
    border: 1px solid rgba(99,102,241,0.25); border-radius: 16px;
    padding: 28px 32px; margin-bottom: 24px;
    backdrop-filter: blur(12px); box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.hero-title {
    font-size: 2.2rem; font-weight: 800;
    background: linear-gradient(90deg,#818cf8,#c084fc,#38bdf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.hero-subtitle { color: #94a3b8; font-size: 1.05rem; line-height: 1.5; }

.card-badge {
    display: inline-block; padding: 4px 10px; border-radius: 9999px;
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; background: rgba(99,102,241,0.2);
    color: #a5b4fc; border: 1px solid rgba(99,102,241,0.4); margin-bottom: 10px;
}
.service-card {
    background: rgba(30,41,59,0.85); border: 1px solid rgba(148,163,184,0.15);
    border-radius: 14px; padding: 22px; margin-bottom: 18px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.rate-card {
    background: rgba(15,23,42,0.9); border: 1px solid rgba(56,189,248,0.2);
    border-radius: 14px; padding: 20px; text-align: center;
}
.rate-value { font-size: 1.6rem; font-weight: 800; color: #38bdf8; margin: 8px 0; }
.rate-label { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; }

.platform-card {
    background: rgba(30,41,59,0.85); border: 1px solid rgba(148,163,184,0.12);
    border-radius: 12px; padding: 20px; margin-bottom: 16px;
}
.platform-badge {
    display: inline-block; padding: 3px 10px; border-radius: 9999px;
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; margin-bottom: 10px;
}
.badge-upwork  { background: rgba(20,184,86,0.2); color:#4ade80; border:1px solid rgba(20,184,86,0.4); }
.badge-linkedin{ background: rgba(59,130,246,0.2); color:#60a5fa; border:1px solid rgba(59,130,246,0.4); }
.badge-fiverr  { background: rgba(249,115,22,0.2); color:#fb923c; border:1px solid rgba(249,115,22,0.4); }
.badge-email   { background: rgba(168,85,247,0.2); color:#c084fc; border:1px solid rgba(168,85,247,0.4); }

.status-pill-online {
    display:inline-flex;align-items:center;gap:6px;padding:4px 12px;
    border-radius:9999px;background:rgba(16,185,129,0.15);color:#34d399;
    border:1px solid rgba(16,185,129,0.3);font-size:0.82rem;font-weight:600;
}
.status-pill-offline {
    display:inline-flex;align-items:center;gap:6px;padding:4px 12px;
    border-radius:9999px;background:rgba(239,68,68,0.15);color:#f87171;
    border:1px solid rgba(239,68,68,0.3);font-size:0.82rem;font-weight:600;
}
.pulse-dot { width:8px;height:8px;border-radius:50%;background-color:currentColor;display:inline-block; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class MicroService(BaseModel):
    title: str = Field(description="Action-oriented title of the micro-service")
    tagline: str = Field(description="One-line pitch focused on client ROI")
    target_client: str = Field(description="Specific ideal client persona who has money to spend")
    deliverables: List[str] = Field(description="3 to 4 concrete bullet deliverables")
    turnaround: str = Field(description="Estimated turnaround, e.g., '48 Hours' or '3-5 Days'")

class PricingTier(BaseModel):
    tier_name: str = Field(description="Starter, Standard, or Retainer tier name")
    price: str = Field(description="Suggested price or price range in selected currency")
    scope: str = Field(description="Clear scope definition for this tier")
    ideal_for: str = Field(description="Who should buy this tier")

class OutreachScript(BaseModel):
    channel: str = Field(description="e.g. Cold Email or LinkedIn Direct Message")
    subject_line: str = Field(description="High-open rate subject line")
    body: str = Field(description="Concise, non-salesy outreach pitch focusing on value")
    follow_up: str = Field(description="Polite 3-day follow-up message")

class FreelanceProposal(BaseModel):
    headline: str = Field(description="Winning proposal opening headline")
    problem_statement: str = Field(description="Empathy-driven summary of the client's current pain point")
    proposed_solution: str = Field(description="Step-by-step roadmap showing how you deliver results")
    why_me: str = Field(description="Highlight of unique blend of technical and soft skills")
    call_to_action: str = Field(description="Low-friction next step to schedule a quick chat")

class FirstGigOutput(BaseModel):
    summary: str = Field(description="Strategic summary of this freelance niche")
    services: List[MicroService] = Field(description="Exactly 3 micro-services")
    pricing: List[PricingTier] = Field(description="Exactly 3 pricing tiers")
    outreach: OutreachScript = Field(description="Cold outreach templates")
    proposal: FreelanceProposal = Field(description="Ready-to-use client proposal")


# ---------------------------------------------------------
# Ollama Connectivity
# ---------------------------------------------------------
def check_ollama_status(host: str):
    try:
        resp = requests.get(f"{host.rstrip('/')}/api/tags", timeout=1.5)
        if resp.status_code == 200:
            models = [m.get("name") for m in resp.json().get("models", [])]
            return True, models, None
        return False, [], f"HTTP {resp.status_code}"
    except Exception as e:
        return False, [], str(e)


# ---------------------------------------------------------
# Fallback Data Generator
# ---------------------------------------------------------
def generate_fallback_data(tech_skills: str, soft_skills: str, niche: str, currency: str) -> FirstGigOutput:
    sym = "$" if "$" in currency else ("€" if "EUR" in currency else ("₹" if "INR" in currency else "£"))
    primary = tech_skills.split(",")[0].strip()
    return FirstGigOutput(
        summary=f"Specialized freelance positioning combining '{tech_skills}' with '{soft_skills}' targeting the '{niche}' market.",
        services=[
            MicroService(
                title=f"{primary} Rapid Implementation & Audit",
                tagline="Plug immediate operational leaks with a streamlined 48-hour technical sprint.",
                target_client=f"Busy founders & operators in {niche} lacking in-house technical bandwidth.",
                deliverables=[
                    "Comprehensive codebase / workflow health audit report",
                    "Implementation of top 3 high-impact fixes or automation scripts",
                    "Recorded Loom video walkthrough explaining every change in plain English",
                    "7 days of post-handoff support & direct Slack/WhatsApp access"
                ],
                turnaround="48 - 72 Hours"
            ),
            MicroService(
                title=f"Custom {niche} Workflow Automation & Tooling",
                tagline="Save 10+ hours per week by connecting fragmented tools into an automated pipeline.",
                target_client=f"Growing businesses in {niche} overwhelmed by repetitive manual tasks.",
                deliverables=[
                    "Custom integration script / micro-dashboard tailored to business needs",
                    "Error logging and automatic alert notifications",
                    "Standard Operating Procedure (SOP) documentation for team onboarding",
                    "1-on-1 handover coaching call"
                ],
                turnaround="4 - 5 Days"
            ),
            MicroService(
                title="Performance Optimization & Reliability Retainer",
                tagline="Continuous peace of mind and priority troubleshooting for mission-critical systems.",
                target_client=f"Established teams in {niche} seeking a dependable fractional technical partner.",
                deliverables=[
                    "Bi-weekly performance checks and preventive maintenance",
                    "Guaranteed 4-hour emergency response SLA",
                    "Continuous feature enhancements (up to 10 hours/month)",
                    "Monthly ROI & optimization strategy report"
                ],
                turnaround="Monthly Ongoing"
            )
        ],
        pricing=[
            PricingTier(
                tier_name="Starter Sprint",
                price=f"{sym}150 - {sym}300",
                scope="Low friction foot-in-the-door technical audit and quick-win deliverable.",
                ideal_for="First-time clients who want to verify work quality with zero risk."
            ),
            PricingTier(
                tier_name="Full Implementation (Recommended)",
                price=f"{sym}500 - {sym}950",
                scope="End-to-end delivery of custom micro-service, documentation, and live walkthrough.",
                ideal_for="Clients with an active budget who need an immediate, turnkey solution."
            ),
            PricingTier(
                tier_name="Growth Retainer",
                price=f"{sym}450 - {sym}1,200/mo",
                scope="Ongoing fractional support, priority updates, and automated maintenance.",
                ideal_for="Long-term clients seeking predictable monthly support."
            )
        ],
        outreach=OutreachScript(
            channel="Email / LinkedIn DM",
            subject_line=f"Quick idea regarding {niche} automation (not a sales pitch)",
            body=(
                f"Hi {{FirstName}},\n\n"
                f"I noticed how {{CompanyName}} is scaling within the {niche} space—congrats on the recent momentum!\n\n"
                f"I put together a quick observation on how you can leverage {primary} "
                f"to eliminate repetitive bottleneck tasks and improve speed.\n\n"
                f"Mind if I send over a 2-minute video walkthrough? No pressure at all.\n\n"
                f"Best regards,\n{{YourName}}\nFreelance Specialist"
            ),
            follow_up=(
                f"Hi {{FirstName}},\n\nQuick bump on this — completely understand if timing is off.\n\n"
                f"Here is a 1-page summary for your team: [Link]\n\nBest,\n{{YourName}}"
            )
        ),
        proposal=FreelanceProposal(
            headline=f"Turnkey {primary} Solution Tailored for {{ClientName}}",
            problem_statement=(
                f"{{ClientName}} needs a dependable solution to automate and modernize processes in {niche} "
                f"without ballooning overhead or hiring full-time engineering staff."
            ),
            proposed_solution=(
                "Phase 1: Discovery & Requirements Lock (Day 1)\n"
                "Phase 2: Core Development & Modular Testing (Days 2-3)\n"
                "Phase 3: Integration, Client Review & Revisions (Day 4)\n"
                "Phase 4: Handoff, Video Walkthrough & 7-Day Guarantee (Day 5)"
            ),
            why_me=(
                f"I combine technical precision in {tech_skills} with strong {soft_skills}. "
                f"I ensure clear communication, on-time delivery, and complete visibility at every milestone."
            ),
            call_to_action=(
                "Are you available for a 15-minute alignment call tomorrow or Thursday to finalize scope? "
                "Looking forward to helping you launch this smoothly!"
            )
        )
    )


# ---------------------------------------------------------
# Ollama Query
# ---------------------------------------------------------
def query_ollama_for_firstgig(
    host: str, model: str, tech_skills: str, soft_skills: str,
    niche: str, exp_level: str, currency: str, temperature: float = 0.5
) -> FirstGigOutput:
    prompt = f"""You are FirstGig AI, an elite freelance career strategist.
Turn the user's skills into 3 realistic micro-services, starter pricing, an outreach script, and a client proposal.

USER PROFILE:
- Technical Skills: {tech_skills}
- Soft Skills: {soft_skills}
- Target Niche: {niche}
- Experience Level: {exp_level}
- Pricing Currency: {currency}

Respond with VALID JSON ONLY:
{{
  "summary": "2-sentence positioning strategy",
  "services": [
    {{"title":"...","tagline":"...","target_client":"...","deliverables":["...","...","..."],"turnaround":"..."}}
  ],
  "pricing": [
    {{"tier_name":"...","price":"...","scope":"...","ideal_for":"..."}}
  ],
  "outreach": {{"channel":"...","subject_line":"...","body":"...","follow_up":"..."}},
  "proposal": {{"headline":"...","problem_statement":"...","proposed_solution":"...","why_me":"...","call_to_action":"..."}}
}}

Rules: exactly 3 services, exactly 3 pricing tiers. Keep descriptions concise (1-2 sentences). No markdown, no extra text. Return only raw JSON."""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return strictly valid JSON only, no markdown, no commentary."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature, "num_predict": 1200, "num_ctx": 2048}
    }
    resp = requests.post(
        f"{host.rstrip('/')}/api/chat",
        headers={"Content-Type": "application/json"},
        json=payload, timeout=180
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")

    content = resp.json().get("message", {}).get("content", "").strip()
    for marker in ["```json", "```"]:
        if content.startswith(marker):
            content = content[len(marker):]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        fixed = content
        if '"' in fixed and fixed.count('"') % 2 != 0:
            fixed += '"'
        fixed += "}" * max(0, fixed.count("{") - fixed.count("}"))
        parsed = json.loads(fixed)

    return FirstGigOutput(**parsed)


# ---------------------------------------------------------
# Rate Calculator Helper
# ---------------------------------------------------------
RATE_TABLE = {
    "Beginner (Landing 1st gig)": {
        "USD ($)": {"hourly": (15, 35), "project": (150, 500), "monthly": (400, 1200)},
        "EUR (€)": {"hourly": (14, 32), "project": (140, 460), "monthly": (370, 1100)},
        "INR (₹)": {"hourly": (800, 2000), "project": (8000, 35000), "monthly": (25000, 80000)},
        "GBP (£)": {"hourly": (12, 28), "project": (120, 420), "monthly": (340, 1000)},
    },
    "Intermediate (Some projects)": {
        "USD ($)": {"hourly": (35, 75), "project": (500, 2000), "monthly": (1200, 4000)},
        "EUR (€)": {"hourly": (32, 68), "project": (460, 1800), "monthly": (1100, 3700)},
        "INR (₹)": {"hourly": (2000, 5000), "project": (35000, 120000), "monthly": (80000, 250000)},
        "GBP (£)": {"hourly": (28, 60), "project": (420, 1600), "monthly": (1000, 3200)},
    },
    "Seasoned Pro (Upscaling rates)": {
        "USD ($)": {"hourly": (75, 200), "project": (2000, 10000), "monthly": (4000, 15000)},
        "EUR (€)": {"hourly": (68, 180), "project": (1800, 9000), "monthly": (3700, 14000)},
        "INR (₹)": {"hourly": (5000, 15000), "project": (120000, 600000), "monthly": (250000, 900000)},
        "GBP (£)": {"hourly": (60, 160), "project": (1600, 8000), "monthly": (3200, 12000)},
    },
}

PLATFORM_FEE = {
    "Upwork": 0.10,
    "Fiverr": 0.20,
    "Toptal": 0.00,
    "LinkedIn / Direct": 0.00,
}

def calculate_rates(exp_level: str, currency: str, platform: str) -> dict:
    base = RATE_TABLE.get(exp_level, RATE_TABLE["Beginner (Landing 1st gig)"])
    rates = base.get(currency, base["USD ($)"])
    fee = PLATFORM_FEE.get(platform, 0)
    sym = currency.split("(")[-1].replace(")", "").strip()
    result = {}
    for rate_type, (lo, hi) in rates.items():
        net_lo = round(lo * (1 - fee))
        net_hi = round(hi * (1 - fee))
        result[rate_type] = {
            "gross": f"{sym}{lo:,} – {sym}{hi:,}",
            "net": f"{sym}{net_lo:,} – {sym}{net_hi:,}",
            "platform_cut": f"{int(fee * 100)}%"
        }
    return result


# ---------------------------------------------------------
# Platform Post Formatter
# ---------------------------------------------------------
def format_platform_post(data: FirstGigOutput, platform: str, tech_skills: str, niche: str) -> str:
    primary = tech_skills.split(",")[0].strip()
    service1 = data.services[0].title if data.services else f"{primary} services"
    price1 = data.pricing[0].price if data.pricing else "competitive rates"

    if platform == "Upwork Bid":
        return f"""**Hi {{ClientFirstName}},**

I came across your job post and immediately saw the overlap with the work I specialize in.

**What I bring:**
{data.proposal.why_me}

**My approach for your project:**
{data.proposal.proposed_solution}

**Starting from:** {price1}

I'd love to jump on a quick 15-minute call to understand your specific requirements and confirm fit before we begin.

**Next step:** Feel free to message me here on Upwork or click "Invite to Job" — I typically respond within 2 hours.

Looking forward to hearing from you!
— {{YourName}}"""

    elif platform == "LinkedIn Post":
        return f"""🚀 Open for freelance projects in {niche}!

I help {niche.lower()} businesses {data.services[0].tagline.lower() if data.services else 'scale faster'}.

✅ {data.services[0].title if data.services else service1}
✅ {data.services[1].title if len(data.services) > 1 else "Custom Workflow Automation"}
✅ {data.services[2].title if len(data.services) > 2 else "Ongoing Retainer Support"}

💡 {data.summary}

📦 Engagements start at {price1}
⏱️ Typical turnaround: {data.services[0].turnaround if data.services else "48-72 Hours"}

If you know a team that could use this, drop a comment or DM me directly.

#Freelance #OpenToWork #{primary.replace(' ', '')} #{niche.replace(' ', '').replace('&', '').replace('/', '')}"""

    elif platform == "Fiverr Gig Description":
        deliverables = ""
        if data.services:
            deliverables = "\n".join([f"✅ {d}" for d in data.services[0].deliverables])
        return f"""🔥 **{data.services[0].title if data.services else service1}**

{data.services[0].tagline if data.services else "Professional delivery every time."}

---

**What you'll get:**
{deliverables}

**Why buyers choose me:**
{data.proposal.why_me}

**Turnaround:** {data.services[0].turnaround if data.services else "48-72 Hours"}

---

📌 **Message me before ordering** so I can confirm this gig is the right fit for your project.

I respond within 1 hour during business hours."""

    elif platform == "Cold Email":
        return f"""Subject: {data.outreach.subject_line}

{data.outreach.body}

---

P.S. If you'd like to see examples of past work, I'm happy to share a quick portfolio — just reply to this email."""

    return ""


# ---------------------------------------------------------
# Markdown Exporter
# ---------------------------------------------------------
def convert_to_markdown(data: FirstGigOutput, tech_skills: str, soft_skills: str, niche: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# FirstGig AI — Freelance Launch Blueprint
*Generated on {now}*

---

## 🎯 Positioning Profile
- **Technical Skills:** {tech_skills}
- **Soft Skills:** {soft_skills}
- **Target Market / Niche:** {niche}

### Strategic Summary
{data.summary}

---

## 🛠️ Micro-Services
"""
    for i, s in enumerate(data.services, 1):
        md += f"""
### Service {i}: {s.title}
- **Tagline:** *{s.tagline}*
- **Ideal Client:** {s.target_client}
- **Estimated Turnaround:** `{s.turnaround}`
- **Deliverables:**
"""
        for d in s.deliverables:
            md += f"  - {d}\n"

    md += "\n---\n\n## 💰 Starter Pricing Strategy\n\n"
    for p in data.pricing:
        md += f"### {p.tier_name} — `{p.price}`\n"
        md += f"- **Scope:** {p.scope}\n"
        md += f"- **Target Buyer:** {p.ideal_for}\n\n"

    md += f"""---

## 📨 Cold Outreach Playbook
- **Channel:** {data.outreach.channel}
- **Subject Line:** `{data.outreach.subject_line}`

### Initial Message:
```
{data.outreach.body}
```

### 3-Day Follow-Up:
```
{data.outreach.follow_up}
```

---

## 📝 Client Proposal Template
### Headline: {data.proposal.headline}

#### 1. Understanding the Problem
{data.proposal.problem_statement}

#### 2. Proposed Scope of Work
{data.proposal.proposed_solution}

#### 3. Why Me?
{data.proposal.why_me}

#### 4. Next Steps
{data.proposal.call_to_action}

---
*Generated with FirstGig AI (Hacktoberfest Week 2: Side Hustle)*
"""
    return md


# ---------------------------------------------------------
# PDF Exporter
# ---------------------------------------------------------
def _safe(text: str) -> str:
    """Strip non-latin1 characters for fpdf basic font."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(data: FirstGigOutput, tech_skills: str, soft_skills: str, niche: str) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=18, top=18, right=18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    PAGE_W = 174  # A4 210mm minus 18mm left + 18mm right margins

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(PAGE_W, 10, _safe("FirstGig AI  —  Freelance Blueprint"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(PAGE_W, 5, _safe(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}   |   Niche: {niche}"), ln=True, align="C")
    pdf.ln(4)

    def section_title(title: str):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(56, 189, 248)
        pdf.cell(PAGE_W, 7, _safe(title), ln=True)
        pdf.set_draw_color(56, 189, 248)
        pdf.line(18, pdf.get_y(), 192, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(30, 41, 59)

    def body_text(text: str):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 60, 80)
        pdf.multi_cell(PAGE_W, 5, _safe(text))
        pdf.ln(1)

    def label_value(label: str, value: str):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(35, 5, _safe(label + ":"))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(PAGE_W - 35, 5, _safe(value))

    # Profile
    section_title("Positioning Profile")
    label_value("Tech Skills", tech_skills)
    label_value("Soft Skills", soft_skills)
    label_value("Niche", niche)
    pdf.ln(2)
    body_text(data.summary)

    # Services
    section_title("3 High-Impact Micro-Services")
    for i, s in enumerate(data.services, 1):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(PAGE_W, 6, _safe(f"Service {i}: {s.title}"), ln=True)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(56, 189, 248)
        pdf.multi_cell(PAGE_W, 4, _safe(f'"{s.tagline}"'))
        label_value("Ideal Client", s.target_client)
        label_value("Turnaround", s.turnaround)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(PAGE_W, 4, "Deliverables:", ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(30, 41, 59)
        for d in s.deliverables:
            pdf.set_x(pdf.l_margin + 4)
            pdf.multi_cell(PAGE_W - 4, 4, _safe(f"* {d}"))
        pdf.ln(3)

    # Pricing
    section_title("3-Tier Pricing Strategy")
    for p in data.pricing:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(PAGE_W, 6, _safe(f"{p.tier_name}  —  {p.price}"), ln=True)
        label_value("Scope", p.scope)
        label_value("Ideal For", p.ideal_for)
        pdf.ln(2)

    # Outreach
    section_title("Cold Outreach Playbook")
    label_value("Channel", data.outreach.channel)
    label_value("Subject", data.outreach.subject_line)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(PAGE_W, 4, "Initial Message:", ln=True)
    body_text(data.outreach.body)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(PAGE_W, 4, "3-Day Follow-Up:", ln=True)
    body_text(data.outreach.follow_up)

    # Proposal
    section_title("Freelance Proposal Template")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(PAGE_W, 6, _safe(data.proposal.headline))
    pdf.ln(1)
    label_value("Problem", data.proposal.problem_statement)
    label_value("Solution", data.proposal.proposed_solution)
    label_value("Why Me", data.proposal.why_me)
    label_value("CTA", data.proposal.call_to_action)

    # Footer
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(PAGE_W, 4, "Generated with FirstGig AI  |  Hacktoberfest Week 2: Side Hustle", ln=True, align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ AI Engine Configuration")
    default_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    ollama_host = st.text_input("Ollama Endpoint", value=default_host,
                                help="Local or remote Ollama server URL.")
    is_online, models_list, _ = check_ollama_status(ollama_host)

    if is_online:
        st.markdown('<div class="status-pill-online"><span class="pulse-dot"></span> Ollama Connected</div>', unsafe_allow_html=True)
        sel_idx = models_list.index("gemma2:2b") if "gemma2:2b" in models_list else 0
        selected_model = st.selectbox("Selected Model", options=models_list or ["gemma2:2b"], index=sel_idx)
    else:
        st.markdown('<div class="status-pill-offline"><span class="pulse-dot"></span> Ollama Offline</div>', unsafe_allow_html=True)
        selected_model = st.text_input("Model Name", value="gemma2:2b")
        st.caption("ℹ️ Run `ollama run gemma2:2b` in your WSL terminal.\n*(Demo Mode auto-activates if offline)*")

    use_demo_mode = st.checkbox("Simulate / Demo Mode (No Ollama needed)", value=not is_online,
                                help="Instant high-quality outputs without local inference.")

    st.markdown("---")
    st.markdown("### 🎛️ Generation Tuning")
    temperature = st.slider("Creativity / Temperature", 0.1, 1.0, 0.5, 0.05)

    st.markdown("---")
    st.markdown("### 💡 Quick Skill Presets")
    preset = st.selectbox("Load Preset Profile", options=[
        "Custom",
        "Python Automation & Web Scraping",
        "React / Next.js Web Development",
        "Data Analysis & Streamlit Dashboards",
        "AI Integration & Prompt Engineering",
        "UI/UX Design & Frontend Polish"
    ])


# ---------------------------------------------------------
# Preset Population
# ---------------------------------------------------------
PRESETS = {
    "Python Automation & Web Scraping": {
        "tech": "Python, BeautifulSoup, Selenium, Pandas, REST APIs, Cron jobs",
        "soft": "Problem decomposition, proactive client updates, clear documentation",
        "niche": "E-commerce & Lead Generation Agencies"
    },
    "React / Next.js Web Development": {
        "tech": "React, Next.js, Tailwind CSS, TypeScript, Supabase, Vercel",
        "soft": "Visual empathy, speed of execution, responsive communication",
        "niche": "B2B SaaS Founders & Tech Startups"
    },
    "Data Analysis & Streamlit Dashboards": {
        "tech": "Python, Streamlit, SQL, Plotly, Excel/CSV wrangling",
        "soft": "Data storytelling, business acumen, active listening",
        "niche": "Local Clinics, Real Estate Brokers, Fitness Franchises"
    },
    "AI Integration & Prompt Engineering": {
        "tech": "OpenAI / Ollama APIs, LangChain, RAG pipelines, Vector DBs, Python",
        "soft": "Managing client expectations, ethical AI usage, plain-language translation",
        "niche": "Content Creators & Boutique Marketing Agencies"
    },
    "UI/UX Design & Frontend Polish": {
        "tech": "Figma, HTML/CSS, Webflow, Design Systems, Mobile responsiveness",
        "soft": "Client empathy, constructive critique handling, user research",
        "niche": "Indie Hackers & Early Stage Bootstrapped Startups"
    }
}

default_tech  = "Python, Web Scraping, API Integration, Task Automation"
default_soft  = "Clear communication, timely delivery, client empathy"
default_niche = "B2B E-Commerce & Retail Brands"

if preset in PRESETS:
    default_tech  = PRESETS[preset]["tech"]
    default_soft  = PRESETS[preset]["soft"]
    default_niche = PRESETS[preset]["niche"]


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown(
    """<div class="hero-container">
        <div class="hero-title">⚡ FirstGig AI</div>
        <p class="hero-subtitle">
            Transform your technical and soft skills into 3 profitable micro-services, starter pricing,
            battle-tested cold outreach, and client-winning freelance proposals — powered by Gemma 2 2B running locally.
        </p>
    </div>""",
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# INPUT FORM
# ---------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    tech_skills = st.text_area("🛠️ Technical Skills & Tools", value=default_tech, height=100,
                               help="Languages, frameworks, tools you know.")
    niche = st.text_input("🎯 Target Industry / Niche", value=default_niche,
                          help="e.g. E-commerce Brands, Local Dentists, B2B SaaS")
with col2:
    soft_skills = st.text_area("🤝 Soft Skills & Strengths", value=default_soft, height=100,
                               help="Communication, speed, reliability, domain expertise.")
    c1, c2 = st.columns(2)
    with c1:
        exp_level = st.selectbox("📈 Experience Level",
                                 ["Beginner (Landing 1st gig)", "Intermediate (Some projects)", "Seasoned Pro (Upscaling rates)"])
    with c2:
        currency = st.selectbox("💵 Pricing Currency", ["USD ($)", "EUR (€)", "INR (₹)", "GBP (£)"])

generate_btn = st.button("🚀 Generate FirstGig Blueprint", type="primary", use_container_width=True)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
for key in ["blueprint_data", "blueprint_markdown"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------------------------------------------------
# GENERATION
# ---------------------------------------------------------
if generate_btn:
    if not tech_skills.strip() or not niche.strip():
        st.error("Please fill in your technical skills and target niche before generating.")
    else:
        with st.spinner("🧠 Gemma 2 2B is generating your blueprint (CPU inference ~30-60s)..."):
            t0 = time.time()
            try:
                if use_demo_mode or not is_online:
                    time.sleep(0.8)
                    result_data = generate_fallback_data(tech_skills, soft_skills, niche, currency)
                    if not is_online:
                        st.info("ℹ️ Generated via Instant Fallback Engine (Ollama offline).")
                else:
                    result_data = query_ollama_for_firstgig(
                        ollama_host, selected_model, tech_skills, soft_skills,
                        niche, exp_level, currency, temperature
                    )
                st.session_state.blueprint_data = result_data
                st.session_state.blueprint_markdown = convert_to_markdown(result_data, tech_skills, soft_skills, niche)
                st.success(f"✨ Blueprint generated in {round(time.time()-t0, 2)}s!")
            except Exception as ex:
                st.warning(f"Ollama error: {ex}. Falling back to structured generator.")
                result_data = generate_fallback_data(tech_skills, soft_skills, niche, currency)
                st.session_state.blueprint_data = result_data
                st.session_state.blueprint_markdown = convert_to_markdown(result_data, tech_skills, soft_skills, niche)

# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------
data: Optional[FirstGigOutput] = st.session_state.blueprint_data

if data:
    st.markdown("---")
    st.info(f"💡 **Strategic Positioning:** {data.summary}")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🛠️ 3 Micro-Services",
        "💰 Pricing Strategy",
        "📊 Rate Calculator",
        "📨 Cold Outreach",
        "📝 Proposal",
        "🔗 Platform Posts",
        "📄 Export"
    ])

    # ── Tab 1: Micro-Services ──
    with tab1:
        st.markdown("### 📦 3 High-Impact Micro-Services")
        st.caption("Package your skills into specific, scoped offers rather than generic hourly labor.")
        cols = st.columns(3)
        for idx, service in enumerate(data.services):
            deliverables_html = "".join([f"<li style='margin-bottom:4px'>{d}</li>" for d in service.deliverables])
            card_html = (
                f'<div class="service-card">'
                f'<span class="card-badge">Service {idx + 1}</span>'
                f'<h4 style="margin:8px 0;color:#f1f5f9">{service.title}</h4>'
                f'<p style="color:#38bdf8;font-size:0.9rem;font-style:italic;margin-bottom:10px">"{service.tagline}"</p>'
                f'<p style="font-size:0.85rem;color:#cbd5e1"><b>Ideal Client:</b> {service.target_client}</p>'
                f'<p style="font-size:0.85rem;color:#cbd5e1;margin-bottom:4px"><b>Deliverables:</b></p>'
                f'<ul style="font-size:0.82rem;color:#94a3b8;padding-left:18px;margin-bottom:12px">{deliverables_html}</ul>'
                f'<div style="font-size:0.8rem;background:rgba(15,23,42,0.7);padding:8px 12px;border-radius:6px;border:1px solid rgba(255,255,255,0.08);color:#f1f5f9">'
                f'⏱️ <b>Turnaround:</b> <span style="color:#34d399;font-weight:600">{service.turnaround}</span>'
                f'</div></div>'
            )
            with cols[idx]:
                st.markdown(card_html, unsafe_allow_html=True)

    # ── Tab 2: Pricing Strategy ──
    with tab2:
        st.markdown("### 💰 Recommended 3-Tier Pricing Model")
        st.caption("Use a tiered ladder to give clients choice and anchor value perception.")
        pcols = st.columns(3)
        tier_styles = [
            ("rgba(15,23,42,0.9)", "1px solid rgba(99,102,241,0.2)", ""),
            ("linear-gradient(180deg,rgba(30,27,75,0.6)0%,rgba(15,23,42,0.95)100%)", "2px solid #818cf8", "box-shadow:0 8px 24px rgba(99,102,241,0.25);"),
            ("rgba(15,23,42,0.9)", "1px solid rgba(99,102,241,0.2)", ""),
        ]
        for i, (tier, (bg, border, extra)) in enumerate(zip(data.pricing, tier_styles)):
            badge = '<span class="card-badge" style="background:rgba(129,140,248,0.25);color:#a5b4fc">⭐ Most Popular</span><br>' if i == 1 else ''
            html = (
                f'<div style="background:{bg};border:{border};border-radius:14px;padding:22px;text-align:center;{extra}">'
                f'{badge}'
                f'<h3 style="color:#f8fafc;margin:8px 0 4px">{tier.tier_name}</h3>'
                f'<div style="font-size:1.8rem;font-weight:800;color:#38bdf8;margin:10px 0">{tier.price}</div>'
                f'<p style="color:#cbd5e1;font-size:0.9rem;margin-bottom:14px">{tier.scope}</p>'
                f'<hr style="border:0;border-top:1px solid rgba(255,255,255,0.1);margin:10px 0">'
                f'<p style="font-size:0.82rem;color:#94a3b8"><b>Target Buyer:</b><br>{tier.ideal_for}</p>'
                f'</div>'
            )
            with pcols[i]:
                st.markdown(html, unsafe_allow_html=True)

    # ── Tab 3: Rate Calculator ──
    with tab3:
        st.markdown("### 📊 Platform-Specific Rate Calculator")
        st.caption("See your realistic market rates per platform after fees are deducted.")
        rc1, rc2 = st.columns(2)
        with rc1:
            calc_platform = st.selectbox("Choose Platform", list(PLATFORM_FEE.keys()), key="calc_plat")
        with rc2:
            calc_exp = st.selectbox("Experience Level", list(RATE_TABLE.keys()), key="calc_exp",
                                    index=list(RATE_TABLE.keys()).index(exp_level) if exp_level in RATE_TABLE else 0)

        rates = calculate_rates(calc_exp, currency, calc_platform)
        fee_pct = int(PLATFORM_FEE[calc_platform] * 100)

        if fee_pct > 0:
            st.warning(f"⚠️ **{calc_platform}** charges a **{fee_pct}% service fee**. Net rates shown below reflect your actual take-home.")
        else:
            st.success(f"✅ **{calc_platform}** charges **no platform fee** — you keep 100% of your earnings.")

        r1, r2, r3 = st.columns(3)
        labels = {"hourly": ("⏱️ Hourly Rate", "Per hour billed"), "project": ("📦 Project Rate", "Fixed-scope deliverable"), "monthly": ("📅 Monthly Retainer", "Ongoing engagement")}
        for col, (rate_key, (title, subtitle)) in zip([r1, r2, r3], labels.items()):
            if rate_key in rates:
                r = rates[rate_key]
                with col:
                    st.markdown(
                        f'<div class="rate-card">'
                        f'<div class="rate-label">{title}</div>'
                        f'<div class="rate-value">{r["net"]}</div>'
                        f'<div style="font-size:0.75rem;color:#64748b">Gross: {r["gross"]}<br>Platform cut: {r["platform_cut"]}</div>'
                        f'<div style="font-size:0.72rem;color:#475569;margin-top:6px">{subtitle}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

        st.markdown("---")
        st.markdown("#### 💡 Pricing Strategy Tip")
        tips = {
            "Upwork": "Start with a slightly lower rate to earn your first 5 reviews, then raise by 20-30% after reaching Job Success Score 90%+.",
            "Fiverr": "Use 3 Gig packages. The middle package should be the obvious best value. Upsell extras like rush delivery (+50% of base).",
            "Toptal": "Toptal clients expect senior-level rates. Never discount — position as a premium specialist.",
            "LinkedIn / Direct": "No platform fees means you can offer 10% off compared to platform rates and still earn more.",
        }
        st.info(tips.get(calc_platform, "Price based on value delivered, not hours worked."))

    # ── Tab 4: Cold Outreach ──
    with tab4:
        st.markdown("### 📨 Cold Outreach Playbook")
        st.caption("Personalized, low-pressure outreach scripts ready to copy and send.")
        st.markdown(f"**Channel:** `{data.outreach.channel}`")
        st.markdown(f"**Subject Line:** `{data.outreach.subject_line}`")
        st.markdown("#### Initial Pitch Message:")
        st.code(data.outreach.body, language="text")
        st.markdown("#### 3-Day Polite Follow-Up:")
        st.code(data.outreach.follow_up, language="text")

    # ── Tab 5: Proposal ──
    with tab5:
        st.markdown("### 📝 Ready-to-Send Freelance Proposal")
        st.caption("Copy into Upwork, Fiverr, or paste into client email discussions.")
        st.subheader(data.proposal.headline)
        with st.expander("1. Understanding Your Problem (Empathy)", expanded=True):
            st.write(data.proposal.problem_statement)
        with st.expander("2. Proposed Solution & Milestone Roadmap", expanded=True):
            st.write(data.proposal.proposed_solution)
        with st.expander("3. Why Choose Me?", expanded=True):
            st.write(data.proposal.why_me)
        with st.expander("4. Low-Friction Next Steps (CTA)", expanded=True):
            st.write(data.proposal.call_to_action)

    # ── Tab 6: Platform Posts ──
    with tab6:
        st.markdown("### 🔗 Platform-Specific Post Formatter")
        st.caption("One-click conversion of your blueprint into ready-to-paste posts for each platform.")

        platform_choice = st.radio(
            "Choose output format:",
            ["Upwork Bid", "LinkedIn Post", "Fiverr Gig Description", "Cold Email"],
            horizontal=True
        )

        post_content = format_platform_post(data, platform_choice, tech_skills, niche)

        badge_map = {
            "Upwork Bid": "badge-upwork",
            "LinkedIn Post": "badge-linkedin",
            "Fiverr Gig Description": "badge-fiverr",
            "Cold Email": "badge-email",
        }
        st.markdown(
            f'<span class="platform-badge {badge_map.get(platform_choice, "")}">{platform_choice}</span>',
            unsafe_allow_html=True
        )
        st.text_area("📋 Copy this content:", value=post_content, height=380, key="platform_post_output")
        st.download_button(
            f"⬇️ Download {platform_choice} (.txt)",
            data=post_content,
            file_name=f"FirstGig_{platform_choice.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # ── Tab 7: Export ──
    with tab7:
        st.markdown("### 📄 Export Your Blueprint")
        st.caption("Download in Markdown or a formatted PDF report.")

        e1, e2, e3 = st.columns(3)

        with e1:
            st.download_button(
                "📥 Download Markdown (.md)",
                data=st.session_state.blueprint_markdown,
                file_name=f"FirstGig_Blueprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with e2:
            pdf_bytes = generate_pdf(data, tech_skills, soft_skills, niche)
            st.download_button(
                "📑 Download PDF Report",
                data=pdf_bytes,
                file_name=f"FirstGig_Blueprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with e3:
            if st.button("💾 Save .md to Project Folder", use_container_width=True):
                save_path = os.path.join(os.getcwd(), "FirstGig_Blueprint.md")
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(st.session_state.blueprint_markdown)
                st.success(f"Saved to `{save_path}`!")

        st.markdown("#### Preview:")
        st.text_area("Raw Markdown Content", value=st.session_state.blueprint_markdown, height=300)
