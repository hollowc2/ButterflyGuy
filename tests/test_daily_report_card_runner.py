from __future__ import annotations

from tools.send_daily_report_card import load_report_gateway_settings


def test_report_gateway_settings_load_host_values_from_infra_env(tmp_path) -> None:
    infra_env = tmp_path / ".env"
    infra_env.write_text(
        "\n".join(
            (
                "SCHWAB_ACCESS_MODE_REPORT=gateway",
                "SCHWAB_GATEWAY_REPORT_URL=http://127.0.0.1:8011",
                "SCHWAB_GATEWAY_URL=http://schwab-gateway:8011",
                "SCHWAB_GATEWAY_API_KEY=report-test-key",
            )
        ),
        encoding="utf-8",
    )

    settings = load_report_gateway_settings(
        infra_env_path=infra_env,
        process_env={},
    )

    assert settings.access_mode == "gateway"
    assert settings.gateway_url == "http://127.0.0.1:8011"
    assert settings.gateway_api_key.get_secret_value() == "report-test-key"
    assert "report-test-key" not in repr(settings)


def test_report_gateway_process_values_override_infra_env(tmp_path) -> None:
    infra_env = tmp_path / ".env"
    infra_env.write_text(
        "SCHWAB_ACCESS_MODE_REPORT=direct\n"
        "SCHWAB_GATEWAY_API_KEY=infra-key\n",
        encoding="utf-8",
    )

    settings = load_report_gateway_settings(
        infra_env_path=infra_env,
        process_env={
            "SCHWAB_ACCESS_MODE_REPORT": "gateway",
            "SCHWAB_GATEWAY_REPORT_URL": "http://localhost:18011",
            "SCHWAB_GATEWAY_API_KEY": "process-key",
        },
    )

    assert settings.access_mode == "gateway"
    assert settings.gateway_url == "http://localhost:18011"
    assert settings.gateway_api_key.get_secret_value() == "process-key"
