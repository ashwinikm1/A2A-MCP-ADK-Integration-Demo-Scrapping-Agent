export PROJECT_ID="alpha-code-461805"
export REGION="us-central1"
export REPO_NAME="muti-url-browser-agentv2"

## ---------------------------------------------------------------------------
## Step 1: Create an Artifact Registry repository (one-time setup)
## ---------------------------------------------------------------------------
## This command creates a Docker repository. If you see an "ALREADY_EXISTS"
## error on subsequent runs, that is expected. You can safely ignore it and proceed.
## You can reuse this repository for other agent images as well.
gcloud artifacts repositories create ${REPO_NAME} \
  --repository-format=docker \
  --location=${REGION} \
  --description="Docker repository for the multi-url browser agent"

## ---------------------------------------------------------------------------
## Step 2: Build and push the container image to the new repository
## ---------------------------------------------------------------------------
gcloud builds submit . --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/search-agent

## ---------------------------------------------------------------------------
## Step 3: Deploy the image to Cloud Run and set the public URL
## ---------------------------------------------------------------------------

gcloud run deploy search-agent \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/search-agent \
  --platform managed \
  --region ${REGION} \
  --port 8080 \
  --allow-unauthenticated 

echo "Retrieving service URL..."
SERVICE_URL=$(gcloud run services describe search-agent --platform managed --region ${REGION} --format 'value(status.url)')

if [ -z "$SERVICE_URL" ]; then
    echo "Error: Could not retrieve service URL. Please check the deployment in the GCP console."
    exit 1
fi

echo "Service URL found: ${SERVICE_URL}"
echo "Updating service with PUBLIC_URL..."

gcloud run services update search-agent \
  --platform managed \
  --region ${REGION} \
  --update-env-vars="PUBLIC_URL=${SERVICE_URL}"

echo "Deployment and configuration complete."