# Devpost Field Answers

Last verified: 2026-06-07

## Project Overview

### Project name

Vartovii Trust Intelligence Agent

### Elevator pitch

A multi-agent trust investigation console that uses Gemini, Google ADK, MongoDB Atlas, and MongoDB MCP to produce judge-verifiable company and crypto risk decisions.

## Project Details

### About the project

## Inspiration

Trust decisions are still slow, fragmented, and hard to audit. When a user wants to know whether a company, employer, crypto project, or wallet can be trusted, they usually have to jump across databases, review sites, market APIs, blockchain explorers, search results, and spreadsheets.

Vartovii was built to turn that manual trust research process into an agent workflow: one request, a visible route, evidence-backed scoring, durable memory, and a decision that can be inspected by a judge instead of accepted as a black-box chatbot answer.

## What it does

Vartovii Trust Intelligence Agent runs multi-step trust investigations for companies and crypto projects.

The system can:

- Route a prompt through a Google ADK multi-agent graph.
- Delegate work to corporate, crypto, OSINT, memory, and MongoDB MCP specialists.
- Analyze trust signals and return a risk score with supporting evidence.
- Persist investigations, live evidence, and audit events in MongoDB Atlas.
- Expose judge-verifiable proof through `/api/readiness`, `/api/judge-trace`, `/api/live-proof`, and `/api/wallet-live-proof`.
- Fetch live CoinGecko market evidence and live Etherscan wallet balance evidence.
- Cache live proof records in MongoDB Atlas so the result can be inspected later.
- Show the agent route, source freshness, persistence state, trust dimensions, and audit activity in the UI.

The judge demo focuses on a Wirecard-style trust investigation, a live Ethereum market proof, and a live Etherscan wallet balance proof.

## How we built it

The project is built around a Google ADK agent graph. A root orchestrator powered by Gemini delegates work to specialized agents:

- Corporate Agent for company trust signals.
- Crypto Agent for crypto project and wallet risk.
- OSINT Agent for web-grounded research.
- Memory Agent for investigations and audit events.
- MongoDB MCP Agent for flexible Atlas inspection.

MongoDB Atlas is the evidence and memory layer. It stores companies, crypto projects, wallets, investigations, audit logs, and live evidence cache records.

The hosted project runs on Google Cloud Run with a FastAPI backend and static web console. Runtime secrets are handled through Google Secret Manager. The repo also includes an Agent Engine deployment helper to demonstrate the hosted ADK graph path.

## Google Cloud and Gemini

- Google ADK orchestrates the multi-agent graph.
- Vertex AI Gemini 3.5 Flash powers the production agent and chat runtime.
- Google Cloud Run hosts the live product demo.
- Google Secret Manager stores runtime credentials.
- Google Cloud Build builds and deploys the container.
- Agent Engine deployment support demonstrates the hosted ADK graph path.
- Google Search grounding supports OSINT-style research.

## MongoDB and MCP

MongoDB Atlas is not just storage in this project. It is the agent memory and evidence system.

Structured PyMongo tools handle production scoring workflows, while the MongoDB MCP specialist gives the ADK graph a flexible database inspection path for ad-hoc questions that were not hard-coded in advance.

That matters for trust investigation because analysts rarely know every query shape ahead of time. The agent needs durable evidence records and a flexible way to inspect them.

## What makes it different

Most agent demos stop at a polished chat answer. Vartovii is designed to be verifiable:

- It shows the agent route.
- It shows source freshness.
- It shows trust-score inputs.
- It stores evidence in MongoDB Atlas.
- It exposes audit activity.
- It includes live CoinGecko and Etherscan proof.
- It shows MongoDB MCP as an inspectable investigation path.
- It includes a readiness endpoint, judge trace endpoint, and automated tests.

The goal is not only to answer "is this trustworthy?" but to show how that decision was reached.

## Challenges we ran into

The hardest part was making the project judge-verifiable rather than just impressive in a chat window. We had to expose runtime state, source freshness, model policy, MongoDB persistence, MCP readiness, and the final decision path in a way that could survive a live demo.

