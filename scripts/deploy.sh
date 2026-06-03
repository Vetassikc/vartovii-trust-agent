#!/bin/bash
# ============================================
# Vartovii Trust Agent — Cloud Run Deploy
# ============================================
# Usage:
#   chmod +x scripts/deploy.sh
#   ./scripts/deploy.sh
#
# Prerequisites:
#   - gcloud CLI authenticated
#   - GCP project set
#   - Docker installed (for local build) OR use Cloud Build

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
fi

if [[ -f ".env" ]]; then
    eval "$("${PYTHON_BIN}" - <<'PY'
from dotenv import dotenv_values
import shlex

for key, value in dotenv_values(".env").items():
    if key and value is not None:
        print(f"export {key}={shlex.quote(value)}")
PY
)"
fi

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${CLOUD_RUN_REGION:-europe-west1}"
SERVICE_NAME="vartovii-trust-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
GOOGLE_API_SECRET_NAME="${GOOGLE_API_SECRET_NAME:-vartovii-google-api-key}"
MONGODB_SECRET_NAME="${MONGODB_SECRET_NAME:-vartovii-mongodb-connection-string}"
MONGODB_DATABASE="${MONGODB_DATABASE:-vartovii}"
MONGODB_MCP_ENABLED="${MONGODB_MCP_ENABLED:-true}"
GOOGLE_GENAI_USE_VERTEXAI="${GOOGLE_GENAI_USE_VERTEXAI:-true}"
GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
PUBLIC_HOSTED_URL="${PUBLIC_HOSTED_URL:-https://vartovii-trust-agent-n7kszqvpoq-ew.a.run.app}"
AGENT_ENGINE_RESOURCE_NAME="${AGENT_ENGINE_RESOURCE_NAME:-projects/1047739822568/locations/europe-west1/reasoningEngines/1778103816160280576}"
AGENT_ENGINE_CONSOLE_URL="${AGENT_ENGINE_CONSOLE_URL:-https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/europe-west1/agent-engines/1778103816160280576/playground?project=1047739822568}"
GEMINI_MODEL_PROFILE="${DEPLOY_GEMINI_MODEL_PROFILE:-${GEMINI_MODEL_PROFILE:-stable}}"
if [[ "${GEMINI_MODEL_PROFILE}" == "preview" && "${DEPLOY_ALLOW_PREVIEW_GEMINI:-false}" != "true" ]]; then
    GEMINI_MODEL_PROFILE="stable"
fi
if [[ "${DEPLOY_RESPECT_MODEL_OVERRIDES:-false}" != "true" ]]; then
    unset GEMINI_ADK_MODEL GEMINI_CHAT_MODEL GEMINI_REPORT_MODEL GEMINI_SENTIMENT_MODEL
fi
case "${GEMINI_MODEL_PROFILE}" in
    cost)
        DEFAULT_GEMINI_ADK_MODEL="gemini-3.1-flash-lite"
        DEFAULT_GEMINI_CHAT_MODEL="gemini-3.1-flash-lite"
        DEFAULT_GEMINI_REPORT_MODEL="gemini-3.1-flash-lite"
        DEFAULT_GEMINI_SENTIMENT_MODEL="gemini-3.1-flash-lite"
        ;;
    preview)
        DEFAULT_GEMINI_ADK_MODEL="gemini-3.5-flash"
        DEFAULT_GEMINI_CHAT_MODEL="gemini-3.5-flash"
        DEFAULT_GEMINI_REPORT_MODEL="gemini-3.1-pro-preview"
        DEFAULT_GEMINI_SENTIMENT_MODEL="gemini-3.5-flash"
        ;;
    *)
        DEFAULT_GEMINI_ADK_MODEL="gemini-3.5-flash"
        DEFAULT_GEMINI_CHAT_MODEL="gemini-3.5-flash"
        DEFAULT_GEMINI_REPORT_MODEL="gemini-3.5-flash"
        DEFAULT_GEMINI_SENTIMENT_MODEL="gemini-3.5-flash"
        ;;
