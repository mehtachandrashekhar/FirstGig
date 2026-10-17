import pytest
from pydantic import ValidationError
from app import MicroService, PricingTier, OutreachScript, FreelanceProposal, FirstGigOutput


def test_valid_micro_service():
    service = MicroService(
        title="Python Web Scraper",
        tagline="Extract clean data from target sites",
        target_client="E-commerce founders needing lead generation",
        deliverables=["Scraping script", "CSV export", "Execution docs"],
        turnaround="Estimated 2-3 business days"
    )
    assert service.title == "Python Web Scraper"
    assert len(service.deliverables) == 3


def test_micro_service_empty_fields_fail():
    with pytest.raises(ValidationError):
        MicroService(
            title="   ",
            tagline="Tagline here",
            target_client="Target client",
            deliverables=["Deliv 1", "Deliv 2"],
            turnaround="Estimated 2 days"
        )


def test_micro_service_insufficient_deliverables():
    with pytest.raises(ValidationError):
        MicroService(
            title="Valid Title",
            tagline="Valid Tagline",
            target_client="Valid Client",
            deliverables=["Only One Deliverable"],
            turnaround="Estimated 2 days"
        )


def test_pricing_tier_empty_fields_fail():
    with pytest.raises(ValidationError):
        PricingTier(
            tier_name="",
            price="$100",
            scope="Valid scope description",
            ideal_for="Target buyer"
        )


def test_outreach_script_empty_fields_fail():
    with pytest.raises(ValidationError):
        OutreachScript(
            channel="Email",
            subject_line="",
            body="Valid message body for pitch",
            follow_up="Valid follow-up message"
        )


def test_freelance_proposal_empty_fields_fail():
    with pytest.raises(ValidationError):
        FreelanceProposal(
            headline="",
            problem_statement="Problem description text",
            proposed_solution="Solution steps text",
            why_me="Why me explanation",
            call_to_action="Call to action"
        )


def test_firstgig_output_requires_exactly_three_services():
    valid_service = MicroService(
        title="Valid Service",
        tagline="Valid Tagline",
        target_client="Valid Client",
        deliverables=["Deliverable 1", "Deliverable 2"],
        turnaround="Estimated 2-3 business days"
    )
    valid_pricing = PricingTier(
        tier_name="Starter",
        price="$150",
        scope="Basic audit",
        ideal_for="Beginners"
    )
    valid_outreach = OutreachScript(
        channel="Email",
        subject_line="Quick note",
        body="Value-focused pitch message body text",
        follow_up="Polite follow up message"
    )
    valid_proposal = FreelanceProposal(
        headline="Winning Proposal",
        problem_statement="Client pain point statement",
        proposed_solution="Detailed solution steps",
        why_me="Technical and soft skill strengths",
        call_to_action="Let's schedule a call"
    )

    # 2 services should fail (must be exactly 3)
    with pytest.raises(ValidationError):
        FirstGigOutput(
            summary="Strategic summary for testing",
            services=[valid_service, valid_service],
            pricing=[valid_pricing, valid_pricing, valid_pricing],
            outreach=valid_outreach,
            proposal=valid_proposal
        )

    # 4 services should fail
    with pytest.raises(ValidationError):
        FirstGigOutput(
            summary="Strategic summary for testing",
            services=[valid_service, valid_service, valid_service, valid_service],
            pricing=[valid_pricing, valid_pricing, valid_pricing],
            outreach=valid_outreach,
            proposal=valid_proposal
        )


def test_firstgig_output_requires_exactly_three_pricing_tiers():
    valid_service = MicroService(
        title="Valid Service",
        tagline="Valid Tagline",
        target_client="Valid Client",
        deliverables=["Deliverable 1", "Deliverable 2"],
        turnaround="Estimated 2-3 business days"
    )
    valid_pricing = PricingTier(
        tier_name="Starter",
        price="$150",
        scope="Basic audit",
        ideal_for="Beginners"
    )
    valid_outreach = OutreachScript(
        channel="Email",
        subject_line="Quick note",
        body="Value-focused pitch message body text",
        follow_up="Polite follow up message"
    )
    valid_proposal = FreelanceProposal(
        headline="Winning Proposal",
        problem_statement="Client pain point statement",
        proposed_solution="Detailed solution steps",
        why_me="Technical and soft skill strengths",
        call_to_action="Let's schedule a call"
    )

    # 2 pricing tiers should fail
    with pytest.raises(ValidationError):
        FirstGigOutput(
            summary="Strategic summary for testing",
            services=[valid_service, valid_service, valid_service],
            pricing=[valid_pricing, valid_pricing],
            outreach=valid_outreach,
            proposal=valid_proposal
        )

    # 4 pricing tiers should fail
    with pytest.raises(ValidationError):
        FirstGigOutput(
            summary="Strategic summary for testing",
            services=[valid_service, valid_service, valid_service],
            pricing=[valid_pricing, valid_pricing, valid_pricing, valid_pricing],
            outreach=valid_outreach,
            proposal=valid_proposal
        )

    # Exactly 3 should pass
    output = FirstGigOutput(
        summary="Strategic summary for testing",
        services=[valid_service, valid_service, valid_service],
        pricing=[valid_pricing, valid_pricing, valid_pricing],
        outreach=valid_outreach,
        proposal=valid_proposal
    )
    assert len(output.services) == 3
    assert len(output.pricing) == 3
    assert output.is_fallback is False
