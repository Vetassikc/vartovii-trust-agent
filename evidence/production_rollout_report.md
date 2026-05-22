# Production Rollout Verification Report

**Date:** March 25, 2026
**Service:** Vartovii Trust Intelligence Agent (ADK Multi-Agent)

## Rollout Evidence

**Cloud Build:**
- Build ID: `9653f7e3-441c-4239-9ecd-1ae4427b0afe`
- Status: `SUCCESS`
- Finish time: `2026-03-25T08:56:20.835245Z`

**Cloud Run:**
- Service: `sentry-app`
- Latest revision: `sentry-app-00527-62h`
- Service URL: `https://sentry-app-4p7rbtt5yq-oa.a.run.app`
- Region: `europe-west6`

## Runtime Verification

Confirmed via `gcloud run services describe`:
- `ADK_ENABLED=true` ✅
- `COMMIT_SHA=dc711a2` ✅
- All secrets bound from Secret Manager ✅

## Live Chat Verification

**Probe 1:**
- Response: `ok`
- ADK hit upstream 503 (model capacity)
- **Graceful fallback to legacy tools** ✅

**Probe 2:**
- Response: `ok`
- `execution.adk_agent=true` ✅
- `execution.adk_tools=["transfer_to_agent", "search_company", "get_trust_score"]` ✅

## Conclusion

✅ ADK multi-agent is live in production
✅ Graceful degradation on upstream failures
✅ Tool calls executing successfully
