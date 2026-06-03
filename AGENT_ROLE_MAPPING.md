# Agent Role Mapping

Last updated: 2026-06-02

This document defines the ownership model for the Vartovii ADK multi-agent
system. It is intended for maintainers, judges, and future coding agents.

## System Principle

The root agent routes. Specialist agents investigate. Tools touch data. Memory
persists decisions. This separation keeps the graph auditable and prevents the
orchestrator from becoming a hidden all-purpose agent.

## Agent Map

| Agent | Primary role | Owns | Must not own |
|-------|--------------|------|--------------|
| `vartovii_orchestrator` | Intent routing and delegation | Query classification, sub-agent selection, context handoff | Direct evidence lookup, raw MongoDB access, final risk claims without specialist output |
| `corporate_agent` | Company and employer trust analysis | Company search, reviews, trust score, comparisons, vacancy signals | Wallet forensics, MCP database exploration |
| `crypto_agent` | Crypto project and wallet risk analysis | Project search, contract indicators, holder risk, transaction history, wallet checks | Employer reviews, company reputation scoring |
| `osint_agent` | Fresh public web research | Real-time search, recent news, domain/background checks, source summaries | Persisting investigations, private database mutation |
| `memory_agent` | Investigation persistence and audit trail | Saving decisions, retrieving history, logging audit events | Primary scoring, raw source scraping |
| `mongodb_mcp_agent` | Ad-hoc Atlas inspection through MCP | Collection inspection, custom finds, aggregations, explain-plan work | User-facing conclusions without orchestrator/specialist synthesis |

## Tool Ownership

| Tool group | Owner | Data surface | Notes |
|------------|-------|--------------|-------|
| Corporate tools | `corporate_agent` | `companies`, review aggregates, vacancy signals | Structured production path for employer intelligence. |
| Crypto tools | `crypto_agent` | `crypto_projects`, `wallets`, transaction records | Structured production path for crypto and on-chain intelligence. |
| Investigation tools | `memory_agent` | `investigations`, `audit_log` | Must preserve auditability and avoid storing secrets. |
| Google Search grounding | `osint_agent` | Public web | Used when database evidence is missing, stale, or contradicted. |
| MongoDB MCP toolset | `mongodb_mcp_agent` | Atlas collections through official MCP server | Optional specialist for flexible database exploration. |

## Routing Rules

1. Company, employer, review, vacancy, reputation, and comparison requests route
   to `corporate_agent`.
2. Token, project, wallet, contract, holder, transaction, and DeFi requests
   route to `crypto_agent`.
3. Requests about latest news, recently changed facts, missing entities, or
   external corroboration route to `osint_agent`.
4. Requests to save, recall, compare with past investigations, or inspect audit
   history route to `memory_agent`.
5. Requests that require custom database exploration beyond structured tools
   route to `mongodb_mcp_agent` when MCP is configured.
6. Mixed requests should be decomposed by the orchestrator and delegated to the
   narrowest specialist first.

## Output Contract

Each specialist answer should include:

- Entity name and type.
- Trust score or risk classification when supported by evidence.
- Evidence summary with source type.
- Uncertainty or stale-data warning when applicable.
- Suggested next action for the operator.

## Guardrails

- No agent may expose raw secrets or connection strings.
- No agent should claim real-time freshness unless the source includes a
  retrieval timestamp or the OSINT agent performed a fresh lookup.
- The orchestrator must not answer directly when a specialist is available.
- The MCP agent is a database operator, not the final risk judge.
- Memory writes must include enough context for audit replay.
