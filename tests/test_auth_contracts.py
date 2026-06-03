from __future__ import annotations

from elbysodic.services.auth import (
    SESSION_COOKIE,
    auth_trust_posture,
    format_auth_trust_posture,
    seed_passwords_enabled,
)


def test_auth_trust_posture_reports_production_demo_state_without_secret(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "super-secret-production-key-value")

    posture = auth_trust_posture()
    report = format_auth_trust_posture(posture)

    assert posture.production is True
    assert posture.demo_mode_enabled is True
    assert posture.seed_passwords_enabled is True
    assert posture.secret_key_configured is True
    assert posture.secret_key_meets_minimum is True
    assert posture.session_cookie_name == SESSION_COOKIE
    assert posture.development_identity_allowed is False
    assert posture.session_required_for_app_routes is True
    assert seed_passwords_enabled() is True
    assert "production demo mode accepts seeded demo passwords" in posture.warnings
    assert "super-secret-production-key-value" not in report
    assert "secret_key_configured: yes" in report
    assert "secret_key_meets_minimum: yes" in report


def test_auth_trust_posture_reports_production_secret_warning(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "staging")
    monkeypatch.delenv("ELBYSODIC_DEMO_MODE", raising=False)
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "tiny-secret-value")

    posture = auth_trust_posture()
    report = format_auth_trust_posture(posture)

    assert posture.production is True
    assert posture.demo_mode_enabled is False
    assert posture.seed_passwords_enabled is False
    assert posture.secret_key_configured is True
    assert posture.secret_key_meets_minimum is False
    assert posture.development_identity_allowed is False
    assert posture.session_required_for_app_routes is True
    assert seed_passwords_enabled() is False
    assert posture.warnings == ("production secret key is missing or too short",)
    assert "tiny-secret-value" not in report
    assert "secret_key_meets_minimum: no" in report


def test_auth_trust_posture_reports_development_shortcuts(monkeypatch) -> None:
    monkeypatch.delenv("ELBYSODIC_ENV", raising=False)
    monkeypatch.delenv("ELBYSODIC_DEMO_MODE", raising=False)
    monkeypatch.delenv("ELBYSODIC_SECRET_KEY", raising=False)

    posture = auth_trust_posture()

    assert posture.environment == "development"
    assert posture.production is False
    assert posture.seed_passwords_enabled is True
    assert posture.development_identity_allowed is True
    assert posture.session_required_for_app_routes is False
    assert posture.warnings == ("development identity shortcuts are enabled",)
