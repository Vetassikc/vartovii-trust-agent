# Devpost Submission Copy

## Project Name

Vartovii Trust Intelligence Agent

## Tagline

A judge-verifiable multi-agent trust investigation system for companies and crypto projects, powered by Gemini, Google ADK, MongoDB Atlas, and MongoDB MCP.

## Short Description

Vartovii Trust Intelligence Agent helps users investigate whether a company or crypto project can be trusted. Instead of returning a generic chatbot answer, it routes the request through specialized agents, checks structured evidence, persists the investigation in MongoDB Atlas, exposes an audit trail, and returns a trust decision that judges can verify through live proof endpoints.

## Inspiration

Trust research is still painfully manual. A user who wants to evaluate a company, employer, token, wallet, or suspicious project usually has to jump between search results, review sites, on-chain tools, databases, reports, and spreadsheets. The hard part is not only finding signals; it is turning scattered signals into a decision that can be explained and audited.

Vartovii was built to make trust investigation fast, repeatable, and evidence-first. This hackathon submission focuses that idea into a new Google ADK and MongoDB MCP agent layer that can show its route, evidence, memory, and final decision.

## What It Does

Vartovii runs multi-step trust investigations for companies and crypto projects. A root orchestrator delegates work to specialized agents for corporate research, crypto risk, web/OSINT grounding, investigation memory, and optional MongoDB MCP inspection.

For the judge demo, the system can run a Wirecard-style investigation path and expose:

- The agent route used for the investigation.
- The trust score and risk reasoning.
- The evidence considered.
- MongoDB Atlas persistence.
- MongoDB MCP proof path.
- Audit events with model, latency, and action metadata.
- A final decision that can be inspected through the UI and `/api/judge-trace`.

## How We Built It

The project is built around a Google ADK multi-agent graph. The root orchestrator uses Gemini model routing and delegates work to specialized `LlmAgent` agents. Structured tools query MongoDB Atlas for production workflows, while the optional MongoDB MCP specialist provides flexible ad-hoc database access for collection inspection, aggregations, and explain-plan style workflows.

The hosted project runs on Google Cloud Run with a FastAPI backend and static web console. The repository also includes an Agent Engine deployment helper for the hosted ADK graph path. MongoDB Atlas stores evidence, entities, investigations, and audit events. The UI exposes readiness and judge-trace proof so judges can verify that the demo is backed by real runtime data.

## Google Cloud And Gemini

- Google ADK orchestrates the agent graph.
- Vertex AI Gemini powers the orchestrator and specialized agents.
- Google Cloud Run hosts the live project surface.
- Agent Engine deployment support demonstrates the hosted ADK graph path.
- Google Search grounding supports web/OSINT research when needed.

## MongoDB And MCP

MongoDB Atlas is the evidence and memory layer for the agent. It stores companies, crypto projects, investigations, audit events, and related trust signals.

The MongoDB MCP integration is used as a partner superpower: it gives the ADK graph a flexible database specialist that can inspect Atlas data beyond pre-built tool calls. This matters because real investigations often require unexpected database questions, not just fixed API endpoints.

## What Makes It Different

Most agent demos stop at a conversation. Vartovii is built around a verifiable investigation workflow:

- It plans and delegates through multiple agents.
- It uses domain-specific tools rather than only free-form generation.
- It stores investigation memory and audit events.
- It exposes readiness and judge-trace endpoints.
- It shows MongoDB Atlas and MCP as part of the product story, not just as hidden infrastructure.
- It connects to a broader trust intelligence product direction covering corporate research, crypto risk, reports, watchlists, and forensic workflows.

## Challenges We Ran Into

The hardest part was making the agent demo judge-verifiable. A normal chatbot response is not enough for this challenge, so the project needed visible proof of routing, source freshness, database state, model policy, MCP readiness, and final decision quality. We also hardened the system so old audit records cannot show stale model labels and so the UI works both as a deployed Cloud Run site and as a local file-mode demo.

## Accomplishments

- Built a Google ADK multi-agent trust investigation graph.
- Integrated MongoDB Atlas as evidence storage and audit memory.
- Added an optional MongoDB MCP specialist for flexible database inspection.
- Deployed the project on Google Cloud Run.
- Added live readiness and judge-trace proof endpoints.
- Added model routing and fallback policy.
- Added automated tests for the core agent, API, services, and MCP paths.
- Improved the UI so the demo communicates trust investigation rather than generic chat.

## What We Learned

The strongest agent experiences are not just more fluent conversations. They need route transparency, tool boundaries, durable memory, source freshness, and proof that the system can be inspected. MongoDB Atlas and MCP are a strong fit for this because trust work depends on both structured evidence and flexible investigation.

## What's Next

Next, Vartovii can expand from the hackathon proof path into a production trust intelligence layer:

- More live data connectors for corporate, crypto, and OSINT signals.
- Deeper evidence ranking and source freshness controls.
- Analyst review workflows and exportable reports.
- Watchlists and alerting for trust score changes.
- More MCP-powered investigation tools for ad-hoc forensic workflows.

## Links

- Hosted project: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app
- Repository: https://github.com/Vetassikc/vartovii-trust-agent
- Main product context: https://sentryanalytic.com/
- Judge trace proof: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/judge-trace
- Readiness proof: https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/readiness
