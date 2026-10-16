import json
from unittest.mock import patch, MagicMock
import pytest
import requests

from app import query_ollama_for_firstgig, check_ollama_status, FirstGigOutput


SAMPLE_OLLAMA_RESPONSE = {
    "summary": "Expert Python developer specializing in financial data pipelines and reporting automation.",
    "services": [
        {
            "title": "Financial Pipeline Audit",
            "tagline": "Audit and streamline reporting scripts within 48 hours",
            "target_client": "Fintech teams with manual reporting overhead",
            "deliverables": ["Code review report", "Automated SQL extract", "Setup guide"],
            "turnaround": "48 Hours"
        },
        {
            "title": "Automated Reconciliation Pipeline",
            "tagline": "Connect banking feeds to internal ledgers smoothly",
            "target_client": "Growing accounting and finance operators",
            "deliverables": ["Reconciliation script", "Error notification webhook", "Team documentation"],
            "turnaround": "4 Days"
        },
        {
            "title": "Quarterly Data Maintenance Retainer",
            "tagline": "Dependable fractional engineering support for routine reporting",
            "target_client": "Established CFO offices seeking outsourced maintenance",
            "deliverables": ["Monthly health audit", "Priority bug resolution", "System updates"],
            "turnaround": "Monthly Ongoing"
        }
    ],
    "pricing": [
        {"tier_name": "Starter Audit", "price": "$250", "scope": "Initial pipeline audit", "ideal_for": "New clients"},
        {"tier_name": "Full Implementation", "price": "$850", "scope": "End to end integration", "ideal_for": "Funded teams"},
        {"tier_name": "Monthly Retainer", "price": "$600/mo", "scope": "Ongoing maintenance", "ideal_for": "Stable firms"}
    ],
    "outreach": {
        "channel": "Email",
        "subject_line": "Idea regarding your reporting pipeline",
        "body": "Hi there, I noticed your finance automation efforts and put together a quick observation.",
        "follow_up": "Hi, just following up in case this is of interest."
    },
    "proposal": {
        "headline": "Reliable Python Data Automation for Your Operations",
        "problem_statement": "Manual reporting slows down monthly closing cycles.",
        "proposed_solution": "Phase 1: Analysis, Phase 2: Implementation, Phase 3: Verification.",
        "why_me": "Combining Python depth with transparent, frequent client communication.",
        "call_to_action": "Let's schedule a 15-minute alignment call this week."
    }
}


def test_check_ollama_status_offline():
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Offline")):
        online, models, err = check_ollama_status("http://localhost:11434")
        assert online is False
        assert models == []
        assert err == "Connection failed"


def test_check_ollama_status_online():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "gemma2:2b"}, {"name": "llama3:8b"}]}

    with patch("requests.get", return_value=mock_resp):
        online, models, err = check_ollama_status("http://localhost:11434")
        assert online is True
        assert "gemma2:2b" in models
        assert err is None


def test_query_ollama_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {"content": json.dumps(SAMPLE_OLLAMA_RESPONSE)}
    }

    with patch("requests.post", return_value=mock_resp):
        result = query_ollama_for_firstgig(
            host="http://localhost:11434",
            model="gemma2:2b",
            tech_skills="Python, SQL",
            soft_skills="Clear communication",
            niche="Fintech",
            exp_level="Intermediate (Some projects)",
            currency="USD ($)"
        )

        assert isinstance(result, FirstGigOutput)
        assert result.is_fallback is False
        assert len(result.services) == 3
        assert len(result.pricing) == 3
        assert result.services[0].title == "Financial Pipeline Audit"


def test_query_ollama_retry_success():
    # First call returns invalid JSON, second call returns valid JSON
    bad_resp = MagicMock()
    bad_resp.status_code = 200
    bad_resp.json.return_value = {"message": {"content": "INVALID JSON TEXT"}}

    good_resp = MagicMock()
    good_resp.status_code = 200
    good_resp.json.return_value = {"message": {"content": json.dumps(SAMPLE_OLLAMA_RESPONSE)}}

    with patch("requests.post", side_effect=[bad_resp, good_resp]):
        result = query_ollama_for_firstgig(
            host="http://localhost:11434",
            model="gemma2:2b",
            tech_skills="Python",
            soft_skills="Speed",
            niche="SaaS",
            exp_level="Beginner",
            currency="USD ($)"
        )
        assert isinstance(result, FirstGigOutput)
        assert len(result.services) == 3


def test_query_ollama_model_not_found():
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(RuntimeError) as exc_info:
            query_ollama_for_firstgig(
                host="http://localhost:11434",
                model="nonexistent_model",
                tech_skills="Python",
                soft_skills="Speed",
                niche="SaaS",
                exp_level="Beginner",
                currency="USD ($)"
            )
        assert "not found" in str(exc_info.value).lower()
