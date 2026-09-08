import pytest
from src.agent.rag import LoreRetriever


def test_lore_retrieval_success():
    retriever = LoreRetriever(threshold=0.15)
    
    # Query related to water purification
    res = retriever.query("How do we purify the water in Ash Valley?")
    assert res["retrieved"]
    assert len(res["passages"]) > 0
    assert "water" in res["context_text"].lower() or "collapse" in res["context_text"].lower()

    # Query related to cooling
    res_cooling = retriever.query("What is the thermal cooling formula?")
    assert res_cooling["retrieved"]
    assert "cooling" in res_cooling["context_text"].lower()


def test_lore_retrieval_threshold_fallback():
    retriever = LoreRetriever(threshold=0.50)  # High threshold
    
    # Unrelated query
    res = retriever.query("xyz123 random nonsensical gibberish string")
    assert not res["retrieved"]
    assert "No specific lore archives match" in res["context_text"]
