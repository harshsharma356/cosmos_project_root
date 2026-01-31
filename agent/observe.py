import json
import time
from collections import defaultdict
from typing import Dict, Any, List


class Observer:
    """
    Observer is responsible for collecting raw signals from the system
    and converting them into a normalized observation snapshot.

    It does NOT interpret, judge, or decide.
    """

    def __init__(self):
        self.observation_id = 0

    def observe(self, raw_signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main observe loop entrypoint.
        Takes raw system signals and produces a structured observation.
        """

        self.observation_id += 1

        observation = {
            "observation_id": self.observation_id,
            "timestamp": time.time(),
            "signals": {},
            "stats": {},
            "anomalies": [],
            "confidence": 1.0
        }

        # 1. Ingest raw signals
        observation["signals"] = self._ingest_signals(raw_signals)

        # 2. Compute lightweight statistics (NOT conclusions)
        observation["stats"] = self._compute_stats(observation["signals"])

        # 3. Detect surface-level anomalies (counts, spikes only)
        observation["anomalies"] = self._detect_anomalies(
            observation["signals"],
            observation["stats"]
        )

        # 4. Adjust confidence if data is incomplete or noisy
        observation["confidence"] = self._estimate_confidence(
            observation["signals"]
        )

        return observation

    # -------------------------
    # Internal helper methods
    # -------------------------

    def _ingest_signals(self, raw_signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize incoming signals into predictable buckets.
        """

        return {
            "tickets": raw_signals.get("tickets", []),
            "errors": raw_signals.get("errors", []),
            "checkouts": raw_signals.get("checkouts", []),
            "webhooks": raw_signals.get("webhooks", []),
            "migration_states": raw_signals.get("migration_states", [])
        }

    def _compute_stats(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute simple counts and frequencies.
        No inference.
        """

        stats = {}

        stats["ticket_count"] = len(signals["tickets"])
        stats["error_count"] = len(signals["errors"])
        stats["failed_checkouts"] = sum(
            1 for c in signals["checkouts"] if c.get("status") == "failed"
        )

        # Count error types
        error_types = defaultdict(int)
        for error in signals["errors"]:
            error_types[error.get("type", "unknown")] += 1
        stats["error_types"] = dict(error_types)

        # Count migration stages
        migration_stage_counts = defaultdict(int)
        for m in signals["migration_states"]:
            migration_stage_counts[m.get("stage", "unknown")] += 1
        stats["migration_stage_distribution"] = dict(migration_stage_counts)

        return stats

    def _detect_anomalies(
        self,
        signals: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect obvious anomalies without reasoning about cause.
        """

        anomalies = []

        if stats["failed_checkouts"] > 0:
            anomalies.append({
                "type": "checkout_failures",
                "count": stats["failed_checkouts"],
                "severity": "high"
            })

        for error_type, count in stats["error_types"].items():
            if count >= 5:
                anomalies.append({
                    "type": "repeated_error",
                    "error_type": error_type,
                    "count": count,
                    "severity": "medium"
                })

        return anomalies

    def _estimate_confidence(self, signals: Dict[str, Any]) -> float:
        """
        Reduce confidence if signal coverage is sparse.
        """

        missing_sources = 0

        for key, value in signals.items():
            if not value:
                missing_sources += 1

        confidence = 1.0 - (missing_sources * 0.1)
        return max(confidence, 0.5)
