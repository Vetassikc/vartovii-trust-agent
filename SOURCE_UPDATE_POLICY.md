# Source Update Policy

Last updated: 2026-06-02

This policy defines how Vartovii treats source freshness, evidence updates, and
conflicting data. It exists so the product can be judged as an auditable trust
intelligence system rather than a static demo dataset.

## Source Tiers

| Tier | Source type | Examples | Trust use |
|------|-------------|----------|-----------|
| Tier 0 | Internal evidence and audit data | `investigations`, `audit_log`, saved agent outputs | Replay, continuity, operator accountability |
| Tier 1 | Primary structured sources | MongoDB Atlas records seeded from vetted APIs, chain data, review aggregates | Default scoring inputs |
| Tier 2 | Fresh public corroboration | Google Search grounding, official company/project pages, public registries | Freshness checks and contradiction handling |
| Tier 3 | User-provided context | User query, uploaded or pasted facts, manual analyst notes | Context only until corroborated |

## Freshness Windows

| Evidence class | Target freshness | Stale after | Action when stale |
|----------------|------------------|-------------|-------------------|
| Wallet balance and recent transactions | 15 minutes | 1 hour | Refresh or mark as stale before final risk claim |
| Token/project market signals | 1 hour | 6 hours | Refresh before ranking or trend claims |
| Security/audit status | 24 hours | 7 days | Verify with OSINT if risk is medium or higher |
| Company review aggregates | 7 days | 30 days | Use as historical signal and disclose age |
| News, sanctions, legal, incident data | 1 hour | 24 hours | Run OSINT before final decision |
| Static company metadata | 30 days | 90 days | Refresh during scheduled source sync |

## Required Evidence Metadata

New or refreshed source records should include:

- `source_name`
- `source_type`
- `source_url` when public
- `retrieved_at`
- `expires_at` or freshness class
- `confidence`
- `normalization_version`
- `last_verified_by` when manually reviewed

Records that lack freshness metadata may be used for demo continuity, but they
must not be presented as fresh live evidence.

## Update Workflow

1. Fetch source data through a structured connector, custom tool, or OSINT
   grounding.
2. Normalize fields into the relevant MongoDB collection.
3. Validate required fields and freshness metadata.
4. Upsert by stable entity key, not by display name alone.
5. Log the update to `audit_log` with agent/tool, source, and timestamp.
6. Recompute trust score only after validation passes.
7. Preserve the previous value when the new source conflicts without enough
   confidence to override it.

## Conflict Handling

When sources disagree:

- Prefer primary official sources over secondary summaries.
- Prefer more recent evidence only when the source is credible and complete.
- Keep both values if they describe different time windows.
- Mark the risk explanation with a contradiction note.
- Route high-impact contradictions to OSINT before saving a final investigation.

## MongoDB and MCP Usage

Structured PyMongo tools are the production path for common workflows. The MCP
specialist is reserved for:

- Ad-hoc collection inspection.
- Debugging stale or missing data.
- Aggregations not yet implemented as first-class tools.
- Explain-plan or index analysis.

MCP output should be converted into an auditable investigation or source update
before it influences user-facing scoring.

## Non-Goals

- Do not scrape private data.
- Do not store secrets in source records.
- Do not overwrite verified evidence with unverified user-provided claims.
- Do not present stale demo data as current market or legal truth.
