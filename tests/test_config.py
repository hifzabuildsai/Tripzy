import pytest

from app import config
from app import server


def test_local_cors_origins_default_to_nextjs(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    assert config.get_cors_origins() == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_production_cors_has_no_local_fallback(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv("APP_ENV", "production")

    assert config.get_cors_origins() == []


def test_api_docs_are_disabled_only_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    assert config.get_api_docs_urls() == {
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }

    monkeypatch.setenv("APP_ENV", "production")
    assert config.get_api_docs_urls() == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }


@pytest.mark.parametrize("value", ["0", "-1", "not-a-number"])
def test_public_demo_integer_settings_must_be_positive(
    monkeypatch,
    value: str,
) -> None:
    monkeypatch.setenv("MAX_REQUEST_BODY_BYTES", value)

    with pytest.raises(RuntimeError, match="MAX_REQUEST_BODY_BYTES"):
        config.get_positive_int("MAX_REQUEST_BODY_BYTES", 16_384)


@pytest.mark.parametrize(
    "value",
    ["0", "-0.1", "not-a-number", "nan", "inf"],
)
def test_public_demo_timeout_settings_must_be_positive(
    monkeypatch,
    value: str,
) -> None:
    monkeypatch.setenv("PLANNING_TIMEOUT_SECONDS", value)

    with pytest.raises(RuntimeError, match="PLANNING_TIMEOUT_SECONDS"):
        config.get_positive_float("PLANNING_TIMEOUT_SECONDS", 240.0)


def test_production_environment_requires_backend_contract(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")

    for variable in config.PRODUCTION_REQUIRED_ENV_VARS:
        monkeypatch.delenv(variable, raising=False)

    with pytest.raises(RuntimeError) as error:
        config.validate_production_environment()

    for variable in config.PRODUCTION_REQUIRED_ENV_VARS:
        assert variable in str(error.value)


def test_production_environment_accepts_exact_frontend_origin(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")

    values = {
        "GEMINI_API_KEY": "placeholder",
        "TAVILY_API_KEY": "placeholder",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "placeholder",
        "CORS_ORIGINS": "https://tripzy.example",
    }

    for variable, value in values.items():
        monkeypatch.setenv(variable, value)

    config.validate_production_environment()


def test_server_honors_port_and_binds_all_interfaces(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PORT", "4321")
    monkeypatch.setattr(server, "DEBUG", False)
    monkeypatch.setattr(
        server.uvicorn,
        "run",
        lambda application, **options: calls.append((application, options)),
    )

    server.main()

    assert calls == [
        (
            "app.api:app",
            {
                "host": "0.0.0.0",
                "port": 4321,
                "proxy_headers": True,
                "access_log": False,
                "log_level": "info",
            },
        )
    ]


@pytest.mark.parametrize("port", ["not-a-number", "0", "65536"])
def test_server_rejects_invalid_port(monkeypatch, port: str) -> None:
    monkeypatch.setenv("PORT", port)

    with pytest.raises(RuntimeError, match="PORT"):
        server.get_port()
