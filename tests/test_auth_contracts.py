from __future__ import annotations

from elbysodic.services.auth import (
    SESSION_COOKIE,
    AuthTrustDiagnostic,
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
    demo_diagnostic = _diagnostic(posture.diagnostics, "auth.demo_mode.seed_passwords")
    assert demo_diagnostic.severity == "warning"
    assert demo_diagnostic.surface == "demo login"
    assert demo_diagnostic.production_blocking is True
    assert demo_diagnostic.local_development_exception is False
    assert "Unset ELBYSODIC_DEMO_MODE" in demo_diagnostic.recommended_fix
    assert "super-secret-production-key-value" not in report
    assert "secret_key_configured: yes" in report
    assert "secret_key_meets_minimum: yes" in report
    assert "[auth.demo_mode.seed_passwords] warning" in report
    assert "production_blocking: yes" in report


def test_auth_trust_posture_allows_staging_demo_rehearsal_without_launch_blocker(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "staging")
    monkeypatch.setenv("ELBYSODIC_DEMO_MODE", "1")
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "staging-demo-secret-value-123456")

    posture = auth_trust_posture()
    report = format_auth_trust_posture(posture)

    assert posture.production is True
    assert posture.environment == "staging"
    assert posture.demo_mode_enabled is True
    assert posture.seed_passwords_enabled is True
    assert posture.secret_key_meets_minimum is True
    assert posture.session_required_for_app_routes is True
    demo_diagnostic = _diagnostic(posture.diagnostics, "auth.demo_mode.seed_passwords")
    assert demo_diagnostic.severity == "warning"
    assert demo_diagnostic.production_blocking is False
    assert demo_diagnostic.local_development_exception is True
    assert "staging or seeded demo rehearsals" in demo_diagnostic.recommended_fix
    assert "staging-demo-secret-value-123456" not in report
    assert "[auth.demo_mode.seed_passwords] warning" in report
    assert "production_blocking: no" in report


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
    secret_diagnostic = _diagnostic(posture.diagnostics, "auth.secret_key.too_short")
    assert secret_diagnostic.severity == "blocker"
    assert secret_diagnostic.surface == "session secret"
    assert secret_diagnostic.production_blocking is True
    assert "32 characters" in secret_diagnostic.recommended_fix
    assert "tiny-secret-value" not in report
    assert "secret_key_meets_minimum: no" in report
    assert "[auth.secret_key.too_short] blocker" in report


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
    dev_diagnostic = _diagnostic(posture.diagnostics, "auth.development_identity.shortcuts")
    assert dev_diagnostic.severity == "note"
    assert dev_diagnostic.surface == "local identity"
    assert dev_diagnostic.production_blocking is False
    assert dev_diagnostic.local_development_exception is True
    assert "local development" in dev_diagnostic.recommended_fix


def test_auth_trust_posture_diagnostics_cover_remediation_surfaces(monkeypatch) -> None:
    monkeypatch.setenv("ELBYSODIC_ENV", "production")
    monkeypatch.delenv("ELBYSODIC_DEMO_MODE", raising=False)
    monkeypatch.setenv("ELBYSODIC_SECRET_KEY", "x" * 32)

    posture = auth_trust_posture()
    diagnostics = {diagnostic.code: diagnostic for diagnostic in posture.diagnostics}

    assert {
        "auth.secret_key.configured",
        "auth.secure_cookies.expected",
        "auth.csrf.configured",
        "auth.forwarded_headers.not_trusted",
        "auth.invite_only.entry",
        "auth.deployment_environment",
    }.issubset(diagnostics)
    assert diagnostics["auth.secure_cookies.expected"].surface == "session cookie"
    assert "Secure, HttpOnly, and SameSite=Lax" in (
        diagnostics["auth.secure_cookies.expected"].recommended_fix
    )
    assert diagnostics["auth.csrf.configured"].surface == "mutating forms"
    assert "csrf_field()" in diagnostics["auth.csrf.configured"].recommended_fix
    assert diagnostics["auth.forwarded_headers.not_trusted"].surface == "request origin"
    assert "security tests" in diagnostics["auth.forwarded_headers.not_trusted"].recommended_fix
    assert diagnostics["auth.invite_only.entry"].surface == "writer entry"
    assert "request-access and invitation" in diagnostics["auth.invite_only.entry"].recommended_fix
    assert all("x" * 32 not in diagnostic.recommended_fix for diagnostic in diagnostics.values())


def _diagnostic(
    diagnostics: tuple[AuthTrustDiagnostic, ...],
    code: str,
) -> AuthTrustDiagnostic:
    return next(diagnostic for diagnostic in diagnostics if diagnostic.code == code)
