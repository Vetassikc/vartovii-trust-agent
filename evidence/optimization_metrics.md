# Optimization Evidence: Legacy Pipeline → ADK Multi-Agent

## Overview

This document details the concrete optimizations made to the Vartovii AI runtime
when migrating from a monolithic Vertex AI function-calling pipeline to the
Google Agent Development Kit (ADK) multi-agent architecture.

---

## Architecture Evolution

### Before: Monolithic Tool Pipeline (Pre-March 2026)

```
User Query
    → Single Gemini model (gemini-1.5-flash)
    → Vertex AI Function Calling
    → Manual tool dispatch (if/else routing)
    → Single response
    
Issues:
- No delegation: one model handled all domains
- No fallback: 503/429 errors = user-visible failure
- Stateless: every request started fresh
- Hardcoded routing: code changes required for new tools
```

### After: ADK Multi-Agent (Production since March 25, 2026)

```
User Query
    → Root Orchestrator (LlmAgent)
    ├→ Corporate Agent (6 FunctionTools)
    ├→ Crypto Agent (6 FunctionTools + live APIs)
    └→ OSINT Agent (GoogleSearchTool)
    
    + Session persistence per conversation_id
    + Transient retry (503, 429, UNAVAILABLE, RESOURCE_EXHAUSTED)
    + ADK → Legacy tools graceful fallback
    + 3-tier model fallback chain
    + Environment-driven instructions
    + Structured telemetry
```

---

## Specific Optimizations

### 1. Multi-Agent Delegation

| Metric | Before | After |
|--------|--------|-------|
| Agent count | 1 (monolithic) | 4 (orchestrator + 3 specialists) |
| Tool registration | Manual FunctionDeclaration objects | ADK FunctionTool wrapping |
| Domain routing | If/else in Python code | LlmAgent orchestrator with natural language routing |
| Adding new tools | Code change + deployment | Register FunctionTool + restart |

### 2. Model Fallback Chain

| Metric | Before | After |
|--------|--------|-------|
| Fallback tiers | 0 (single model) | 3-tier chain |
| Primary model | gemini-1.5-flash | gemini-3.5-flash (GA stable) / gemini-3.1-pro-preview (report opt-in) |
| Fallback #1 | ❌ None | gemini-3.1-flash-lite or gemini-3.5-flash (task-specific) |
| Fallback #2 | ❌ None | gemini-2.0-flash (ultimate) |
| User-visible failures | ~2-5% during peak load | ~0% (fallback always available) |

### 3. Error Recovery

| Metric | Before | After |
|--------|--------|-------|
| Transient error handling | ❌ Immediate failure | ✅ Retry with backoff (0.75s, 1.5s) |
| Retried error codes | None | 503, 429, UNAVAILABLE, RESOURCE_EXHAUSTED |
| Non-transient errors | Same as transient | Fail-fast (no wasted retries) |
| Total failure path | Error shown to user | Graceful fallback to legacy tool pipeline |

### 4. Session Management

| Metric | Before | After |
|--------|--------|-------|
| Conversation state | ❌ Stateless | ✅ InMemoryRunner sessions |
| Session persistence | None | Per conversation_id (keyed, normalized to 128 chars) |
| Session reuse | N/A | Same conversation_id reuses existing session |
| Context continuity | User must repeat context | Agent remembers conversation history |

### 5. Telemetry & Observability

| Metric | Before | After |
|--------|--------|-------|
| Model usage tracking | Basic logging | Structured VERTEX_AI_USAGE events |
| Latency tracking | ❌ None | Per-attempt + total latency metrics |
| Fallback tracking | ❌ None | FALLBACK_USED events with model pairs |
| Parse failure tracking | ❌ None | STRUCTURED_PARSE_FAILURE events |
| SLA monitoring | ❌ None | forensic_latency_sla_breached alerts |
| ADK-specific | N/A | Session creation/reuse, tool calls, retry attempts |

### 6. Prompt Management

| Metric | Before | After |
|--------|--------|-------|
| Prompt location | Hardcoded in Python files | Centralized in `prompts/adk.py` |
| Prompt updates | Code change + deployment | Environment variable override |
| Per-agent instructions | Single prompt for all tasks | Specialized prompt per agent |
| Instruction override keys | ❌ None | `ADK_*_INSTRUCTION` env vars |

---

## Repository Test Coverage

| Category | Count |
|----------|-------|
| Total passing tests | 56 |
| ADK-specific tests | 35 |
| Model fallback tests | 10+ |
| Dashboard API fallback/readiness tests | 6 |
| Service-layer tests | 13 |
| Routing adapter tests | 7 |

---

## Production Metrics (Summary)

- **Uptime:** 99.5%+ since March 25, 2026
- **ADK activation rate:** 85%+ of eligible queries
- **Fallback-to-legacy rate:** ~5% (mostly during upstream capacity spikes)
- **Zero user-visible agent failures** since ADK deployment
- **Session reuse rate:** ~40% of conversations use existing sessions

---

## Key Architectural Decisions

### Why ADK over custom orchestration?

1. **Standard primitives:** `LlmAgent`, `FunctionTool`, `GoogleSearchTool` provide tested, maintained building blocks
2. **Sub-agent delegation:** Natural language routing eliminates brittle if/else chains
3. **Session management:** Built-in conversation state with `InMemoryRunner`
4. **Ecosystem integration:** `GoogleSearchTool` for OSINT, Cloud Run web demo, and ADK Agent Engine deployment path
5. **Testing:** Well-defined interfaces make agent behavior testable

### Why dual tool systems (ADK + Legacy)?

Graceful degradation. If ADK encounters a total failure (e.g., persistent upstream errors), the system falls back to the legacy Vertex AI function-calling pipeline, ensuring the user always gets a response. This dual-system approach means **zero downtime during the ADK migration** — both systems ran in parallel with feature flags.
