COSMOS: Agentic AI for Self-Healing Support

COSMOS is an advanced Agentic AI system designed to manage the complexities of headless e-commerce migrations. It moves beyond simple automation to provide a "self-healing" support layer that observes system signals, reasons about root causes, and executes safe, explainable actions.

🚀 Core Concept: The ORDA Loop
The system operates on a continuous Observe-Reason-Decide-Act loop to ensure every action is grounded in data and safety:


Observe: Ingests raw signals (tickets, API logs, webhook failures) and detects anomalies.

Reason: Employs a Hybrid Reasoning engine. It uses deterministic rules for speed and escalates to a local LLM (Ollama) for ambiguous cases.


Decide: Applies strict policy logic and safety gates to determine the best course of action.


Act: Executes only whitelisted, low-risk actions or requests human approval for high-risk escalations.

📂 Project Structure
Root Directory
run_agent.py: The main orchestrator that runs the agent loop and starts the UI server.

generate_data.py: Utility to generate synthetic datasets for migration failure scenarios.

agent_memory.json: Append-only persistent log for auditing and learning.

agent_state.json: Tracks real-time execution states and pending approvals.

/agent (Core Logic)
observe.py: Signal ingestion and statistical normalization.

reason.py: Hybrid reasoning engine (Deterministic + LLM).

decide.py: Policy layer with safety gates and confidence thresholds.

act.py: Safe execution dispatcher for approved actions.

llm_client.py: Hardened interface for local LLM (Ollama/Phi-3).

memory.py: Manages the storage and querying of incident snapshots.

/ui (Explainability Dashboard)
index.html: The frontend structure for the agent dashboard.

app.js: Logic to visualize reasoning traces and learning trends.

styles.css: Visual styling for risk levels and reasoning modes.

/data
events.json & tickets.json: Simulated raw system logs and support tickets.

🛠️ Key Features

Explainable AI: A web-based dashboard provides a clear view of what the agent believes, why it believes it, and what actions it proposes.


Safety First: Deterministic cores work even if the LLM fails, and actions are restricted by strict policy limits.


Privacy & Efficiency: Uses a Local LLM via Ollama to avoid network latency and keep sensitive system data offline.


Learning Over Time: Tracks confidence trends and common failure modes to improve system stability.

🚦 Getting Started
Prerequisites: Ensure you have Python 3.x and Ollama installed locally.

Install Dependencies: pip install requests (for Ollama communication).

Run the Agent:

Bash:
python run_agent.py

View Dashboard: Open http://localhost:8000 in your browser to inspect the agent's real-time decisions.
