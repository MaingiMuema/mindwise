from app.services.llm import LLMRegistry


def test_provider_registry_falls_back_to_heuristic(monkeypatch):
    monkeypatch.setenv("LLM_PRIMARY_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    registry = LLMRegistry()
    provider = registry.choose()

    assert provider.name == "heuristic"
