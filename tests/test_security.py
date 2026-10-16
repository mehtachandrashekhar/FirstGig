from app import safe_html, sanitize_input


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
