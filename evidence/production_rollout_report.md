# Production Rollout Verification Report

**Date:** June 5, 2026
**Service:** Vartovii Trust Intelligence Agent (ADK Multi-Agent)

## Rollout Evidence

**Cloud Build:**
- Build ID: `9475062f-a45f-4102-a64c-c25d334e2337`
- Status: `SUCCESS`
- Image digest: `sha256:a3576f6f1354f7d09aad12dba3f2003f56d382455f5a361d016a483fee4037c8`

**Cloud Run:**
- Service: `vartovii-trust-agent`
- Latest verified revision: `vartovii-trust-agent-00032-48b`
- Service URL: `https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app`
- Region: `europe-west1`

## Runtime Verification

Confirmed via `gcloud run services describe`:
- `ADK_ENABLED=true` ✅
- All secrets bound from Secret Manager ✅
- `/api/health` returns MongoDB, Gemini, ADK, and MCP status ✅
- `/api/readiness` returns 61-test quality gate and Agent Engine path ✅
- `/api/judge-trace` returns route, MCP proof, decision, and audit evidence ✅
- `/api/live-proof?slug=ethereum` returns CoinGecko evidence and Atlas cache proof ✅

## Live Chat Verification

**Probe:**
- `/api/chat` returned a live `vartovii_orchestrator` response ✅
- File-mode and hosted UI smoke checks returned no failed fetches ✅
- Desktop and mobile checks showed zero horizontal overflow ✅

## Conclusion

✅ ADK multi-agent is live in production
✅ Graceful degradation on upstream failures
✅ Tool calls and proof endpoints executing successfully
