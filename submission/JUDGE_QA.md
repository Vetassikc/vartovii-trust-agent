# Judge Q&A Cheat Sheet

## What is Vartovii?

Vartovii is a trust intelligence system for investigating companies and crypto projects. This standalone hackathon build uses Google ADK and MongoDB MCP to turn a trust question into a verifiable investigation route.

## Why is this an agent and not just a chatbot?

The system does not only generate text. It routes work through specialized agents, calls tools, inspects evidence, persists investigations, logs audit events, and exposes live proof endpoints. The judge can inspect the route and final decision instead of relying only on a chat transcript.

## Why MongoDB?

Trust investigation depends on durable evidence and flexible entity data. MongoDB Atlas stores companies, crypto projects, investigations, audit events, wallet data, and related trust signals. It also fits the product because investigations naturally produce document-shaped records with nested evidence, decisions, source metadata, and audit history.

## Why MongoDB MCP?

Structured PyMongo tools are best for production scoring workflows. MongoDB MCP adds a flexible investigation path for ad-hoc database inspection, aggregation, and explain-plan style tasks. This lets the agent answer unexpected database questions without requiring every query shape to be pre-built.

## What live data does it use?

The live proof paths call CoinGecko for current crypto market evidence and Etherscan for native ETH wallet balance evidence. The system stores both proof records in MongoDB Atlas and exposes source freshness and persistence status through `/api/live-proof` and `/api/wallet-live-proof`.

## Is this connected to prior work?

The domain is trust intelligence, but this submission is packaged as a standalone contest build. The submitted agent graph, proof endpoints, UI, tests, deployment scripts, MongoDB Atlas path, and MongoDB MCP integration are focused on the hackathon requirements.

## Is this only a demo?

It is a hackathon implementation, but it is structured like a production system. It includes a public repository, MIT license, Cloud Run deployment, FastAPI backend, static UI, ADK agent graph, MongoDB Atlas integration, MCP path, model policy, source update policy, and automated tests.

## What should judges verify first?

1. Open the hosted project.
2. Run the Wirecard judge path.
3. Inspect the judge trace in the UI.
4. Inspect the live proof block in the UI.
5. Open `/api/live-proof?slug=ethereum`.
6. Open `/api/wallet-live-proof`.
7. Open `/api/judge-trace`.
8. Open `/api/readiness`.
9. Check the repository README, license, architecture, and tests.

## What is the strongest differentiator?

The strongest differentiator is verifiability. Many agent demos show a polished chat answer. Vartovii shows the live source proof, investigation route, evidence, memory, MCP proof, audit trail, model policy, and final decision.

## What is the biggest product opportunity?

The opportunity is to make trust checks fast and repeatable for analysts, investors, job seekers, procurement teams, and crypto users. A future production version can monitor entities over time, generate reports, alert users when trust scores change, and support deeper forensic workflows.
