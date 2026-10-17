import html
import io
import json
import logging
import os
import time
from datetime import datetime
from typing import List, Optional

import requests
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
logger = logging.getLogger("FirstGigAI")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ---------------------------------------------------------
# Security & Helper Utilities
# ---------------------------------------------------------
def safe_html(val: Optional[str]) -> str:
    """Escapes HTML entities from untrusted dynamic text before rendering."""
    if val is None:
        return ""
    return html.escape(str(val))


def sanitize_input(text: Optional[str], max_len: int = 500) -> str:
    """Sanitizes user input by stripping whitespace and truncating to max_len."""
    if not text:
        return ""
    cleaned = text.strip()
    return cleaned[:max_len]


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
# Custom Modern CSS (Static & Safe)
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
# Pydantic Schemas with Strict Validation
# ---------------------------------------------------------
class MicroService(BaseModel):
    title: str = Field(min_length=3, max_length=150, description="Action-oriented title of the micro-service")
    tagline: str = Field(min_length=5, max_length=250, description="One-line pitch focused on client ROI")
    target_client: str = Field(min_length=5, max_length=250, description="Specific ideal client persona who has money to spend")
    deliverables: List[str] = Field(min_length=2, description="Concrete bullet deliverables")
    turnaround: str = Field(min_length=2, max_length=80, description="Estimated turnaround time")

    @field_validator("title", "tagline", "target_client", "turnaround")
    @classmethod
    def strip_and_validate_nonempty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or pure whitespace")
        return s

    @field_validator("deliverables")
    @classmethod
    def validate_deliverables(cls, v: List[str]) -> List[str]:
        cleaned = [d.strip() for d in v if d and d.strip()]
        if len(cleaned) < 2:
            raise ValueError("Must provide at least 2 non-empty deliverables")
        return cleaned


class PricingTier(BaseModel):
    tier_name: str = Field(min_length=2, max_length=80, description="Tier name")
    price: str = Field(min_length=1, max_length=60, description="Suggested price or price range")
    scope: str = Field(min_length=5, max_length=300, description="Clear scope definition for this tier")
    ideal_for: str = Field(min_length=5, max_length=250, description="Who should buy this tier")

    @field_validator("tier_name", "price", "scope", "ideal_for")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Pricing fields cannot be empty")
        return s


class OutreachScript(BaseModel):
    channel: str = Field(min_length=2, max_length=80, description="Outreach channel")
    subject_line: str = Field(min_length=3, max_length=150, description="Subject line")
    body: str = Field(min_length=10, max_length=2000, description="Concise value-focused outreach message")
    follow_up: str = Field(min_length=10, max_length=1000, description="Polite 3-day follow-up message")

    @field_validator("channel", "subject_line", "body", "follow_up")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Outreach fields cannot be empty")
        return s


class FreelanceProposal(BaseModel):
    headline: str = Field(min_length=5, max_length=150, description="Proposal headline")
    problem_statement: str = Field(min_length=10, max_length=1500, description="Summary of client's pain point")
    proposed_solution: str = Field(min_length=10, max_length=2500, description="Step-by-step roadmap")
    why_me: str = Field(min_length=10, max_length=1500, description="Unique skills and reliability highlight")
    call_to_action: str = Field(min_length=5, max_length=500, description="Low-friction next step")

    @field_validator("headline", "problem_statement", "proposed_solution", "why_me", "call_to_action")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Proposal fields cannot be empty")
        return s


class FirstGigOutput(BaseModel):
    summary: str = Field(min_length=10, max_length=1000, description="Strategic positioning summary")
    services: List[MicroService] = Field(min_length=3, max_length=3, description="Exactly 3 micro-services")
    pricing: List[PricingTier] = Field(min_length=3, max_length=3, description="Exactly 3 pricing tiers")
    outreach: OutreachScript = Field(description="Cold outreach templates")
    proposal: FreelanceProposal = Field(description="Ready-to-use client proposal")
    is_fallback: bool = Field(default=False, description="Flag indicating deterministic demo/fallback generation")
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Summary cannot be empty")
        return s


# ---------------------------------------------------------
# Ollama Connectivity & Configuration
# ---------------------------------------------------------
DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2:2b")


def check_ollama_status(host: str, timeout: float = 2.0):
    """Checks if Ollama is running and retrieves the list of installed models."""
    try:
        clean_host = host.rstrip("/")
        resp = requests.get(f"{clean_host}/api/tags", timeout=timeout)
        if resp.status_code == 200:
            models = [m.get("name") for m in resp.json().get("models", []) if m.get("name")]
            return True, models, None
        return False, [], f"HTTP {resp.status_code}"
    except Exception as e:
        logger.debug("Ollama connectivity check failed: %s", e)
        return False, [], "Connection failed"


