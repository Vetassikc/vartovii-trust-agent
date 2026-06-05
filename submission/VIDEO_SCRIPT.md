# 3-Minute Demo Video Script

Target length: 2:45-3:00.

## Recording Setup

- Use English voiceover or English subtitles.
- Record the live hosted project, not only local files.
- Keep browser zoom at 100%.
- Use a clean browser window with three tabs ready:
  - Hosted project: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app
  - Live proof: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/live-proof?slug=ethereum
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

### 1:50-2:20 — Live Source Proof

Scroll to the Live Proof section, then switch to `/api/live-proof?slug=ethereum`.

Voiceover:

> The project also proves that it is not limited to static seed data. This live proof path fetches current CoinGecko market evidence, computes a trust-score delta, and stores the proof in MongoDB Atlas for audit and MCP inspection. The UI shows the source, freshness, adjusted score, and persistence status.

### 2:20-2:40 — Judge Trace And Readiness

Switch to `/api/judge-trace`, then `/api/readiness`.

Voiceover:

> The submission also exposes live proof endpoints. The judge trace endpoint shows the route, decision, evidence, audit events, and MCP proof. The readiness endpoint shows the active model, MongoDB status, test count, Agent Engine deployment path, and MCP configuration.

### 2:40-2:55 — Repository And Production Quality

Switch to GitHub README. Briefly show README, architecture, license, and tests.

Voiceover:

> The repository is public, licensed, and includes architecture docs, model policy, source freshness policy, agent role mapping, deployment scripts, and automated tests. The goal was to make the project read like a production trust system, not a disposable demo.

### 2:55-3:00 — Close

Return to the UI standalone context section or footer.

Voiceover:

> The result is a standalone contest build for evidence-first trust investigation: live source proof, MongoDB memory, MCP inspection, and a judge-ready decision layer.

## Backup One-Take Script

> Vartovii Trust Intelligence Agent helps users investigate whether a company or crypto project can be trusted. It is built with Google ADK, Gemini, MongoDB Atlas, and MongoDB MCP.
>
> The key idea is simple: do not just ask a chatbot for an opinion. Run a real investigation. The root orchestrator delegates work to specialized agents for corporate research, crypto risk, OSINT, memory, and database inspection. MongoDB Atlas stores the evidence and audit trail. MongoDB MCP gives the agent flexible ad-hoc database access beyond fixed tools.
>
> In the demo, I run a judge-ready Wirecard investigation. The system shows the route, the trust score, the evidence, and the final decision. It also exposes a live judge-trace endpoint so the workflow can be inspected outside the chat UI.
>
> I then show the live proof endpoint for Ethereum. It fetches current CoinGecko market evidence, computes a trust-score delta, and stores that proof in MongoDB Atlas. Atlas gives us durable memory and structured evidence. MCP gives the agent a flexible database specialist for unexpected investigation questions.
>
> Finally, the readiness endpoint proves that the system is deployed, tested, and configured with Gemini, Google ADK, MongoDB Atlas, MCP, and the Agent Engine deployment path. This is a standalone hackathon build focused on verifiable investigation.
