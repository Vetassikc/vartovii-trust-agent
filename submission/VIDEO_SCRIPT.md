# 3-Minute Demo Video Script

Target length: 2:45-3:00.

## Recording Setup

- Use English voiceover or English subtitles.
- Record the live hosted project, not only local files.
- Keep browser zoom at 100%.
- Use a clean browser window with three tabs ready:
  - Hosted project: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app
  - Judge trace: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/judge-trace
  - Repository: https://github.com/Vetassikc/vartovii-trust-agent

## Shot List

### 0:00-0:15 — Problem And Hook

Show the hero/status area.

Voiceover:

> Trust investigations are still too slow and too fragmented. If I want to know whether a company, employer, token, or wallet can be trusted, I need to manually connect signals across databases, search, reviews, and risk reports. Vartovii turns that into a judge-verifiable agent workflow.

### 0:15-0:40 — What The Agent Is

Show the main UI, live status, model/data/MCP indicators.

Voiceover:

> This is Vartovii Trust Intelligence Agent. It is not a generic chatbot. It is a Google ADK multi-agent system powered by Gemini, with MongoDB Atlas as the evidence and memory layer, and MongoDB MCP as the flexible database inspection path.

### 0:40-1:15 — Run The Judge Path

Click or type:

```text
Run a judge-ready investigation for Wirecard. Show the agent route, trust score, evidence, and final decision.
```

Show the response and scroll to the judge trace section.

Voiceover:

> The orchestrator routes the request through specialized agents. Corporate and risk tools inspect structured evidence, the memory agent persists the investigation, and the UI exposes the route, score, evidence, and final decision. This is important because judges do not need to trust a black-box answer; they can inspect the proof path.

### 1:15-1:50 — MongoDB Atlas And MCP Value

Click or type:

```text
Explain how MongoDB Atlas and MCP improve this trust investigation workflow.
```

Show the MCP proof section.

Voiceover:

> MongoDB Atlas stores the entities, investigations, and audit events. The structured tools handle production scoring paths. The MongoDB MCP specialist gives the agent flexible ad-hoc access for questions that were not hard-coded in advance. That is the partner superpower: the agent can inspect the database as part of the investigation workflow.

### 1:50-2:20 — Live Proof Endpoints

Switch to `/api/judge-trace`, then `/api/readiness`.

Voiceover:

> The submission also exposes live proof endpoints. The judge trace endpoint shows the route, decision, evidence, audit events, and MCP proof. The readiness endpoint shows the active model, MongoDB status, test count, Agent Engine deployment path, and MCP configuration.

### 2:20-2:45 — Repository And Production Quality

Switch to GitHub README. Briefly show README, architecture, license, and tests.

Voiceover:

> The repository is public, licensed, and includes architecture docs, model policy, source freshness policy, agent role mapping, deployment scripts, and automated tests. The goal was to make the project read like a production trust system, not a disposable demo.

### 2:45-3:00 — Main Product Context

Return to the UI product context section or footer.

Voiceover:

> This hackathon build is a new evidence-first agent layer for the broader Vartovii trust product. The main product covers corporate and crypto trust research, reports, watchlists, and forensic workflows. This submission proves the agent route, MongoDB memory, MCP inspection, and judge-ready decision layer.

## Backup One-Take Script

> Vartovii Trust Intelligence Agent helps users investigate whether a company or crypto project can be trusted. It is built with Google ADK, Gemini, MongoDB Atlas, and MongoDB MCP.
>
> The key idea is simple: do not just ask a chatbot for an opinion. Run a real investigation. The root orchestrator delegates work to specialized agents for corporate research, crypto risk, OSINT, memory, and database inspection. MongoDB Atlas stores the evidence and audit trail. MongoDB MCP gives the agent flexible ad-hoc database access beyond fixed tools.
>
> In the demo, I run a judge-ready Wirecard investigation. The system shows the route, the trust score, the evidence, and the final decision. It also exposes a live judge-trace endpoint so the workflow can be inspected outside the chat UI.
>
> I then ask how MongoDB Atlas and MCP improve the workflow. Atlas gives us durable memory and structured evidence. MCP gives the agent a flexible database specialist for unexpected investigation questions.
>
> Finally, the readiness endpoint proves that the system is deployed, tested, and configured with Gemini, Google ADK, MongoDB Atlas, MCP, and the Agent Engine deployment path. Vartovii is connected to a broader trust intelligence product for corporate and crypto research, but this hackathon submission is a new agent layer focused on verifiable investigation.