# ---------------------------------------------------------
# Deterministic Fallback Data Generator (Demo Mode)
# ---------------------------------------------------------
def generate_fallback_data(tech_skills: str, soft_skills: str, niche: str, currency: str) -> FirstGigOutput:
    """
    Generates realistic, grounded demo output without AI inference.
    Contains no fabricated metrics, unverified guarantees, or arbitrary SLAs.
    """
    sym = "$" if "$" in currency else ("€" if "EUR" in currency else ("₹" if "INR" in currency else "£"))
    primary = tech_skills.split(",")[0].strip() if tech_skills else "Technical"

    return FirstGigOutput(
        summary=(
            f"Specialized freelance positioning combining {primary} capabilities with {soft_skills} "
            f"to solve high-value operational bottlenecks for {niche} businesses."
        ),
        services=[
            MicroService(
                title=f"{primary} Health Audit & Rapid Implementation",
                tagline="Audit workflow health and implement scoped high-priority fixes (estimated 2-3 business days pending scope).",
                target_client=f"Founders, operators, and engineering leads in {niche} needing focused technical support.",
                deliverables=[
                    "Comprehensive workflow/codebase audit report detailing top vulnerabilities & bottlenecks",
                    "Implementation of up to 3 prioritized fixes, refactors, or automation scripts",
                    "Clear video walkthrough explaining all changes and technical decisions",
                    "Optional 7-day post-handoff support window for questions and minor adjustments (agreed per contract)"
                ],
                turnaround="Estimated 2 - 3 business days (scope dependent)"
            ),
            MicroService(
                title=f"Custom {niche} Workflow Automation Pipeline",
                tagline="Streamline repetitive manual tasks and integrate core tools into an automated pipeline.",
                target_client=f"Growing {niche} teams managing fragmented tools and repetitive manual processes.",
                deliverables=[
                    "Custom integration script or lightweight automation tool connecting your daily workflows",
                    "Structured error logging and real-time failure notification alerts",
                    "Standard Operating Procedure (SOP) documentation for seamless team adoption",
                    "Handover walk-through session to review operation and maintenance"
                ],
                turnaround="Estimated 4 - 5 business days (scope dependent)"
            ),
            MicroService(
                title="Continuous Technical Support & Maintenance Retainer",
                tagline="Fractional ongoing support, routine preventive maintenance, and steady technical improvements.",
                target_client=f"Established teams in {niche} seeking a dependable fractional technical partner.",
                deliverables=[
                    "Bi-weekly system health checks, dependency updates, and preventive maintenance",
                    "Technical support and issue resolution during standard business hours (terms agreed with client)",
                    "Continuous feature enhancements (up to agreed monthly hours allotment)",
                    "Monthly status summary covering completed tasks and upcoming recommendations"
                ],
                turnaround="Monthly retainer (estimated hours agreed per contract)"
            )
        ],
        pricing=[
            PricingTier(
                tier_name="Starter Sprint",
                price=f"{sym}150 - {sym}350",
                scope="Focused entry-level audit and high-impact initial deliverable.",
                ideal_for="First-time clients seeking to validate quality on a scoped problem."
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
                scope="Ongoing fractional technical support, scheduled reviews, and routine maintenance.",
                ideal_for="Long-term clients seeking predictable monthly technical bandwidth."
            )
        ],
        outreach=OutreachScript(
            channel="Email / LinkedIn DM",
            subject_line=f"Quick idea regarding {niche} automation (not a sales pitch)",
            body=(
                f"Hi {{FirstName}},\n\n"
                f"I noticed how {{CompanyName}} is scaling within the {niche} space—congratulations on your progress.\n\n"
                f"I put together a quick observation on how you can leverage {primary} "
                f"to eliminate repetitive bottleneck tasks and improve speed.\n\n"
                f"Mind if I send over a 2-minute video walkthrough? No pressure at all.\n\n"
                f"Best regards,\n{{YourName}}\nFreelance Specialist"
            ),
            follow_up=(
                f"Hi {{FirstName}},\n\nQuick follow-up on this—completely understand if timing is not right currently.\n\n"
                f"Here is a 1-page summary for your team: [Link]\n\nBest,\n{{YourName}}"
            )
        ),
        proposal=FreelanceProposal(
            headline=f"Turnkey {primary} Solution Tailored for {{ClientName}}",
            problem_statement=(
                f"{{ClientName}} requires a dependable, modern solution to streamline key processes in {niche} "
                f"without ballooning overhead or hiring full-time engineering staff."
            ),
            proposed_solution=(
                "Phase 1: Discovery & Requirements Lock (Day 1)\n"
                "Phase 2: Core Development & Modular Testing (Days 2-3)\n"
                "Phase 3: Integration, Client Review & Revisions (Day 4)\n"
                "Phase 4: Handoff, Documentation Walkthrough & Optional Post-Handoff Review Window (Target: Day 5, pending client feedback)"
            ),
            why_me=(
                f"I combine technical precision in {tech_skills} with strong {soft_skills}. "
                f"I ensure clear communication, on-time delivery, and complete visibility at every milestone."
            ),
            call_to_action=(
                "Are you available for a brief 15-minute alignment call tomorrow or Thursday to finalize scope? "
                "Looking forward to helping you launch this smoothly."
            )
        ),
        is_fallback=True
    )


