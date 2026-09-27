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
            },
        )
    ]


@pytest.mark.parametrize("port", ["not-a-number", "0", "65536"])
def test_server_rejects_invalid_port(monkeypatch, port: str) -> None:
    monkeypatch.setenv("PORT", port)

    with pytest.raises(RuntimeError, match="PORT"):
        server.get_port()
