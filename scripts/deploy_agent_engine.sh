#!/bin/bash
# ============================================
# Vartovii Trust Agent — ADK Agent Engine Deploy
# ============================================
# Usage:
#   chmod +x scripts/deploy_agent_engine.sh
#   GOOGLE_CLOUD_PROJECT=my-project ./scripts/deploy_agent_engine.sh
#
# This deploys the ADK agent graph to Google Cloud Agent Engine. The Cloud Run
# deployment remains the primary web demo because it includes the FastAPI UI and
# a Node.js runtime for the MongoDB MCP child process.

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
fi

ADK_BIN="${ADK_BIN:-adk}"
if [[ -x ".venv/bin/adk" ]]; then
    ADK_BIN=".venv/bin/adk"
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

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || true)}"
REGION="${AGENT_ENGINE_REGION:-${CLOUD_RUN_REGION:-europe-west1}}"
VERTEX_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
DISPLAY_NAME="${AGENT_ENGINE_DISPLAY_NAME:-Vartovii Trust Agent}"
DESCRIPTION="${AGENT_ENGINE_DESCRIPTION:-Autonomous trust intelligence agent for company and crypto due diligence.}"
ENV_FILE="${AGENT_ENGINE_ENV_FILE:-}"
REQUIREMENTS_FILE="${AGENT_ENGINE_REQUIREMENTS_FILE:-agent/requirements.txt}"
ADK_APP_OBJECT="${AGENT_ENGINE_ADK_APP_OBJECT:-app}"
MCP_ENABLED="${AGENT_ENGINE_MCP_ENABLED:-false}"
TEMP_ENV_FILE=""

if [[ -z "${PROJECT_ID}" ]]; then
    echo "GOOGLE_CLOUD_PROJECT is required, or set a default gcloud project."
    exit 1
fi

if ! command -v "${ADK_BIN}" >/dev/null 2>&1; then
    echo "ADK CLI is required. Install google-adk in the active environment."
    exit 1
fi

echo "════════════════════════════════════════════════════"
echo "  Vartovii Trust Agent — Agent Engine Deploy"
echo "════════════════════════════════════════════════════"
echo "  Project:      ${PROJECT_ID}"
echo "  Region:       ${REGION}"
echo "  Vertex loc:   ${VERTEX_LOCATION}"
echo "  Display name: ${DISPLAY_NAME}"
echo "  ADK CLI:      ${ADK_BIN}"
echo "  ADK object:   ${ADK_APP_OBJECT}"
echo "  MCP enabled:  ${MCP_ENABLED}"
echo "════════════════════════════════════════════════════"
echo ""

export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
export GOOGLE_CLOUD_LOCATION="${VERTEX_LOCATION}"
export MONGODB_MCP_ENABLED="${MCP_ENABLED}"

if [[ -z "${ENV_FILE}" ]]; then
    TEMP_ENV_FILE="$(mktemp)"
    chmod 600 "${TEMP_ENV_FILE}"
    {
        printf "GOOGLE_GENAI_USE_VERTEXAI=true\n"
        printf "GOOGLE_CLOUD_PROJECT=%s\n" "${PROJECT_ID}"
        printf "GOOGLE_CLOUD_LOCATION=%s\n" "${VERTEX_LOCATION}"
        printf "GEMINI_MODEL_PROFILE=%s\n" "${GEMINI_MODEL_PROFILE:-stable}"
        printf "GEMINI_ADK_MODEL=%s\n" "${GEMINI_ADK_MODEL:-gemini-3.5-flash}"
        printf "GEMINI_CHAT_MODEL=%s\n" "${GEMINI_CHAT_MODEL:-gemini-3.5-flash}"
        printf "GEMINI_REPORT_MODEL=%s\n" "${GEMINI_REPORT_MODEL:-gemini-3.5-flash}"
        printf "GEMINI_SENTIMENT_MODEL=%s\n" "${GEMINI_SENTIMENT_MODEL:-gemini-3.5-flash}"
        printf "ADK_ENABLED=true\n"
        printf "MONGODB_ENABLED=false\n"
        printf "MONGODB_DATABASE=%s\n" "${MONGODB_DATABASE:-vartovii}"
        printf "MONGODB_MCP_ENABLED=%s\n" "${MCP_ENABLED}"
    } > "${TEMP_ENV_FILE}"
    ENV_FILE="${TEMP_ENV_FILE}"
fi
trap '[[ -n "${TEMP_ENV_FILE}" ]] && rm -f "${TEMP_ENV_FILE}"' EXIT

cmd=(
    "${ADK_BIN}" deploy agent_engine
    --project "${PROJECT_ID}"
    --region "${REGION}"
    --display_name "${DISPLAY_NAME}"
    --description "${DESCRIPTION}"
    --requirements_file "${REQUIREMENTS_FILE}"
    --adk_app_object "${ADK_APP_OBJECT}"
)

cmd+=(--env_file "${ENV_FILE}")

cmd+=(agent)

"${cmd[@]}"
