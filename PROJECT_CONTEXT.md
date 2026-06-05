# Project Context

Last updated: 2026-06-05

## Product

Vartovii Trust Intelligence is an autonomous multi-agent system for evaluating
the trustworthiness of companies and crypto projects. It combines structured
MongoDB Atlas evidence, Google ADK orchestration, Vertex AI Gemini reasoning,
Google Search grounding, and the official MongoDB MCP server.

## Hackathon Frame

Target event: Google Cloud Rapid Agent Hackathon, MongoDB track.

The product should be presented as a working trust investigation console, not as
a generic chatbot. The strongest judging signal is that Vartovii demonstrates a
real agent graph, partner MCP integration, production hosting, auditable memory,
and a practical risk workflow.

## Core Thesis

Trust decisions fail when analysts must manually assemble weak signals from
reviews, market data, blockchain records, news, and historical context. Vartovii
turns that fragmented evidence into a fast, explainable investigation with a
clear risk label, supporting details, and an audit trail.

## Target Users

- Risk analysts evaluating vendors, employers, or counterparties.
- Crypto investors screening projects and wallets.
- Compliance teams that need repeatable evidence and audit history.
- Founders and operators who need a fast trust pre-check before deeper due
  diligence.

## Differentiators

1. Multi-agent ownership instead of a single broad prompt.
2. MongoDB Atlas as the memory and evidence layer.
3. Official MongoDB MCP path for flexible database inspection.
4. Gemini 3.5 Flash GA as the production model, with explicit preview and cost
   profiles.
5. Live CoinGecko proof path with MongoDB Atlas cache and inspectable freshness.
6. Structured fallback and mock continuity so the demo survives upstream issues.
7. A dashboard that shows readiness, source state, agent graph, and ranked
   evidence instead of hiding the system behind chat only.

## Demo Narrative

1. Open the live console and show `LIVE` plus `MongoDB live`.
2. Highlight the decision brief: score, risk, orchestrator, specialist agents,
   and MCP proof.
3. Show the live proof block or `/api/live-proof?slug=ethereum` to prove
   current source enrichment and Atlas cache persistence.
4. Run a chat investigation for a known company or crypto project.
5. Open the leaderboard/entity detail to show structured evidence.
6. Show architecture and readiness sections to connect the product to judging
   requirements.
7. Mention that secrets are handled through Secret Manager and `.env` is not
   shipped.

## What The Project Is Not

- Not a static landing page.
- Not a toy chatbot with hardcoded answers.
- Not a private-data scraper.
- Not a replacement for regulated legal, investment, or compliance advice.

## Current Production Surface

- Cloud Run web console and API.
- FastAPI backend.
- Google ADK root agent with specialist sub-agents.
- MongoDB Atlas live data path with mock fallback.
- CoinGecko live evidence proof with MongoDB Atlas cache.
- Secret Manager for runtime credentials.
- Agent Engine deployment script for the hosted ADK graph path.

## Near-Term Product Improvements

- Add source freshness badges to entity details.
- Persist OSINT search summaries with `retrieved_at` and `expires_at`.
- Add a small model comparison smoke test for `stable`, `cost`, and `preview`.
- Add one end-to-end test that creates an investigation and verifies the audit
  record.
- Prepare final demo video script and Devpost submission copy after the product
  surface is stable.