We also hardened the deployment path so secrets stay out of the repo, stale model labels are normalized, live source failures degrade safely, and the UI remains usable on both desktop and mobile.

## Accomplishments that we are proud of

- Built a standalone Google ADK multi-agent trust investigation system.
- Integrated MongoDB Atlas as the evidence, memory, and audit layer.
- Added MongoDB MCP as a partner-powered database specialist.
- Deployed a live Cloud Run product with FastAPI and a judge-facing UI.
- Added live CoinGecko market proof with Atlas cache persistence.
- Added live Etherscan wallet balance proof with Atlas cache persistence.
- Added readiness, judge trace, audit, and live proof endpoints.
- Added 63 automated tests across agent topology, services, dashboard API, model policy, and proof contracts.
- Improved the UI into an evidence-first console rather than a generic chatbot surface.

## What we learned

The strongest agent products are not just fluent. They need boundaries, tools, memory, route transparency, and source freshness. MongoDB Atlas and MCP are a strong fit because real trust work is both structured and unpredictable: some questions need fixed scoring tools, while others need flexible database inspection.

## What's next

Next, Vartovii can grow into a production trust intelligence layer:

- More live connectors for corporate, crypto, OSINT, and compliance signals.
- Watchlists and alerts when trust scores change.
- Analyst review workflows and exportable reports.
- Deeper source freshness policy and evidence ranking.
- More MCP-powered forensic workflows.
- Team workspaces for shared investigations.

### Built with

Python, FastAPI, Google ADK, Vertex AI Gemini 3.5 Flash, Google Cloud Run, Google Cloud Build, Google Secret Manager, Google Agent Engine, Google Search Grounding, MongoDB Atlas, MongoDB MCP Server, PyMongo, Model Context Protocol, Etherscan API V2, CoinGecko API, JavaScript, HTML, CSS, Docker, pytest, Playwright.

### Try it out links

Hosted project:
https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app

Open-source repository:
https://github.com/Vetassikc/vartovii-trust-agent

Readiness proof:
https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/readiness

Judge trace proof:
https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/judge-trace

Live CoinGecko proof:
https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/live-proof?slug=ethereum

Live Etherscan wallet proof:
https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app/api/wallet-live-proof

## Additional Info

### Submitter type

Recommended selection: Individual

### Organization name

Recommended entry: N/A

### Government employee

Recommended selection: No, if accurate for every team member. Confirm manually before final submission.

### Submitter country of residence

Select your actual country of residence manually.

### Canadian province

Recommended entry: N/A, unless you or a team member resides in Canada.

### Partner track

MongoDB

### Is your project new or existing prior to May 5, 2026?

Recommended selection: New

### Open-source code repository URL

https://github.com/Vetassikc/vartovii-trust-agent

### Hosted project URL

https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app

### Google Cloud products used

Google ADK, Vertex AI Gemini 3.5 Flash, Google Cloud Run, Google Cloud Build, Google Secret Manager, Google Agent Engine deployment path, and Google Search Grounding.

### Other tools or products used

MongoDB Atlas, MongoDB MCP Server, Model Context Protocol, PyMongo, FastAPI, Docker, Etherscan API V2, CoinGecko API, pytest, Playwright, vanilla JavaScript, HTML, and CSS.

### First time using Arize tools?

Recommended selection: Yes, if accurate for the team.

### First time using Elastic tools?

Recommended selection: Yes, if accurate for the team.

### First time using Fivetran tools?

Recommended selection: Yes, if accurate for the team.

### First time using GitLab tools?

Recommended selection: Yes, if accurate for the team.

### First time using MongoDB tools?

Recommended selection: No, if accurate for the team.

### First time using Dynatrace tools?

Recommended selection: Yes, if accurate for the team.

## Media

### Video demo link

Pending. Use an unlisted YouTube or Vimeo URL after recording the 3-minute demo.

### Recommended image gallery uploads

1. `submission/media/vartovii-hero.png`
2. `submission/media/vartovii-live-proof.png`
3. `submission/media/vartovii-judge-trace.png`
4. `submission/media/vartovii-architecture.png`
