from app import safe_html, sanitize_input, MicroService


def test_safe_html_escapes_script_tags():
    malicious = "<script>alert('XSS')</script>"
    escaped = safe_html(malicious)
    assert "<script>" not in escaped
    assert "&lt;script&gt;" in escaped
    assert "&lt;/script&gt;" in escaped


def test_safe_html_escapes_attributes():
    payload = '<img src="x" onerror="alert(1)">'
    escaped = safe_html(payload)
    assert '<img' not in escaped
    assert '&lt;img' in escaped
    assert '&quot;' in escaped or '"' not in escaped


def test_safe_html_escapes_svg_and_iframe():
    svg_payload = '<svg onload="alert(1)">'
    iframe_payload = '<iframe src="javascript:alert(1)"></iframe>'
    assert "<svg" not in safe_html(svg_payload)
    assert "&lt;svg" in safe_html(svg_payload)
    assert "<iframe" not in safe_html(iframe_payload)
    assert "&lt;iframe" in safe_html(iframe_payload)


def test_safe_html_handles_none_and_numbers():
    assert safe_html(None) == ""
    assert safe_html(123) == "123"
    assert safe_html("") == ""


def test_sanitize_input_truncates_and_strips():
    long_input = "   " + "A" * 600 + "   "
    sanitized = sanitize_input(long_input, max_len=500)
    assert len(sanitized) == 500
    assert not sanitized.startswith(" ")
    assert not sanitized.endswith(" ")


def test_sanitize_input_handles_empty():
    assert sanitize_input(None) == ""
    assert sanitize_input("   ") == ""


def test_malicious_deliverables_escaped_in_service_card():
    # Simulates rendering a card with AI or user injected payload in deliverables
    service = MicroService(
        title="Test <script>alert(1)</script>",
        tagline="Test Tagline <b onmouseover='alert(2)'>hover</b>",
        target_client="Target <img src=x onerror=alert(3)>",
        deliverables=[
            "Item 1 <iframe src='malicious.com'></iframe>",
            "Item 2 <svg onload='alert(4)'>"
        ],
        turnaround="Estimated 2 days"
    )

    deliverables_html = "".join([f"<li style='margin-bottom:4px'>{safe_html(d)}</li>" for d in service.deliverables])

    assert "<iframe" not in deliverables_html
    assert "&lt;iframe" in deliverables_html
    assert "<svg" not in deliverables_html
    assert "&lt;svg" in deliverables_html
    assert "<script>" not in safe_html(service.title)
    assert "&lt;script&gt;" in safe_html(service.title)
