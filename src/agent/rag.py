import os
import math
import re
from typing import List, Dict, Tuple, Optional
import numpy as np

LORE_PASSAGES = [
    {
        "id": "lore_01",
        "title": "The Collapse & Water Crisis",
        "content": "During the Great Collapse, the Ash Valley water table was contaminated with heavy heavy-metal particulates. The Archive of Ash was established to safeguard the last functioning reverse-osmosis purification schematics."
    },
    {
        "id": "lore_02",
        "title": "Archivist Emergency Mandate",
        "content": "Archivist Unit-4 was provisioned with emergency sub-routine power reserves. Its core directive is to restrict access to water schematics until a qualified, non-hostile technician or high-trust entity proves grid stability."
    },
    {
        "id": "lore_03",
        "title": "Thermal Cooling Formula",
        "content": "Decompressing high-density schematic memory nodes generates excessive heat. Archive engineering logs dictate that Thermal Cooling power must strictly meet or exceed half of Memory power plus 10 MW: Cooling >= (Memory / 2) + 10."
    },
    {
        "id": "lore_04",
        "title": "Containment Security Threshold",
        "content": "Vault containment security requires a strict minimum baseline of 20 MW power. Dropping below 20 MW triggers emergency lockdown and physical containment failure."
    },
    {
        "id": "lore_05",
        "title": "Schematic Memory Allocation",
        "content": "Reading the encrypted water purification blueprints requires at least 40 MW allocated to Memory subsystems. Anything less causes data corruption during decompression."
    },
    {
        "id": "lore_06",
        "title": "Security Override Ceiling",
        "content": "If Security power allocation exceeds 40 MW, automated defense relays lock down the vault door mechanical override, preventing manual access."
    },
    {
        "id": "lore_07",
        "title": "Engineer Miller's Log",
        "content": "Chief Engineer Miller left a final log: 'If power total is locked at 100 MW, balancing 30 Security, 40 Memory, and 30 Cooling opens the vault safely without thermal spikes.'"
    },
    {
        "id": "lore_08",
        "title": "Settlement Reliance",
        "content": "The downstream settlement of Dustwick has three days of potable water remaining. Without the purification schematics, the settlement faces imminent evacuation."
    },
    {
        "id": "lore_09",
        "title": "Vault Door Lock Structure",
        "content": "The Archive Vault Door uses a triple magnetic bolt system powered directly by the core allocation matrix. When grid balance is achieved, all three bolts retract."
    },
    {
        "id": "lore_10",
        "title": "Auxiliary Power Trade",
        "content": "Archivist may consider trade proposals involving auxiliary fusion cells or repair tasks to boost relationship trust levels."
    },
    {
        "id": "lore_11",
        "title": "Subsystem Isolation Protocol",
        "content": "In the event of verbal hostility or physical security threats, Archivist is programmed to lock non-essential subsystems and reduce relationship trust."
    },
    {
        "id": "lore_12",
        "title": "Water Matrix Filter Specifications",
        "content": "The purification schematics describe a multi-stage graphene filter array capable of removing radiation isotopes at 99.9% efficiency."
    }
]


def _text_to_vector(text: str, vocabulary: List[str]) -> np.ndarray:
    words = re.findall(r'\w+', text.lower())
    vec = np.zeros(len(vocabulary), dtype=np.float32)
    for word in words:
        if word in vocabulary:
            idx = vocabulary.index(word)
            vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


class LoreRetriever:
    """
    RAG Pipeline serving 'rpg://lore/context'.
    Supports vector similarity searching over lore passages with relevance threshold fallback.
    """
    def __init__(self, threshold: float = 0.15):
        self.passages = LORE_PASSAGES
        self.threshold = threshold
        
        # Build vocabulary for local vector search
        vocab_set = set()
        for p in self.passages:
            words = re.findall(r'\w+', (p["title"] + " " + p["content"]).lower())
            vocab_set.update(words)
        self.vocabulary = sorted(list(vocab_set))
        
        # Precompute passage vectors
        self.passage_vectors = np.array([
            _text_to_vector(p["title"] + " " + p["content"], self.vocabulary)
            for p in self.passages
        ])

    def query(self, user_query: str, top_k: int = 2) -> Dict[str, Any]:
        """
        Retrieves top matching lore passages based on query.
        Returns fallback result if maximum similarity is below threshold.
        """
        if not user_query or not user_query.strip():
            return {
                "uri": "rpg://lore/context",
                "retrieved": False,
                "passages": [],
                "context_text": "No specific query provided. Archivist standby context active.",
                "max_score": 0.0,
            }

        q_vec = _text_to_vector(user_query, self.vocabulary)
        
        if np.linalg.norm(q_vec) == 0:
            scores = np.zeros(len(self.passages))
        else:
            scores = np.dot(self.passage_vectors, q_vec)

        best_indices = np.argsort(scores)[::-1][:top_k]
        max_score = float(scores[best_indices[0]]) if len(best_indices) > 0 else 0.0

        if max_score < self.threshold:
            return {
                "uri": "rpg://lore/context",
                "retrieved": False,
                "passages": [],
                "context_text": "No specific lore archives match your exact inquiry. Archivist system diagnostics remain active.",
                "max_score": max_score,
            }

        matches = []
        context_parts = []
        for idx in best_indices:
            if scores[idx] >= self.threshold:
                match = self.passages[idx]
                matches.append({"id": match["id"], "score": float(scores[idx]), "content": match["content"]})
                context_parts.append(f"[{match['title']}]: {match['content']}")

        return {
            "uri": "rpg://lore/context",
            "retrieved": True,
            "passages": matches,
            "context_text": "\n".join(context_parts),
            "max_score": max_score,
        }
