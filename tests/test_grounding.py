from app.agents.tools import ClinicalAssistantOrchestrator
import app.rag.orchestrator as orchestrator


def test_assistant_fallback_is_grounded(monkeypatch):
    monkeypatch.setattr(orchestrator, "has_llm_credentials", lambda: False)
    response = ClinicalAssistantOrchestrator().run("p001", "What care gaps exist for this patient?")
    assert response.model_status == "fallback"
    assert response.audit.grounded is True
    assert response.supporting_evidence
    assert response.audit.retrieval_strategy == "hybrid"
