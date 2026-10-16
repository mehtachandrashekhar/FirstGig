from app import generate_fallback_data, FirstGigOutput


def test_generate_fallback_data_structure():
    data = generate_fallback_data(
        tech_skills="Python, SQL, FastAPI",
        soft_skills="Clear communication, fast turnaround",
        niche="Fintech & SaaS Startups",
        currency="USD ($)"
    )

    assert isinstance(data, FirstGigOutput)
    assert data.is_fallback is True
    assert len(data.services) == 3
    assert len(data.pricing) == 3
    assert "Python" in data.summary or "Python" in data.services[0].title
    assert data.outreach.body
    assert data.proposal.proposed_solution


def test_fallback_data_has_no_arbitrary_guarantees():
    data = generate_fallback_data(
        tech_skills="React, Node.js",
        soft_skills="Dependability",
        niche="E-commerce",
        currency="EUR (€)"
    )

    all_text = " ".join([
        data.summary,
        *[s.title + " " + s.tagline + " " + " ".join(s.deliverables) for s in data.services],
        *[p.tier_name + " " + p.scope for p in data.pricing],
        data.proposal.headline + " " + data.proposal.proposed_solution
    ]).lower()

    # Verify no fabricated emergency SLA or unsupported guarantees exist
    assert "guaranteed 4-hour emergency response sla" not in all_text
    assert "save 10+ hours per week" not in all_text
    assert "7-day guarantee" not in all_text