# ---------------------------------------------------------
# Ollama Query with Retry and Strict Validation
# ---------------------------------------------------------
def _clean_json_markdown(content: str) -> str:
    """Removes markdown code fences from JSON output."""
    s = content.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def query_ollama_for_firstgig(
    host: str,
    model: str,
    tech_skills: str,
    soft_skills: str,
    niche: str,
    exp_level: str,
    currency: str,
    temperature: float = 0.4,
    timeout: int = 120
) -> FirstGigOutput:
    """
    Queries Ollama to generate structured FirstGigOutput.
    Includes strict grounding rules, JSON enforcement, and a 1-time automatic retry.
    """
    clean_host = host.rstrip("/")

    prompt_instructions = (
        "You are FirstGig AI, an elite freelance career strategist.\n"
        "Convert the user's provided skills into 3 realistic micro-services, starter pricing, an outreach script, and a client proposal.\n\n"
        "GROUNDING RULES:\n"
        "- Propose ONLY services directly deliverable using the user's provided technical skills.\n"
        "- Do NOT invent certifications, fake client logos, or guaranteed financial returns/arbitrary SLAs.\n"
        "- Deliverables must be realistic, concrete, and grounded in standard freelance practice.\n\n"
        f"USER PROFILE:\n"
        f"- Technical Skills: {tech_skills}\n"
        f"- Soft Skills: {soft_skills}\n"
        f"- Target Niche: {niche}\n"
        f"- Experience Level: {exp_level}\n"
        f"- Pricing Currency: {currency}\n\n"
        "SCHEMA REQUIREMENTS (Respond with VALID JSON ONLY):\n"
        "{\n"
        '  "summary": "2-sentence positioning strategy",\n'
        '  "services": [\n'
        '    {"title":"...","tagline":"...","target_client":"...","deliverables":["...","...","..."],"turnaround":"..."}\n'
        "  ],\n"
        '  "pricing": [\n'
        '    {"tier_name":"...","price":"...","scope":"...","ideal_for":"..."}\n'
        "  ],\n"
        '  "outreach": {"channel":"...","subject_line":"...","body":"...","follow_up":"..."},\n'
        '  "proposal": {"headline":"...","problem_statement":"...","proposed_solution":"...","why_me":"...","call_to_action":"..."}\n'
        "}\n\n"
        "CRITICAL RULES: Exactly 3 services, exactly 3 pricing tiers. Deliverables must be a list of at least 2 bullet strings. Return raw JSON only."
    )

    def _call_api(temp: float, extra_instruction: str = "") -> FirstGigOutput:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Return strictly valid JSON only conforming to the requested schema. No markdown formatting, no commentary."},
                {"role": "user", "content": prompt_instructions + extra_instruction}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temp,
                "num_predict": 1200,
                "num_ctx": 2048
            }
        }
        resp = requests.post(
            f"{clean_host}/api/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=timeout
        )
        if resp.status_code == 404:
            raise RuntimeError(f"Model '{model}' not found in Ollama. Run 'ollama pull {model}' to download it.")
        if resp.status_code != 200:
            raise RuntimeError(f"Ollama returned HTTP {resp.status_code}")

        raw_content = resp.json().get("message", {}).get("content", "").strip()
        cleaned_json = _clean_json_markdown(raw_content)

        try:
            parsed = json.loads(cleaned_json)
        except json.JSONDecodeError as err:
            logger.warning("Initial JSON decode error: %s. Attempting bracket recovery.", err)
            fixed = cleaned_json
            if '"' in fixed and fixed.count('"') % 2 != 0:
                fixed += '"'
            fixed += "}" * max(0, fixed.count("{") - fixed.count("}"))
            parsed = json.loads(fixed)

        result = FirstGigOutput(**parsed)
        result.is_fallback = False
        return result

    # Attempt 1
    try:
        return _call_api(temp=temperature)
    except Exception as first_err:
        logger.warning("First inference attempt failed (%s). Retrying once with strict prompt...", first_err)
        # Retry once with low temperature and explicit instruction
        retry_extra = "\n\nCRITICAL RETRY: Ensure exactly 3 services, 3 pricing tiers, and strictly valid JSON syntax."
        return _call_api(temp=0.1, extra_instruction=retry_extra)


