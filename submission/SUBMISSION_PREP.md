# Vartovii Trust Agent Submission Prep

Last verified against Devpost on 2026-06-04.

## Official Hackathon Links

- Hackathon overview: https://rapid-agent.devpost.com/
- Rules: https://rapid-agent.devpost.com/rules
- Deadline: 2026-06-11 2:00 PM PDT
- Track to select: MongoDB

## Submission Links

- Hosted project: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app
- Public repository: https://github.com/Vetassikc/vartovii-trust-agent
- License: MIT, visible in `LICENSE`
- Main product context: https://sentryanalytic.com/
- Product docs: https://sentryanalytic.com/docs
- Judge trace proof: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/judge-trace
- Readiness proof: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/readiness

## Hard Requirements Checklist

- [ ] Devpost account is logged in with the correct email.
- [ ] Hosted project URL is included.
- [ ] Repository URL is public and reachable without login.
- [ ] Repository license is visible at the top of the GitHub page.
- [ ] Demo video is public or unlisted on YouTube or Vimeo.
- [ ] Demo video is about 3 minutes.
- [ ] Demo video is in English or has English subtitles.
- [ ] Written submission is in English.
- [ ] Submission supports English language use.
- [ ] MongoDB track is selected.
- [ ] The description explicitly mentions Gemini, Google ADK, Google Cloud deployment, MongoDB Atlas, and MongoDB MCP.
- [ ] The description does not over-frame this as the existing main product; it is a new hackathon agent layer for the broader Vartovii trust product.

## Judge Narrative

Use this hierarchy in every description and answer:

1. Vartovii is not a generic chatbot.
2. It is a multi-agent trust investigation system.
3. The agent plans a route, uses specialized tools, inspects evidence, stores memory, and returns a judge-verifiable decision.
4. MongoDB Atlas is the evidence and audit memory layer.
5. MongoDB MCP is the flexible ad-hoc database inspection path that lets the agent answer database questions beyond hard-coded tools.
6. The broader Vartovii product gives the submission a real-world path: corporate trust, crypto risk, reports, watchlists, and forensic workflows.

## Judging Criteria Mapping

### Technological Implementation

- Google ADK orchestrator with specialized agents.
- Vertex AI Gemini model routing with fallback policy.
- MongoDB Atlas collections for companies, crypto projects, investigations, and audit events.
- MongoDB MCP specialist for ad-hoc Atlas operations.
- Cloud Run hosted demo plus Agent Engine deployment path.
- Automated tests covering agent topology, MCP setup, API readiness, model policy, and fallback behavior.

### Design

- Evidence-first UI rather than a generic chat screen.
- Live readiness, data source, model, and MCP status are visible to judges.
- Judge trace section exposes the route, trust score, evidence, MCP proof, and final decision.
- Product context links explain how the hackathon agent connects to the broader Vartovii product.

### Potential Impact

- Trust investigations are slow and fragmented today.
- Analysts, investors, job seekers, and crypto users need fast, auditable risk checks.
- The product turns scattered signals into a repeatable trust decision with evidence and memory.

### Quality of the Idea

- The core idea is trust intelligence with auditable agent behavior.
- It combines agent orchestration, database memory, MCP flexibility, and real product context.
- The submission demonstrates a path from hackathon demo to a practical trust layer for financial, corporate, and crypto workflows.

## Demo Flow For Tomorrow

1. Open the hosted project and show that the status reads live.
2. Ask for a judge-ready Wirecard investigation.
3. Scroll to the judge trace and show route, score, evidence, MCP proof, and decision.
4. Ask how MongoDB Atlas and MCP improve the workflow.
5. Show `/api/judge-trace` in a browser tab to prove the UI is backed by a real endpoint.
6. Show `/api/readiness` to prove tests, model, database, Agent Engine, and MCP status.
7. Briefly show the repository README, license, architecture diagram, and tests.
8. End with the main product context: this agent is a new evidence-first agent layer for the broader Vartovii trust product.

## Final Sanity Checks Before Submission

Run these locally if time allows:

```bash
./.venv/bin/python -m pytest tests -q
bash -n scripts/deploy.sh
git diff --check
```

Then smoke the live endpoints:

```bash
curl -sS https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/health
curl -sS https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/readiness
curl -sS https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/judge-trace
```
