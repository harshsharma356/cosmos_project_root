import threading
import webbrowser
import http.server
import socketserver
import time
import random
from pathlib import Path

from agent.observe import Observer
from agent.reason import Reasoner
from agent.decide import Decider
from agent.act import Actor
from agent.memory import Memory
from agent.llm_client import OllamaClient

# -----------------------------
# Config
# -----------------------------
UI_PORT = 8000
RUN_INTERVAL = 5


# -----------------------------
# UI Server
# -----------------------------
def start_ui_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", UI_PORT), handler) as httpd:
        print(f"🌐 UI running at http://localhost:{UI_PORT}/ui")
        httpd.serve_forever()


def open_browser():
    time.sleep(1)
    webbrowser.open(f"http://localhost:{UI_PORT}/ui")


# -----------------------------
# Scenario Generators (MEANINGFUL)
# -----------------------------
def scenario_checkout_failure():
    return {
        "tickets": [{"id": i} for i in range(25)],
        "errors": [
            {"type": "checkout_timeout", "service": "checkout"}
            for _ in range(10)
        ],
        "checkouts": [{"status": "failed"} for _ in range(8)],
        "webhooks": [],
        "migration_states": [{"stage": "post-cutover"}],
    }


def scenario_webhook_failure():
    return {
        "tickets": [{"id": i} for i in range(15)],
        "errors": [
            {"type": "webhook_401", "service": "webhook"}
            for _ in range(6)
        ],
        "checkouts": [{"status": "success"} for _ in range(20)],
        "webhooks": [{"status": "failed"} for _ in range(6)],
        "migration_states": [{"stage": "post-cutover"}],
    }


def scenario_frontend_mismatch():
    return {
        "tickets": [{"id": i} for i in range(10)],
        "errors": [
            {"type": "frontend_state_mismatch", "service": "frontend"}
            for _ in range(5)
        ],
        "checkouts": [{"status": "success"} for _ in range(15)],
        "webhooks": [],
        "migration_states": [{"stage": "stable"}],
    }


def scenario_healthy_system():
    return {
        "tickets": [{"id": 1}, {"id": 2}],
        "errors": [],
        "checkouts": [{"status": "success"} for _ in range(30)],
        "webhooks": [],
        "migration_states": [{"stage": "stable"}],
    }


SCENARIOS = [
    scenario_checkout_failure,
    scenario_webhook_failure,
    scenario_frontend_mismatch,
    scenario_healthy_system,
]


# -----------------------------
# Agent Runner
# -----------------------------
class AgentRunner:
    def __init__(self):
        self.observer = Observer()
        self.reasoner = Reasoner(OllamaClient())
        self.decider = Decider()
        self.actor = Actor()
        self.memory = Memory()

    def run_once(self, raw_signals: dict):
        observation = self.observer.observe(raw_signals)
        reasoning = self.reasoner.reason(observation)
        decision = self.decider.decide(observation, reasoning)
        action = self.actor.act(decision)

        return self.memory.record_incident(
            observation=observation,
            reasoning=reasoning,
            decision=decision,
            action=action,
        )


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":

    threading.Thread(target=start_ui_server, daemon=True).start()
    threading.Thread(target=open_browser, daemon=True).start()

    agent = AgentRunner()

    print("🚀 Agent running with live UI and real scenario variation...")

    while True:
        scenario_fn = random.choice(SCENARIOS)
        raw_signals = scenario_fn()

        incident_id = agent.run_once(raw_signals)

        print("✅ Agent run complete")
        print("Incident ID:", incident_id)
        print("Scenario:", scenario_fn.__name__)
        print("-" * 50)

        time.sleep(RUN_INTERVAL)
