let memory = [];
let activeIndex = null;

/* ---------------- Load Memory ---------------- */
async function loadMemory() {
  try {
    const res = await fetch("../agent_memory.json");
    const newMemory = await res.json();

    if (JSON.stringify(newMemory) !== JSON.stringify(memory)) {
      memory = newMemory.reverse();
      renderIncidentList();

      if (activeIndex === null && memory.length > 0) {
        selectIncident(0);
      }

      renderLearningInsights();
    }
  } catch (err) {
    console.error("Failed to load agent memory", err);
  }
}

/* ---------------- Sidebar ---------------- */
function renderIncidentList() {
  const list = document.getElementById("incidentList");
  list.innerHTML = "";

  memory.forEach((incident, index) => {
    const li = document.createElement("li");

    const time = new Date(
      incident.timestamp * 1000
    ).toLocaleTimeString();

    li.textContent = `${incident.incident_id.slice(0, 8)} • ${time}`;
    li.onclick = () => selectIncident(index);

    if (index === activeIndex) li.classList.add("active");
    list.appendChild(li);
  });
}

/* ---------------- Main Renderer ---------------- */
function selectIncident(index) {
  activeIndex = index;
  const incident = memory[index];

  /* ========== OBSERVE ========== */
  const obs = incident.observation;

  let observeText =
    `The agent observed ${obs.stats.ticket_count} support tickets, ` +
    `${obs.stats.error_count} system errors, and ` +
    `${obs.stats.failed_checkouts} failed checkouts.`;

  if (obs.anomalies.length > 0) {
    observeText += `\n\nDetected anomalies:\n`;
    observeText += obs.anomalies.map(a =>
      `• ${a.type.replaceAll("_", " ")} (${a.severity} severity)`
    ).join("\n");
  } else {
    observeText += `\n\nNo anomalies were detected.`;
  }

  document.getElementById("observe").innerText = observeText;

  /* ========== REASON ========== */
  const r = incident.reasoning;

  let reasonText =
    `The agent used ${r.reasoning_mode.toUpperCase()} reasoning.\n\n`;

  if (r.hypotheses && r.hypotheses.length > 0) {
    reasonText += `Primary hypotheses:\n`;
    reasonText += r.hypotheses.map(h =>
      `• ${h.cause.replaceAll("_", " ")} — ${h.explanation || "no explanation provided"} ` +
      `(confidence ${h.confidence})`
    ).join("\n");
  }

  if (r.assumptions && r.assumptions.length > 0) {
    reasonText += `\n\nAssumptions:\n`;
    reasonText += r.assumptions.map(a =>
      `• ${typeof a === "string" ? a : JSON.stringify(a)}`
    ).join("\n");
  }

  if (r.unknowns && r.unknowns.length > 0) {
    reasonText += `\n\nRemaining unknowns:\n`;
    reasonText += r.unknowns.map(u => {
      if (typeof u === "string") return `• ${u}`;
      if (u.question) return `• ${u.question}`;
      return `• ${JSON.stringify(u)}`;
    }).join("\n");
  }

  reasonText += `\n\nOverall confidence: ${r.confidence}`;

  document.getElementById("reason").innerText = reasonText;

  /* ========== DECIDE ========== */
  const decisions = incident.decision.decisions;

  let decideText = "";

  if (!decisions || decisions.length === 0) {
    decideText = "The agent did not make any decisions.";
  } else {
    decideText = decisions.map(d => {
      let base;

      switch (d.type) {
        case "monitor_only":
          base = "The agent decided to monitor the situation.";
          break;
        case "support_guidance":
          base = "The agent decided to provide guidance to the merchant.";
          break;
        case "escalate_engineering":
          base = "The agent decided to escalate the issue to the engineering team.";
          break;
        case "documentation_update_suggestion":
          base = "The agent suggested updating internal documentation.";
          break;
        default:
          base = `The agent made a decision of type: ${d.type}.`;
      }

      if (d.reason) base += ` Reason: ${d.reason}.`;
      if (d.requires_human_approval) base += " This decision requires human approval.";

      return base;
    }).join("\n");
  }

  document.getElementById("decide").innerText = decideText;

  /* ========== ACT ========== */
  const actions = incident.action.actions_taken;

  let actText = "";

  if (!actions || actions.length === 0) {
    actText = "No automatic actions were executed.";
  } else {
    actText = actions.map(a => {
      switch (a.action) {
        case "monitoring":
          return "The system continues to monitor the situation.";
        case "support_guidance_prepared":
          return "A support guidance checklist was prepared for the merchant.";
        case "engineering_escalation_created":
          return "An engineering escalation ticket was created.";
        default:
          return `An action was executed: ${a.action}.`;
      }
    }).join("\n");
  }

  document.getElementById("act").innerText = actText;

  /* ========== BADGE ========== */
  const badge = document.getElementById("reasoningBadge");
  badge.textContent = r.reasoning_mode;
  badge.className = `badge ${r.reasoning_mode}`;

  renderIncidentList();
}

/* ---------------- Learning Over Time ---------------- */
function renderLearningInsights() {
  if (memory.length < 5) {
    document.getElementById("learning").innerText =
      "Not enough history yet to infer learning trends.";
    return;
  }

  const recent = memory.slice(0, 15);
  const older = memory.slice(15, 30);

  const avg = arr =>
    arr.reduce((s, x) => s + x, 0) / (arr.length || 1);

  const recentConf = avg(recent.map(i => i.reasoning.confidence || 0));
  const olderConf = avg(older.map(i => i.reasoning.confidence || 0));

  const confidenceTrend =
    recentConf > olderConf ? "Improving" :
    recentConf < olderConf ? "Declining" :
    "Stable";

  const causeCount = {};
  memory.forEach(i => {
    i.reasoning.hypotheses.forEach(h => {
      causeCount[h.cause] = (causeCount[h.cause] || 0) + 1;
    });
  });

  const topCause = Object.entries(causeCount)
    .sort((a, b) => b[1] - a[1])[0];

  const escalationRate =
    memory.filter(i =>
      i.decision.decisions.some(d => d.type === "escalate_engineering")
    ).length / memory.length;

  const modeCount = {};
  memory.forEach(i => {
    const m = i.reasoning.reasoning_mode;
    modeCount[m] = (modeCount[m] || 0) + 1;
  });

  document.getElementById("learning").innerText =
    `Confidence trend: ${confidenceTrend}\n\n` +
    `Average confidence (recent): ${recentConf.toFixed(2)}\n` +
    `Average confidence (earlier): ${olderConf.toFixed(2)}\n\n` +
    `Most common issue learned:\n` +
    `• ${topCause ? topCause[0].replaceAll("_", " ") : "none"} ` +
    `(${topCause ? topCause[1] : 0} occurrences)\n\n` +
    `Reasoning modes used:\n` +
    Object.entries(modeCount)
      .map(([k, v]) => `• ${k}: ${v}`)
      .join("\n") +
    `\n\nEscalation rate:\n` +
    `• ${(escalationRate * 100).toFixed(1)}% of incidents`;
}

/* ---------------- Live Polling ---------------- */
setInterval(loadMemory, 2000);
loadMemory();
