from typing import Dict, Any, List


class Decider:
    """
    Applies policy rules to hypotheses and observations
    to determine allowed actions.

    PURE POLICY LAYER.
    """

    def decide(
        self,
        observation: Dict[str, Any],
        reasoning: Dict[str, Any]
    ) -> Dict[str, Any]:

        hypotheses = reasoning.get("hypotheses", [])
        overall_confidence = reasoning.get("confidence", 0.5)

        decisions = []
        top_hypothesis = self._get_top_hypothesis(hypotheses)

        cause = top_hypothesis.get("cause", "unknown")

        # ----------------------------
        # SAFETY GATES
        # ----------------------------
        if observation["confidence"] < 0.6:
            return self._block(
                "Low observation confidence",
                observation,
                reasoning
            )

        # ----------------------------
        # POLICY BY CAUSE (KEY FIX)
        # ----------------------------

        # 🔴 Platform regression → immediate escalation
        if cause == "platform_regression":
            decisions.append(
                self._escalate_engineering(
                    severity="high",
                    reason="Suspected platform regression across services",
                    requires_human_approval=False
                )
            )

        # 🟠 Webhook auth failure → support guidance
        elif cause == "webhook_auth_failure":
            decisions.append(
                self._support_guidance(
                    reason="Webhook authentication failures detected",
                    requires_human_approval=False
                )
            )

        # 🟡 Frontend/backend mismatch → documentation + monitoring
        elif cause == "frontend_backend_mismatch":
            decisions.append(
                self._documentation_update(
                    reason="Frontend and backend state mismatch observed",
                )
            )
            decisions.append(
                self._monitor_only(
                    "Mismatch may resolve after configuration sync"
                )
            )

        # 🟢 Migration misconfiguration → guided support
        elif cause == "migration_misconfiguration":
            decisions.append(
                self._support_guidance(
                    reason="Likely merchant-side migration misconfiguration",
                    requires_human_approval=False
                )
            )

        # 🟢 Normal operation → no action
        elif cause == "normal_operation":
            decisions.append(
                self._monitor_only(
                    "System operating normally"
                )
            )

        # ⚪ Unknown → cautious monitoring
        else:
            decisions.append(
                self._monitor_only(
                    "Root cause unclear, monitoring for changes"
                )
            )

        return self._finalize(decisions, observation, reasoning)

    # ------------------------------------------------
    # HELPERS
    # ------------------------------------------------

    def _get_top_hypothesis(self, hypotheses: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not hypotheses:
            return {"cause": "unknown", "confidence": 0.0}
        return max(hypotheses, key=lambda h: h.get("confidence", 0))

    def _finalize(
        self,
        decisions: List[Dict[str, Any]],
        observation: Dict[str, Any],
        reasoning: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {
            "observation_id": observation["observation_id"],
            "decisions": decisions,
            "risk_level": self._assess_risk(decisions),
            "trace": {
                "observation_confidence": observation["confidence"],
                "reasoning_confidence": reasoning["confidence"]
            }
        }

    def _assess_risk(self, decisions: List[Dict[str, Any]]) -> str:
        if any(d["type"] == "escalate_engineering" for d in decisions):
            return "high"
        if any(d.get("requires_human_approval") for d in decisions):
            return "medium"
        return "low"

    # ------------------------------------------------
    # DECISION CONSTRUCTORS
    # ------------------------------------------------

    def _monitor_only(self, reason: str) -> Dict[str, Any]:
        return {
            "type": "monitor_only",
            "reason": reason,
            "requires_human_approval": False
        }

    def _support_guidance(
        self,
        reason: str,
        requires_human_approval: bool
    ) -> Dict[str, Any]:
        return {
            "type": "support_guidance",
            "reason": reason,
            "requires_human_approval": requires_human_approval
        }

    def _escalate_engineering(
        self,
        severity: str,
        reason: str,
        requires_human_approval: bool
    ) -> Dict[str, Any]:
        return {
            "type": "escalate_engineering",
            "severity": severity,
            "reason": reason,
            "requires_human_approval": requires_human_approval
        }

    def _documentation_update(self, reason: str) -> Dict[str, Any]:
        return {
            "type": "documentation_update_suggestion",
            "reason": reason,
            "requires_human_approval": True
        }

    def _block(
        self,
        reason: str,
        observation: Dict[str, Any],
        reasoning: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "observation_id": observation["observation_id"],
            "decisions": [{
                "type": "block_auto_actions",
                "reason": reason,
                "requires_human_approval": True
            }],
            "risk_level": "high",
            "trace": {
                "observation_confidence": observation["confidence"],
                "reasoning_confidence": reasoning["confidence"]
            }
        }
