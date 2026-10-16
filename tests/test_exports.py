from app import convert_to_markdown, generate_pdf, generate_fallback_data, _sanitize_pdf_text


def test_markdown_export_contains_all_sections():
    data = generate_fallback_data(
        tech_skills="Python, SQL",
        soft_skills="Reliable",
        niche="Fintech",
        currency="USD ($)"
    )
    md = convert_to_markdown(data, "Python, SQL", "Reliable", "Fintech")

    assert "# FirstGig AI — Freelance Launch Blueprint" in md
    assert "DEMO / SAMPLE BLUEPRINT" in md
    assert "## 🎯 Positioning Profile" in md
    assert "## 🛠️ Micro-Services" in md
    assert "Service 1:" in md
    assert "Service 2:" in md
    assert "Service 3:" in md
    assert "## 💰 Starter Pricing Strategy" in md
    assert "## 📨 Cold Outreach Playbook" in md
    assert "## 📝 Client Proposal Template" in md


def test_sanitize_pdf_text_replaces_unicode_safely():
    text = "Em dash — En dash – Quotes “smart” and ‘single’ bullet • rupee ₹ euro € pound £"
    sanitized = _sanitize_pdf_text(text)
    assert "--" in sanitized
    assert '"' in sanitized
    assert "'" in sanitized
    assert "*" in sanitized
    assert "INR" in sanitized
    assert "EUR" in sanitized
    assert "GBP" in sanitized


def test_pdf_export_succeeds_with_unicode_and_long_text():
    data = generate_fallback_data(
        tech_skills="Python 3.11, PyTorch, LangChain — Advanced AI / ML",
        soft_skills="Clear communication & proactive updates",
        niche="Healthcare “MedTech” & Clinical Research",
        currency="INR (₹)"
    )

    pdf_bytes = generate_pdf(
        data=data,
        tech_skills="Python 3.11, PyTorch, LangChain — Advanced AI / ML",
        soft_skills="Clear communication & proactive updates",
        niche="Healthcare “MedTech” & Clinical Research"
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