esac
GEMINI_ADK_MODEL="${GEMINI_ADK_MODEL:-${DEFAULT_GEMINI_ADK_MODEL}}"
GEMINI_CHAT_MODEL="${GEMINI_CHAT_MODEL:-${DEFAULT_GEMINI_CHAT_MODEL}}"
GEMINI_REPORT_MODEL="${GEMINI_REPORT_MODEL:-${DEFAULT_GEMINI_REPORT_MODEL}}"
GEMINI_SENTIMENT_MODEL="${GEMINI_SENTIMENT_MODEL:-${DEFAULT_GEMINI_SENTIMENT_MODEL}}"
RUNTIME_ENV_VARS="GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},PUBLIC_HOSTED_URL=${PUBLIC_HOSTED_URL},AGENT_ENGINE_RESOURCE_NAME=${AGENT_ENGINE_RESOURCE_NAME},AGENT_ENGINE_CONSOLE_URL=${AGENT_ENGINE_CONSOLE_URL},GEMINI_MODEL_PROFILE=${GEMINI_MODEL_PROFILE},GEMINI_ADK_MODEL=${GEMINI_ADK_MODEL},GEMINI_CHAT_MODEL=${GEMINI_CHAT_MODEL},GEMINI_REPORT_MODEL=${GEMINI_REPORT_MODEL},GEMINI_SENTIMENT_MODEL=${GEMINI_SENTIMENT_MODEL},ADK_ENABLED=true,MONGODB_ENABLED=true,MONGODB_DATABASE=${MONGODB_DATABASE},MONGODB_MCP_ENABLED=${MONGODB_MCP_ENABLED}"

upsert_secret() {
    local secret_name="$1"
    local secret_value="$2"

    if [[ -z "${secret_value}" ]]; then
        return 0
    fi

    if gcloud secrets describe "${secret_name}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
        printf "%s" "${secret_value}" | gcloud secrets versions add "${secret_name}" \
            --data-file=- \
            --project="${PROJECT_ID}" \
            --quiet >/dev/null
    else
        printf "%s" "${secret_value}" | gcloud secrets create "${secret_name}" \
            --data-file=- \
            --replication-policy=automatic \
            --project="${PROJECT_ID}" \
            --quiet >/dev/null
    fi
}

echo "════════════════════════════════════════════════════"
echo "  🛡️  Vartovii Trust Agent — Cloud Run Deploy"
echo "════════════════════════════════════════════════════"
echo "  Project:  ${PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  Service:  ${SERVICE_NAME}"
echo "  Image:    ${IMAGE_NAME}"
echo "  Profile:  ${GEMINI_MODEL_PROFILE}"
echo "  Model:    ${GEMINI_ADK_MODEL}"
echo "════════════════════════════════════════════════════"
echo ""

# Step 1: Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    --project="${PROJECT_ID}" \
    --quiet

# Step 2: Build with Cloud Build (no local Docker needed)
echo ""
echo "🏗️  Building container with Cloud Build..."
gcloud builds submit \
    --tag="${IMAGE_NAME}" \
    --project="${PROJECT_ID}" \
    --quiet

# Step 3: Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=3 \
    --timeout=300 \
    --set-env-vars="${RUNTIME_ENV_VARS}" \
    --quiet

# Step 4: Store runtime secrets in Secret Manager and attach to Cloud Run
echo ""
echo "🔐 Configuring runtime secrets..."
upsert_secret "${GOOGLE_API_SECRET_NAME}" "${GOOGLE_API_KEY:-}"
upsert_secret "${MONGODB_SECRET_NAME}" "${MONGODB_CONNECTION_STRING:-}"

SERVICE_ACCOUNT=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || true)

if [[ -z "${SERVICE_ACCOUNT}" ]]; then
    PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
    SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
fi

if [[ "${GOOGLE_GENAI_USE_VERTEXAI}" == "true" ]]; then
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/aiplatform.user" \
        --quiet >/dev/null
fi

if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
    gcloud secrets add-iam-policy-binding "${GOOGLE_API_SECRET_NAME}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="${PROJECT_ID}" \
        --quiet >/dev/null
fi

if [[ -n "${MONGODB_CONNECTION_STRING:-}" ]]; then
    gcloud secrets add-iam-policy-binding "${MONGODB_SECRET_NAME}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="${PROJECT_ID}" \
        --quiet >/dev/null
fi

SECRET_ARGS=()
if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
    SECRET_ARGS+=("GOOGLE_API_KEY=${GOOGLE_API_SECRET_NAME}:latest")
fi
if [[ -n "${MONGODB_CONNECTION_STRING:-}" ]]; then
    SECRET_ARGS+=("MONGODB_CONNECTION_STRING=${MONGODB_SECRET_NAME}:latest")
fi

if [[ ${#SECRET_ARGS[@]} -gt 0 ]]; then
    SECRET_SPEC=$(IFS=,; echo "${SECRET_ARGS[*]}")
    gcloud run services update "${SERVICE_NAME}" \
        --region="${REGION}" \
        --project="${PROJECT_ID}" \
        --set-secrets="${SECRET_SPEC}" \
        --update-env-vars="${RUNTIME_ENV_VARS}" \
        --quiet >/dev/null
fi

# Step 5: Get the URL
echo ""
echo "════════════════════════════════════════════════════"
URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.url)")
echo "  ✅ Deployed successfully!"
echo "  🌐 URL: ${URL}"
echo ""
echo "  🔐 Runtime secrets: Secret Manager"
echo "════════════════════════════════════════════════════"