# ---------------------------------------------------------
# Rate Calculator Helper & Disclaimers
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
    "Upwork (Flat 10% fee)": 0.10,
    "Fiverr (Standard 20% seller fee)": 0.20,
    "Toptal (Platform fee added to client bill)": 0.00,
    "LinkedIn / Direct (0% platform fee)": 0.00,
}


def calculate_rates(exp_level: str, currency: str, platform: str) -> dict:
    """Calculates gross and net freelance rates with platform fee deductions."""
    base = RATE_TABLE.get(exp_level, RATE_TABLE["Beginner (Landing 1st gig)"])
    rates = base.get(currency, base["USD ($)"])
    fee = max(0.0, min(1.0, PLATFORM_FEE.get(platform, 0.0)))
    sym = currency.split("(")[-1].replace(")", "").strip()
    result = {}
    for rate_type, (lo, hi) in rates.items():
        net_lo = max(0, round(lo * (1 - fee)))
        net_hi = max(0, round(hi * (1 - fee)))
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
    primary = tech_skills.split(",")[0].strip() if tech_skills else "Specialist"
    service1 = data.services[0].title if data.services else f"{primary} services"
    price1 = data.pricing[0].price if data.pricing else "competitive rates"

    if platform == "Upwork Bid":
        return f"""**Hi {{ClientFirstName}},**

I came across your job post and immediately saw the overlap with the work I specialize in.

**What I bring:**
{data.proposal.why_me}

**My approach for your project:**
{data.proposal.proposed_solution}

**Starting scope:** {price1}

I would welcome a quick 15-minute conversation to clarify your exact requirements and ensure strong mutual alignment.

**Next step:** Feel free to message me here on Upwork or click "Invite to Job" to discuss details.

Looking forward to hearing from you,
— {{YourName}}"""

    elif platform == "LinkedIn Post":
        return f"""🚀 Open for freelance engagements in {niche}!

I help {niche.lower()} businesses {data.services[0].tagline.lower() if data.services else 'streamline technical bottlenecks'}.

✅ {data.services[0].title if data.services else service1}
✅ {data.services[1].title if len(data.services) > 1 else "Custom Workflow Tooling"}
✅ {data.services[2].title if len(data.services) > 2 else "Ongoing Technical Maintenance"}

💡 {data.summary}

📦 Initial engagements start at {price1}
⏱️ Estimated turnaround: {data.services[0].turnaround if data.services else "Estimated 2-3 business days"}

If your team is tackling these bottlenecks or looking for fractional support, let's connect!

#Freelance #OpenToWork #{primary.replace(' ', '')} #{niche.replace(' ', '').replace('&', '').replace('/', '')}"""

    elif platform == "Fiverr Gig Description":
        deliverables = ""
        if data.services:
            deliverables = "\n".join([f"✅ {d}" for d in data.services[0].deliverables])
        return f"""⚡ **{data.services[0].title if data.services else service1}**

{data.services[0].tagline if data.services else "Dependable, high-quality technical implementation."}

---

**Deliverables Included:**
{deliverables}

**Why Work With Me:**
{data.proposal.why_me}

**Estimated Turnaround:** {data.services[0].turnaround if data.services else "Estimated 2-3 business days (dependent on scope)"}

---

📌 **Please message me before placing an order** so we can verify requirements and ensure this package meets your exact goals."""

    elif platform == "Cold Email":
        return f"""Subject: {data.outreach.subject_line}

{data.outreach.body}

---

P.S. If helpful, I am glad to share a short portfolio overview or sample workflow breakdown for your team."""

    return ""


