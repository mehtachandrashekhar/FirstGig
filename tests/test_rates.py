from app import calculate_rates, RATE_TABLE, PLATFORM_FEE


def test_calculate_rates_upwork_fee():
    rates = calculate_rates(
        exp_level="Beginner (Landing 1st gig)",
        currency="USD ($)",
        platform="Upwork (Flat 10% fee)"
    )
    assert "hourly" in rates
    assert "project" in rates
    assert "monthly" in rates
    assert rates["hourly"]["platform_cut"] == "10%"

    # Base Beginner USD hourly is 15 to 35
    # With 10% fee: 15 * 0.9 = 13.5 -> 14, 35 * 0.9 = 31.5 -> 32
    assert "14" in rates["hourly"]["net"]
    assert "32" in rates["hourly"]["net"]


def test_calculate_rates_direct_no_fee():
    rates = calculate_rates(
        exp_level="Seasoned Pro (Upscaling rates)",
        currency="USD ($)",
        platform="LinkedIn / Direct (0% platform fee)"
    )
    assert rates["hourly"]["platform_cut"] == "0%"
    # 75 - 200
    assert "75" in rates["hourly"]["net"]
    assert "200" in rates["hourly"]["net"]


def test_calculate_rates_fiverr_fee():
    rates = calculate_rates(
        exp_level="Intermediate (Some projects)",
        currency="EUR (€)",
        platform="Fiverr (Standard 20% seller fee)"
    )
    assert rates["hourly"]["platform_cut"] == "20%"
    # Base Intermediate EUR hourly is 32 to 68
    # With 20% fee: 32 * 0.8 = 25.6 -> 26, 68 * 0.8 = 54.4 -> 54
    assert "26" in rates["hourly"]["net"]
    assert "54" in rates["hourly"]["net"]


def test_calculate_rates_fallback_defaults():
    # Test with unknown/missing keys
    rates = calculate_rates(
        exp_level="Nonexistent Level",
        currency="Unknown Currency ($)",
        platform="Nonexistent Platform"
    )
    assert "hourly" in rates
    assert rates["hourly"]["platform_cut"] == "0%"
