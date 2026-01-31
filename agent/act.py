import json
import time
from typing import Dict, Any, List
from pathlib import Path


STATE_FILE = Path("agent_state.json")


class Actor:
    """
    Executes approved decisions in a safe, auditable way.
    """

    def act(self, decision_output: Dict[str, Any]) -> Dict[str, Any]:
        actions_taken = []
        pending_approvals = []

        for decision in decision_output.get("decisions", []):
            if decision.get("requires_human_approval"):
                pending_approvals.append(decision)
                continue

            action = self._execute(decision)
            if action:
                actions_taken.append(action)

        state_update = {
            "timestamp": time.time(),
            "observation_id": decision_output["observation_id"],
            "actions_taken": actions_taken,
            "pending_approvals": pending_approvals,
            "risk_level": decision_output.get("risk_level")
        }

        self._write_state(state_update)
        return state_update

    # -----------------------
    # Execution dispatcher
    # -----------------------

    def _execute(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        action_type = decision.get("type")

        if action_type == "monitor_only":
            return self._monitor(decision)

        if action_type == "support_guidance":
            return self._support_guidance(decision)

        if action_type == "escalate_engineering":
            return self._escalate_engineering(decision)

        # Unknown or blocked action
        return None

    # -----------------------
    # Action implementations
    # -----------------------

    def _monitor(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "action": "monitoring",
            "note": decision.get("reason")
        }

    def _support_guidance(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "action": "support_guidance_prepared",
            "message": (
                "Provide merchant with migration checklist, "
                "webhook verification steps, and API credential validation."
            ),
            "reason": decision.get("reason")
        }

    def _escalate_engineering(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "action": "engineering_escalation_created",
            "severity": decision.get("severity"),
            "summary": (
                "Potential platform regression detected during headless migration."
            )
        }

    # -----------------------
    # State persistence
    # -----------------------

    def _write_state(self, update: Dict[str, Any]) -> None:
        existing = []

        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                try:
                    existing = json.load(f)
                except json.JSONDecodeError:
                    existing = []

        existing.append(update)

        with open(STATE_FILE, "w") as f:
            json.dump(existing, f, indent=2)
