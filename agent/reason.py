import os
import json
from typing import Dict, Any


class Reasoner:
    """
    Hybrid reasoner for the agent.

    - Deterministic reasoning for clear cases
    - LLM reasoning for ambiguous or mixed cases

    LLM is ENABLED BY DEFAULT.
    Disable with:
        USE_LLM=false
    """

    def __init__(self, llm=None):
        self.llm = llm

    # ==================================================
    # ENTRY POINT
    # ==================================================
    def reason(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        use_llm_env = os.getenv("USE_LLM", "true").lower() == "true"

        if self.llm and use_llm_env and self._should_use_llm(observation):
            print("🧠 LLM reasoning enabled")
            return self._reason_with_llm(observation)

        print("⚡ Deterministic reasoning")
        return self._reason_deterministic(observation)

    # ==================================================
    # LLM ESCALATION LOGIC
    # ==================================================
    def _should_use_llm(self, observation: Dict[str, Any]) -> bool:
        confidence = observation.get("confidence", 1.0)
        anomalies = observation.get("anomalies", [])

        if confidence < 0.85:
            return True

        if len(anomalies) >= 2:
            return True

        return False

    # ==================================================
    # SAFE STRING NORMALIZER
    # ==================================================
    def _stringify(self, value) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return (
                value.get("description")
                or value.get("explanation")
                or value.get("justification")
                or json.dumps(value)
            )
        return str(value)

    # ==================================================
    # LLM REASONING (HARDENED)
    # ==================================================
    def _reason_with_llm(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        print("🧠 ACTUALLY CALLING OLLAMA")

        try:
            prompt = self._build_prompt(observation)
            response = self.llm.generate(prompt)

            # -------- Normalize confidence --------
            confidence = response.get("confidence", 0.5)
            if not isinstance(confidence, (int, float)):
                confidence = 0.5

            # -------- Normalize hypotheses --------
            hypotheses = []
            raw_hypotheses = response.get("hypotheses", [])

            if isinstance(raw_hypotheses, list):
                for h in raw_hypotheses:
                    if isinstance(h, dict):
                        hypotheses.append({
                            "cause": h.get("cause", "unknown"),
                            "explanation": h.get("explanation", ""),
                            "confidence": float(h.get("confidence", confidence)),
                        })
                    elif isinstance(h, str):
                        hypotheses.append({
                            "cause": h,
                            "explanation": "",
                            "confidence": confidence,
                        })

            if not hypotheses:
                hypotheses.append({
                    "cause": "unknown",
                    "explanation": "LLM did not return a valid hypothesis",
                    "confidence": 0.4,
                })

            return {
                "reasoning_mode": "llm",
                "hypotheses": hypotheses,
                "assumptions": [
                    self._stringify(a)
                    for a in response.get("assumptions", [])
                ],
                "unknowns": [
                    self._stringify(u)
                    for u in response.get("unknowns", [])
                ],
                "confidence": confidence,
            }

        except Exception as e:
            print("❌ LLM FAILURE:", e)
            return {
                "reasoning_mode": "llm_failed",
                "hypotheses": [{
                    "cause": "unknown",
                    "explanation": "LLM failed or returned malformed output",
                    "confidence": 0.4,
                }],
                "assumptions": [],
                "unknowns": ["LLM reasoning failed"],
                "confidence": 0.4,
                "error": str(e),
            }

    # ==================================================
    # DETERMINISTIC REASONING (UNCHANGED, GOOD)
    # ==================================================
    def _reason_deterministic(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        stats = observation.get("stats", {})
        error_types = stats.get("error_types", {})

        hypotheses = []

        if stats.get("failed_checkouts", 0) >= 5:
            hypotheses.append({
                "cause": "migration_misconfiguration",
                "explanation": "High number of checkout failures detected after migration",
                "confidence": 0.8,
            })

        if error_types.get("webhook_401", 0) >= 3:
            hypotheses.append({
                "cause": "webhook_auth_failure",
                "explanation": "Repeated webhook authentication failures detected",
                "confidence": 0.7,
            })

        if error_types.get("frontend_state_mismatch", 0) >= 3:
            hypotheses.append({
                "cause": "frontend_backend_mismatch",
                "explanation": "Frontend and backend states are inconsistent",
                "confidence": 0.65,
            })

        if error_types.get("unknown", 0) >= 10:
            hypotheses.append({
                "cause": "platform_regression",
                "explanation": "High volume of unknown errors suggests a platform regression",
                "confidence": 0.6,
            })

        if not hypotheses:
            hypotheses.append({
                "cause": "normal_operation",
                "explanation": "System signals are within expected parameters",
                "confidence": 0.9,
            })

        return {
            "reasoning_mode": "deterministic",
            "hypotheses": hypotheses,
            "assumptions": [
                "Observed signals accurately reflect system behavior"
            ],
            "unknowns": [
                "Merchant-specific configurations not visible"
            ],
            "confidence": max(h["confidence"] for h in hypotheses),
        }

    # ==================================================
    # PROMPT BUILDER (STRICT CONTRACT)
    # ==================================================
    def _build_prompt(self, observation: Dict[str, Any]) -> str:
        stats = observation.get("stats", {})
        anomalies = observation.get("anomalies", [])

        return f"""
You are an automated incident analysis system.

STRICT RULES:
- Return VALID JSON ONLY
- Do NOT add nested objects
- Do NOT add justification fields
- Follow the schema EXACTLY

SCHEMA:
{{
  "hypotheses": [
    {{
      "cause": "<snake_case_string>",
      "explanation": "<short string>",
      "confidence": <number between 0 and 1>
    }}
  ],
  "assumptions": ["<string>"],
  "unknowns": ["<string>"],
  "confidence": <number between 0 and 1>
}}

DATA:
Stats: {stats}
Anomalies: {anomalies}

Return JSON ONLY.
""".strip()
