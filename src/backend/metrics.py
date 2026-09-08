import time
from typing import List, Dict, Any


class PerformanceTracker:
    """
    Tracks turn-by-turn performance metrics against explicit latency and cost targets:
    - Target Voice Latency: < 2.0 seconds
    - Token usage tracking
    - Cost estimation
    """
    def __init__(self, target_latency_sec: float = 2.0):
        self.target_latency_sec = target_latency_sec
        self.turns: List[Dict[str, Any]] = []

    def record_turn(
        self,
        latency_sec: float,
        prompt_tokens: int,
        response_tokens: int,
        cost_usd: float,
        input_type: str = "text"
    ) -> Dict[str, Any]:
        turn_metric = {
            "turn_index": len(self.turns) + 1,
            "input_type": input_type,
            "latency_sec": round(latency_sec, 3),
            "target_latency_sec": self.target_latency_sec,
            "met_target": latency_sec <= self.target_latency_sec,
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": prompt_tokens + response_tokens,
            "cost_usd": round(cost_usd, 6),
        }
        self.turns.append(turn_metric)
        return turn_metric

    def get_summary(self) -> Dict[str, Any]:
        if not self.turns:
            return {
                "total_turns": 0,
                "avg_latency_sec": 0.0,
                "target_latency_sec": self.target_latency_sec,
                "target_compliance_rate": "100%",
                "total_tokens": 0,
                "total_cost_usd": 0.0,
            }

        avg_lat = sum(t["latency_sec"] for t in self.turns) / len(self.turns)
        met_count = sum(1 for t in self.turns if t["met_target"])
        total_tokens = sum(t["total_tokens"] for t in self.turns)
        total_cost = sum(t["cost_usd"] for t in self.turns)

        return {
            "total_turns": len(self.turns),
            "avg_latency_sec": round(avg_lat, 3),
            "target_latency_sec": self.target_latency_sec,
            "target_compliance_rate": f"{(met_count / len(self.turns)) * 100:.1f}%",
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
        }