# ---------------------------------------------------------
# Markdown Exporter
# ---------------------------------------------------------
def convert_to_markdown(data: FirstGigOutput, tech_skills: str, soft_skills: str, niche: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    mode_badge = "⚠️ DEMO / SAMPLE BLUEPRINT (Deterministic Fallback)" if data.is_fallback else "⚡ LIVE AI BLUEPRINT (Local Inference)"

    md = f"""# FirstGig AI — Freelance Launch Blueprint
*{mode_badge} | Generated on {now}*

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
*Note: Pricing and turnaround estimates are illustrative guidelines. Independent review of client scope and platform terms is recommended.*
"""
    return md


# ---------------------------------------------------------
# PDF Exporter (Safe Unicode & Margin Handling)
# ---------------------------------------------------------
def _sanitize_pdf_text(text: str) -> str:
    """
    Substitutes common Unicode typography with ASCII/Latin-1 safe equivalents,
    preventing FPDF character rendering exceptions.
    """
    if not text:
        return ""
    replacements = {
        "—": "--",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "…": "...",
        "₹": "INR ",
        "€": "EUR ",
        "£": "GBP ",
        "™": "(TM)",
        "©": "(c)",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(data: FirstGigOutput, tech_skills: str, soft_skills: str, niche: str) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=18, top=18, right=18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    PAGE_W = 174  # A4 210mm minus 18mm left + 18mm right margins

    # Title & Header
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(PAGE_W, 10, _sanitize_pdf_text("FirstGig AI  --  Freelance Blueprint"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    mode_str = "SAMPLE DEMO BLUEPRINT" if data.is_fallback else "AI GENERATED"
    pdf.cell(PAGE_W, 5, _sanitize_pdf_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Mode: {mode_str}  |  Niche: {niche}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    def section_title(title: str):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(56, 189, 248)
        pdf.cell(PAGE_W, 7, _sanitize_pdf_text(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(56, 189, 248)
        pdf.line(18, pdf.get_y(), 192, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(30, 41, 59)

    def body_text(text: str):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 60, 80)
        pdf.multi_cell(PAGE_W, 5, _sanitize_pdf_text(text))
        pdf.ln(1)

    def label_value(label: str, value: str):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(35, 5, _sanitize_pdf_text(label + ":"))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(PAGE_W - 35, 5, _sanitize_pdf_text(value))

    # Positioning Profile
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
        pdf.cell(PAGE_W, 6, _sanitize_pdf_text(f"Service {i}: {s.title}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(56, 189, 248)
        pdf.multi_cell(PAGE_W, 4, _sanitize_pdf_text(f'"{s.tagline}"'))
        label_value("Ideal Client", s.target_client)
        label_value("Turnaround", s.turnaround)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(PAGE_W, 4, "Deliverables:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(30, 41, 59)
        for d in s.deliverables:
            pdf.set_x(pdf.l_margin + 4)
            pdf.multi_cell(PAGE_W - 4, 4, _sanitize_pdf_text(f"* {d}"))
        pdf.ln(3)

    # Pricing
    section_title("3-Tier Pricing Strategy (Illustrative)")
    for p in data.pricing:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(PAGE_W, 6, _sanitize_pdf_text(f"{p.tier_name}  --  {p.price}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
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
    pdf.cell(PAGE_W, 4, "Initial Message:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    body_text(data.outreach.body)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(PAGE_W, 4, "Follow-Up Message:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    body_text(data.outreach.follow_up)

    # Proposal
    section_title("Freelance Proposal Template")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(PAGE_W, 6, _sanitize_pdf_text(data.proposal.headline))
    pdf.ln(1)
    label_value("Problem", data.proposal.problem_statement)
    label_value("Solution", data.proposal.proposed_solution)
    label_value("Why Me", data.proposal.why_me)
    label_value("CTA", data.proposal.call_to_action)

    # Footer Disclaimer
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(PAGE_W, 4, _sanitize_pdf_text("Disclaimer: Rates, deliverables, and outreach templates are sample guidelines. Always tailor proposals and verify platform agreements directly with clients."), align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ---------------------------------------------------------
# SIDEBAR: Engine & Presets
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ AI Engine Configuration")
    ollama_host = st.text_input("Ollama Endpoint", value=DEFAULT_OLLAMA_HOST,
                                help="Local or remote Ollama server URL.")
    is_online, models_list, _ = check_ollama_status(ollama_host)

    if is_online:
        st.markdown('<div class="status-pill-online"><span class="pulse-dot"></span> Ollama Connected</div>', unsafe_allow_html=True)
        preferred = DEFAULT_OLLAMA_MODEL
        sel_idx = models_list.index(preferred) if preferred in models_list else 0
        selected_model = st.selectbox("Selected Model", options=models_list or [preferred], index=sel_idx)
    else:
        st.markdown('<div class="status-pill-offline"><span class="pulse-dot"></span> Ollama Offline</div>', unsafe_allow_html=True)
        selected_model = st.text_input("Model Name", value=DEFAULT_OLLAMA_MODEL)
        st.caption("ℹ️ Local inference requires Ollama running on your machine.\n*(Demo Mode auto-activates when offline)*")

    use_demo_mode = st.checkbox("Sample Demo Mode (Instant, No Ollama needed)", value=not is_online,
                                help="Generate sample blueprints using deterministic templates.")

    st.markdown("---")
    st.markdown("### 🎛️ Generation Tuning")
    temperature = st.slider("Creativity / Temperature", 0.1, 1.0, 0.4, 0.05)

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
# Preset Profiles
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

default_tech = "Python, Web Scraping, API Integration, Task Automation"
default_soft = "Clear communication, timely delivery, client empathy"
default_niche = "B2B E-Commerce & Retail Brands"

if preset in PRESETS:
    default_tech = PRESETS[preset]["tech"]
    default_soft = PRESETS[preset]["soft"]
    default_niche = PRESETS[preset]["niche"]


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown(
    """<div class="hero-container">
        <div class="hero-title">⚡ FirstGig AI</div>
        <p class="hero-subtitle">
            Transform technical and soft skills into 3 realistic micro-services, starter pricing,
            targeted cold outreach, and structured freelance proposals — optimized for local inference with Gemma 2 2B.
        </p>
    </div>""",
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# INPUT FORM
# ---------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    raw_tech_skills = st.text_area("🛠️ Technical Skills & Tools", value=default_tech, height=100,
                                   help="Languages, frameworks, tools you know (max 500 characters).")
    raw_niche = st.text_input("🎯 Target Industry / Niche", value=default_niche,
                              help="e.g. E-commerce Brands, Local Dentists, B2B SaaS (max 500 characters).")
with col2:
    raw_soft_skills = st.text_area("🤝 Soft Skills & Strengths", value=default_soft, height=100,
                                   help="Communication, speed, reliability, domain expertise (max 500 characters).")
    c1, c2 = st.columns(2)
    with c1:
        exp_level = st.selectbox("📈 Experience Level",
                                 ["Beginner (Landing 1st gig)", "Intermediate (Some projects)", "Seasoned Pro (Upscaling rates)"])
    with c2:
        currency = st.selectbox("💵 Pricing Currency", ["USD ($)", "EUR (€)", "INR (₹)", "GBP (£)"])

# Sanitize inputs
tech_skills = sanitize_input(raw_tech_skills)
soft_skills = sanitize_input(raw_soft_skills)
niche = sanitize_input(raw_niche)

generate_btn = st.button("🚀 Generate FirstGig Blueprint", type="primary", use_container_width=True)

# ---------------------------------------------------------
# SESSION STATE MANAGEMENT
# ---------------------------------------------------------
if "blueprint_data" not in st.session_state:
    st.session_state.blueprint_data = None
if "blueprint_markdown" not in st.session_state:
    st.session_state.blueprint_markdown = None
if "blueprint_inputs" not in st.session_state:
    st.session_state.blueprint_inputs = None

# ---------------------------------------------------------
# GENERATION LOGIC
# ---------------------------------------------------------
if generate_btn:
    if not tech_skills or not niche:
        st.error("Please enter both technical skills and a target niche before generating.")
    else:
        with st.spinner("🧠 Generating your freelance blueprint..."):
            t0 = time.time()
            try:
                if use_demo_mode or not is_online:
                    time.sleep(0.5)
                    result_data = generate_fallback_data(tech_skills, soft_skills, niche, currency)
                else:
                    result_data = query_ollama_for_firstgig(
                        host=ollama_host,
                        model=selected_model,
                        tech_skills=tech_skills,
                        soft_skills=soft_skills,
                        niche=niche,
                        exp_level=exp_level,
                        currency=currency,
                        temperature=temperature
                    )
                st.session_state.blueprint_data = result_data
                st.session_state.blueprint_markdown = convert_to_markdown(result_data, tech_skills, soft_skills, niche)
                st.session_state.blueprint_inputs = {
                    "tech": tech_skills,
                    "soft": soft_skills,
                    "niche": niche,
                    "currency": currency,
                    "exp": exp_level
                }
                elapsed = round(time.time() - t0, 2)
                st.success(f"✨ Blueprint ready in {elapsed}s!")
            except Exception as ex:
                logger.error("Inference failure: %s", ex, exc_info=True)
                st.warning("⚠️ Local Ollama inference encountered an issue. Loaded verified sample demo blueprint.")
                result_data = generate_fallback_data(tech_skills, soft_skills, niche, currency)
                st.session_state.blueprint_data = result_data
                st.session_state.blueprint_markdown = convert_to_markdown(result_data, tech_skills, soft_skills, niche)
                st.session_state.blueprint_inputs = {
                    "tech": tech_skills,
                    "soft": soft_skills,
                    "niche": niche,
                    "currency": currency,
                    "exp": exp_level
                }

# ---------------------------------------------------------
# RESULTS DISPLAY
# ---------------------------------------------------------
data: Optional[FirstGigOutput] = st.session_state.blueprint_data

if data:
    st.markdown("---")

    # Banner distinguishing live inference from demo fallback
    if data.is_fallback:
        st.info("ℹ️ **Sample Demo Blueprint**: These results are generated via verified deterministic templates for demonstration. Connect a local Ollama instance running Gemma 2 2B for personalized AI inference.")
    else:
        st.success("⚡ **AI-Generated Blueprint**: Personalized results produced via local Gemma 2 2B inference.")

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
            deliverables_html = "".join([f"<li style='margin-bottom:4px'>{safe_html(d)}</li>" for d in service.deliverables])
            card_html = (
                f'<div class="service-card">'
                f'<span class="card-badge">Service {idx + 1}</span>'
                f'<h4 style="margin:8px 0;color:#f1f5f9">{safe_html(service.title)}</h4>'
                f'<p style="color:#38bdf8;font-size:0.9rem;font-style:italic;margin-bottom:10px">"{safe_html(service.tagline)}"</p>'
                f'<p style="font-size:0.85rem;color:#cbd5e1"><b>Ideal Client:</b> {safe_html(service.target_client)}</p>'
                f'<p style="font-size:0.85rem;color:#cbd5e1;margin-bottom:4px"><b>Deliverables:</b></p>'
                f'<ul style="font-size:0.82rem;color:#94a3b8;padding-left:18px;margin-bottom:12px">{deliverables_html}</ul>'
                f'<div style="font-size:0.8rem;background:rgba(15,23,42,0.7);padding:8px 12px;border-radius:6px;border:1px solid rgba(255,255,255,0.08);color:#f1f5f9">'
                f'⏱️ <b>Turnaround:</b> <span style="color:#34d399;font-weight:600">{safe_html(service.turnaround)}</span>'
                f'</div></div>'
            )
            with cols[idx]:
                st.markdown(card_html, unsafe_allow_html=True)

    # ── Tab 2: Pricing Strategy ──
    with tab2:
        st.markdown("### 💰 Recommended 3-Tier Pricing Model")
        st.caption("Illustrative starter pricing structure to anchor value perception and offer options.")
        pcols = st.columns(3)
        tier_styles = [
            ("rgba(15,23,42,0.9)", "1px solid rgba(99,102,241,0.2)", ""),
            ("linear-gradient(180deg,rgba(30,27,75,0.6)0%,rgba(15,23,42,0.95)100%)", "2px solid #818cf8", "box-shadow:0 8px 24px rgba(99,102,241,0.25);"),
            ("rgba(15,23,42,0.9)", "1px solid rgba(99,102,241,0.2)", ""),
        ]
        for i, (tier, (bg, border, extra)) in enumerate(zip(data.pricing, tier_styles)):
            badge = '<span class="card-badge" style="background:rgba(129,140,248,0.25);color:#a5b4fc">⭐ Recommended</span><br>' if i == 1 else ''
            html_content = (
                f'<div style="background:{bg};border:{border};border-radius:14px;padding:22px;text-align:center;{extra}">'
                f'{badge}'
                f'<h3 style="color:#f8fafc;margin:8px 0 4px">{safe_html(tier.tier_name)}</h3>'
                f'<div style="font-size:1.8rem;font-weight:800;color:#38bdf8;margin:10px 0">{safe_html(tier.price)}</div>'
                f'<p style="color:#cbd5e1;font-size:0.9rem;margin-bottom:14px">{safe_html(tier.scope)}</p>'
                f'<hr style="border:0;border-top:1px solid rgba(255,255,255,0.1);margin:10px 0">'
                f'<p style="font-size:0.82rem;color:#94a3b8"><b>Target Buyer:</b><br>{safe_html(tier.ideal_for)}</p>'
                f'</div>'
            )
            with pcols[i]:
                st.markdown(html_content, unsafe_allow_html=True)

        st.caption("⚠️ **Pricing Disclaimer:** Price ranges are illustrative estimates based on typical market brackets. Actual rates depend on scope complexity, client geography, urgency, and individual negotiations.")

    # ── Tab 3: Rate Calculator ──
    with tab3:
        st.markdown("### 📊 Platform-Specific Rate Calculator")
        st.caption("Estimate gross and net earnings after typical platform fee deductions.")
        rc1, rc2 = st.columns(2)
        with rc1:
            calc_platform = st.selectbox("Choose Platform", list(PLATFORM_FEE.keys()), key="calc_plat")
        with rc2:
            calc_exp = st.selectbox("Experience Level", list(RATE_TABLE.keys()), key="calc_exp",
                                    index=list(RATE_TABLE.keys()).index(exp_level) if exp_level in RATE_TABLE else 0)

        rates = calculate_rates(calc_exp, currency, calc_platform)
        fee_pct = int(PLATFORM_FEE[calc_platform] * 100)

        if fee_pct > 0:
            st.warning(f"⚠️ **{safe_html(calc_platform)}**: Approx. {fee_pct}% service deduction. Net rates reflect estimated take-home before local taxes.")
        else:
            st.success(f"✅ **{safe_html(calc_platform)}**: No platform-level deduction. Payment processing or subscription fees may still apply.")

        r1, r2, r3 = st.columns(3)
        labels = {
            "hourly": ("⏱️ Hourly Rate", "Estimated per hour"),
            "project": ("📦 Project Rate", "Fixed-scope milestone"),
            "monthly": ("📅 Monthly Retainer", "Ongoing engagement")
        }
        for col, (rate_key, (title, subtitle)) in zip([r1, r2, r3], labels.items()):
            if rate_key in rates:
                r = rates[rate_key]
                with col:
                    st.markdown(
                        f'<div class="rate-card">'
                        f'<div class="rate-label">{safe_html(title)}</div>'
                        f'<div class="rate-value">{safe_html(r["net"])}</div>'
                        f'<div style="font-size:0.75rem;color:#64748b">Gross: {safe_html(r["gross"])}<br>Platform cut: {safe_html(r["platform_cut"])}</div>'
                        f'<div style="font-size:0.72rem;color:#475569;margin-top:6px">{safe_html(subtitle)}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

        st.markdown("---")
        st.markdown("#### 💡 Platform Strategy Notes")
        tips = {
            "Upwork (Flat 10% fee)": "Upwork charges a 10% freelancer service fee. Focus proposals on specific problem comprehension and include concrete milestone roadmaps.",
            "Fiverr (Standard 20% seller fee)": "Fiverr retains a 20% fee. Tier your gig into 3 clear packages where the middle tier represents the most compelling scope.",
            "Toptal (Platform fee added to client bill)": "Toptal bills the client a markup over your agreed net hourly rate. Position as a vetted specialist.",
            "LinkedIn / Direct (0% platform fee)": "Direct billing avoids marketplace fees, though standard merchant payment processing (e.g. Stripe ~2.9% + $0.30) still applies.",
        }
        st.info(tips.get(calc_platform, "Deliver measurable business outcomes rather than selling raw hours."))

    # ── Tab 4: Cold Outreach ──
    with tab4:
        st.markdown("### 📨 Cold Outreach Playbook")
        st.caption("Personalized, value-first outreach scripts ready to review and adapt.")
        st.markdown(f"**Channel:** `{data.outreach.channel}`")
        st.markdown(f"**Subject Line:** `{data.outreach.subject_line}`")
        st.markdown("#### Initial Outreach Message:")
        st.code(data.outreach.body, language="text")
        st.markdown("#### Polite Follow-Up (After 3 Business Days):")
        st.code(data.outreach.follow_up, language="text")

    # ── Tab 5: Proposal ──
    with tab5:
        st.markdown("### 📝 Structured Client Proposal")
        st.caption("Adapt this proposal outline for Upwork, freelance platforms, or client email bids.")
        st.subheader(data.proposal.headline)
        with st.expander("1. Understanding the Problem (Empathy & Context)", expanded=True):
            st.write(data.proposal.problem_statement)
        with st.expander("2. Proposed Solution & Milestone Roadmap", expanded=True):
            st.write(data.proposal.proposed_solution)
        with st.expander("3. Why Choose Me?", expanded=True):
            st.write(data.proposal.why_me)
        with st.expander("4. Recommended Next Step (Call to Action)", expanded=True):
            st.write(data.proposal.call_to_action)

    # ── Tab 6: Platform Posts ──
    with tab6:
        st.markdown("### 🔗 Platform-Specific Post Formatter")
        st.caption("Directly formatted copy for freelance bids, gig listings, and social outreach.")

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
            f'<span class="platform-badge {safe_html(badge_map.get(platform_choice, ""))}">{safe_html(platform_choice)}</span>',
            unsafe_allow_html=True
        )
        st.text_area("📋 Copy ready text:", value=post_content, height=350, key="platform_post_output")
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
        st.caption("Download the complete blueprint in Markdown or formatted PDF format.")

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
            if st.button("💾 Save .md to Project Directory", use_container_width=True):
                save_path = os.path.join(os.getcwd(), "FirstGig_Blueprint.md")
                try:
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(st.session_state.blueprint_markdown)
                    st.success(f"Saved to `{save_path}`!")
                except Exception as err:
                    logger.error("Failed to save blueprint: %s", err)
                    st.error("Failed to save file locally.")

        st.markdown("#### Preview Raw Markdown:")
        st.text_area("Markdown Preview", value=st.session_state.blueprint_markdown, height=300)
