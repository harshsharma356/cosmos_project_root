import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List


MEMORY_FILE = Path("agent_memory.json")


class Memory:
    """
    Append-only persistent memory for agent incidents.
    """

    def __init__(self):
        if not MEMORY_FILE.exists():
            MEMORY_FILE.write_text("[]")

    def record_incident(
        self,
        observation: Dict[str, Any],
        reasoning: Dict[str, Any],
        decision: Dict[str, Any],
        action: Dict[str, Any]
    ) -> str:
        """
        Store a complete incident snapshot.
        """

        incident = {
            "incident_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "observation": observation,
            "reasoning": reasoning,
            "decision": decision,
            "action": action,
            "outcome": None
        }

        memory = self._load()
        memory.append(incident)
        self._save(memory)

        return incident["incident_id"]

    def update_outcome(
        self,
        incident_id: str,
        outcome: Dict[str, Any]
    ) -> None:
        """
        Attach outcome feedback to an existing incident.
        """

        memory = self._load()

        for entry in memory:
            if entry["incident_id"] == incident_id:
                entry["outcome"] = {
                    "timestamp": time.time(),
                    **outcome
                }
                break

        self._save(memory)

    def query_similar(
        self,
        cause: str = None,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve past incidents matching a cause and confidence threshold.
        """

        memory = self._load()
        results = []

        for entry in memory:
            hypotheses = entry["reasoning"].get("hypotheses", [])
            for h in hypotheses:
                if cause and h.get("cause") != cause:
                    continue
                if h.get("confidence", 0) < min_confidence:
                    continue
                results.append(entry)
                break

        return results

    # -----------------------
    # Internal helpers
    # -----------------------

    def _load(self) -> List[Dict[str, Any]]:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)

    def _save(self, memory: List[Dict[str, Any]]) -> None:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
