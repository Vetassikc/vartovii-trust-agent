# Model Policy

Last updated: 2026-06-02

This document defines the model routing policy for Vartovii Trust Intelligence.
It is based on current Google Cloud model documentation verified on
2026-06-02.

## Current Model Choices

| Profile | Purpose | Agent | Chat | Report | Status |
|---------|---------|-------|------|--------|--------|
| `stable` | Production default | `gemini-3.5-flash` | `gemini-3.5-flash` | `gemini-3.5-flash` | GA |
| `cost` | High-volume low-latency mode | `gemini-3.1-flash-lite` | `gemini-3.1-flash-lite` | `gemini-3.1-flash-lite` | GA |
| `preview` | Explicit opt-in for hard report reasoning | `gemini-3.5-flash` | `gemini-3.5-flash` | `gemini-3.1-pro-preview` | Mixed GA/preview |

## Why `gemini-3.5-flash` Is The Default

`gemini-3.5-flash` is the best fit for this product because it is GA, globally
available, supports function calling, system instructions, structured output,
grounding with Google Search, chat completions, and a 1M token context window.
That combination is more valuable for a judged production demo than using a
preview model as the default.

## Why Preview Is Explicit Opt-In

Preview models can be strong, but they have higher operational risk:

- launch terms are pre-GA;
- model IDs can change;
- quota and regional behavior can be less predictable;
- failures during a live judging session are more damaging than a small quality
  gain.

For that reason, `preview` is only used when `GEMINI_MODEL_PROFILE=preview` is
set intentionally. The Cloud Run deploy script keeps production on the GA
profile unless `DEPLOY_ALLOW_PREVIEW_GEMINI=true` is also set.

## Invalid Or Retired IDs

Do not use these IDs in production configuration:

- `gemini-3-flash`
- `gemini-3-pro`

Use documented IDs such as:

- `gemini-3.5-flash`
- `gemini-3.1-flash-lite`
- `gemini-3.1-pro-preview`
- `gemini-3-flash-preview` only if there is a specific preview reason

## Fallback Chain

The runtime builds a deduplicated chain:

1. Task primary model.
2. Task fallback model when different from the primary.
3. `gemini-2.0-flash` as ultimate fallback.

Default production behavior:

```text
stable: gemini-3.5-flash -> gemini-2.0-flash
cost: gemini-3.1-flash-lite -> gemini-3.5-flash -> gemini-2.0-flash
preview report: gemini-3.1-pro-preview -> gemini-3.5-flash -> gemini-2.0-flash
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GEMINI_MODEL_PROFILE` | Selects `stable`, `cost`, or `preview`. |
| `GEMINI_ADK_MODEL` | Overrides the ADK orchestrator and sub-agent model. |
| `GEMINI_CHAT_MODEL` | Overrides the chat model. |
| `GEMINI_REPORT_MODEL` | Overrides report generation. |
| `GEMINI_SENTIMENT_MODEL` | Overrides lightweight scoring and sentiment tasks. |
| `GEMINI_MODEL_FALLBACK_ENABLED` | Enables or disables fallback chain construction. |
| `DEPLOY_GEMINI_MODEL_PROFILE` | Deploy-time profile override for Cloud Run. |
| `DEPLOY_ALLOW_PREVIEW_GEMINI` | Required for deploy script preview opt-in. |
| `DEPLOY_RESPECT_MODEL_OVERRIDES` | Allows explicit deploy-time `GEMINI_*_MODEL` overrides when set to `true`. |

## Verification Checklist

After changing model configuration:

1. Run `./.venv/bin/python -m pytest tests -q`.
2. Run `bash -n scripts/deploy.sh`.
3. Deploy or update Cloud Run environment variables.
4. Verify `/api/health`.
5. Send one `/api/chat` request and confirm a 200 response.
6. Check logs for model-not-found, quota, or unsupported-tool errors.

## Official References

- Gemini 3.5 Flash:
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-flash
- Gemini 3.1 Flash-Lite:
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-flash-lite
- Gemini 3.1 Pro:
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-1-pro
- Google models overview:
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/google-models
