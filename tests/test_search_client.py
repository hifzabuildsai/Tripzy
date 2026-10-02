import json

import pytest

from app.tools import search_client


class FakeTavilyClient:
    calls = []

    def __init__(self, api_key=None):
        self.api_key = api_key

    def search(self, **kwargs):
        type(self).calls.append(kwargs)
        return {
            "results": [
                {
                    "title": "Fixture result",
                    "url": "https://example.com/result",
                    "content": "Example content",
                }
            ]
        }


def test_live_mode_calls_tavily(monkeypatch, tmp_path):
    FakeTavilyClient.calls = []
    monkeypatch.setenv("TRIPZY_SEARCH_MODE", "live")
    monkeypatch.setenv("TRIPZY_SEARCH_FIXTURE_DIR", str(tmp_path))
    monkeypatch.setattr(search_client, "TavilyClient", FakeTavilyClient)

    response = search_client.search(
        "flights Karachi Istanbul",
        search_depth="advanced",
        max_results=5,
    )

    assert response["results"][0]["title"] == "Fixture result"
    assert FakeTavilyClient.calls == [{
        "query": "flights Karachi Istanbul",
        "search_depth": "advanced",
        "max_results": 5,
    }]
    assert list(tmp_path.iterdir()) == []


def test_record_mode_writes_stable_fixture(monkeypatch, tmp_path):
    FakeTavilyClient.calls = []
    monkeypatch.setenv("TRIPZY_SEARCH_MODE", "record")
    monkeypatch.setenv("TRIPZY_SEARCH_FIXTURE_DIR", str(tmp_path))
    monkeypatch.setattr(search_client, "TavilyClient", FakeTavilyClient)

    params = {
        "search_depth": "basic",
        "max_results": 5,
    }
    response = search_client.search("travel Istanbul", **params)
    key = search_client.fixture_key("travel Istanbul", params)
    path = tmp_path / f"{key}.json"

    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["request"] == {
        "query": "travel Istanbul",
        "params": params,
    }
    assert payload["response"] == response


def test_replay_mode_reads_fixture_without_network(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIPZY_SEARCH_MODE", "replay")
    monkeypatch.setenv("TRIPZY_SEARCH_FIXTURE_DIR", str(tmp_path))

    params = {
        "search_depth": "basic",
        "max_results": 5,
    }
    key = search_client.fixture_key("travel Istanbul", params)
    expected = {"results": [{"title": "Recorded"}]}
    (tmp_path / f"{key}.json").write_text(
        json.dumps({
            "request": {
                "query": "travel Istanbul",
                "params": params,
            },
            "response": expected,
        }),
        encoding="utf-8",
    )

    class NetworkMustNotRun:
        def __init__(self, *args, **kwargs):
            raise AssertionError("replay must not instantiate Tavily")

    monkeypatch.setattr(search_client, "TavilyClient", NetworkMustNotRun)

    assert search_client.search("travel Istanbul", **params) == expected


def test_replay_missing_fixture_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("TRIPZY_SEARCH_MODE", "replay")
    monkeypatch.setenv("TRIPZY_SEARCH_FIXTURE_DIR", str(tmp_path))

    with pytest.raises(
        search_client.SearchReplayMissError,
        match="Replay fixture missing",
    ):
        search_client.search(
            "missing",
            search_depth="basic",
            max_results=5,
        )


def test_invalid_mode_is_rejected(monkeypatch):
    monkeypatch.setenv("TRIPZY_SEARCH_MODE", "surprise")

    with pytest.raises(RuntimeError, match="TRIPZY_SEARCH_MODE"):
        search_client.search("anything")
