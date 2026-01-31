import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MERCHANTS = ["M1", "M2", "M3", "M4", "M5", "M6"]

ERROR_TYPES = [
    "webhook_401",
    "checkout_timeout",
    "api_200_inconsistent",
    "frontend_state_mismatch"
]

TICKET_MESSAGES = [
    "Checkout fails only on mobile after headless migration",
    "Orders succeed but webhook not firing for some merchants",
    "Payments captured but frontend shows failure",
    "API returns 200 but data not reflected in dashboard",
    "Worked before migration, now intermittently broken",
    "Some customers can checkout, others cannot",
]

SERVICES = ["checkout", "webhook", "api", "frontend"]

# -----------------------------
# SCENARIO DEFINITIONS
# -----------------------------
SCENARIOS = {
    "clear_misconfig": {
        "ticket_count": 15,
        "event_count": 20,
        "error_bias": ["checkout_timeout"],
        "service_bias": ["checkout"]
    },
    "webhook_failure": {
        "ticket_count": 10,
        "event_count": 15,
        "error_bias": ["webhook_401"],
        "service_bias": ["webhook"]
    },
    "conflicting_signals": {
        "ticket_count": 20,
        "event_count": 30,
        "error_bias": ERROR_TYPES,
        "service_bias": SERVICES
    },
    "low_signal_noise": {
        "ticket_count": 3,
        "event_count": 2,
        "error_bias": [],
        "service_bias": []
    }
}

# -----------------------------
# GENERATORS
# -----------------------------
def generate_tickets(n, error_bias):
    tickets = []
    for i in range(n):
        tickets.append({
            "ticket_id": f"T{i+1}",
            "merchant_id": random.choice(MERCHANTS),
            "issue": random.choice(error_bias or ERROR_TYPES),
            "message": random.choice(TICKET_MESSAGES),
            "timestamp": (
                datetime.utcnow() - timedelta(minutes=random.randint(0, 90))
            ).isoformat()
        })
    return tickets


def generate_events(n, error_bias, service_bias):
    events = []
    for i in range(n):
        events.append({
            "event_id": f"E{i+1}",
            "merchant_id": random.choice(MERCHANTS),
            "error_code": random.choice(error_bias or ERROR_TYPES),
            "service": random.choice(service_bias or SERVICES),
            "timestamp": (
                datetime.utcnow() - timedelta(minutes=random.randint(0, 90))
            ).isoformat()
        })
    return events


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    scenario = sys.argv[1] if len(sys.argv) > 1 else "conflicting_signals"

    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")

    cfg = SCENARIOS[scenario]

    tickets = generate_tickets(
        cfg["ticket_count"],
        cfg["error_bias"]
    )

    events = generate_events(
        cfg["event_count"],
        cfg["error_bias"],
        cfg["service_bias"]
    )

    save_json(DATA_DIR / "tickets.json", tickets)
    save_json(DATA_DIR / "events.json", events)

    print(f"✅ Generated data for scenario: {scenario}")
