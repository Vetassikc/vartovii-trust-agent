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

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${CLOUD_RUN_REGION:-europe-west1}"
SERVICE_NAME="vartovii-trust-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "════════════════════════════════════════════════════"
echo "  🛡️  Vartovii Trust Agent — Cloud Run Deploy"
echo "════════════════════════════════════════════════════"
echo "  Project:  ${PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  Service:  ${SERVICE_NAME}"
echo "  Image:    ${IMAGE_NAME}"
echo "════════════════════════════════════════════════════"
echo ""

# Step 1: Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
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
    --set-env-vars="GEMINI_MODEL_PROFILE=preview,ADK_ENABLED=true,MONGODB_ENABLED=true" \
    --quiet

# Step 4: Get the URL
echo ""
echo "════════════════════════════════════════════════════"
URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.url)")
echo "  ✅ Deployed successfully!"
echo "  🌐 URL: ${URL}"
echo ""
echo "  ⚠️  Don't forget to set secrets:"
echo "  gcloud run services update ${SERVICE_NAME} \\"
echo "    --region=${REGION} \\"
echo "    --set-env-vars=GOOGLE_API_KEY=your_key,MONGODB_CONNECTION_STRING=your_string"
echo "════════════════════════════════════════════════════"
