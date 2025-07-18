# deploy.py

import os

import vertexai

from dotenv import load_dotenv

from scrap_translate.agent import root_agent

import sys
import cloudpickle
from vertexai.preview import reasoning_engines
from vertexai import agent_engines


# Load environment variables from .env file for local execution of this script
load_dotenv()


# --- Configuration ---
# Replace with your real values, or set them in a .env file.
GCP_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
# e.g., "gs://your-gcs-staging-bucket"
STAGING_BUCKET_URI = os.getenv("STAGING_BUCKET_URI")
AGENT_DISPLAY_NAME = "Scrap and Translate Agent"
AGENT_DESCRIPTION = "An agent that can list and call other agents to perform tasks."


# Check if required environment variables are set
if not all([GCP_PROJECT_ID, GCP_LOCATION, STAGING_BUCKET_URI]):
    raise ValueError(
        "Please set GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, and STAGING_BUCKET_URI "
        "in your environment or a .env file."
    )

# --- 1. Initialize Vertex AI SDK ---
# Initialize the Vertex AI SDK with your project, location, and staging bucket
vertexai.init(
    project=GCP_PROJECT_ID,
    location=GCP_LOCATION,
    staging_bucket=STAGING_BUCKET_URI
)


# --- 2. Define Deployment Configuration ---
# List of PyPI packages required by your agent.
# The Reasoning Engine service will install these dependencies.
requirements = [
    # google-cloud-aiplatform with reasoningengine and adk extras is needed
    "google-cloud-aiplatform[reasoningengine,adk]",
    "httpx",
    "python-dotenv",
    "a2a-sdk",  # Based on your agent's imports
]


# --- 3. Wrap Agent with AdkApp ---
# Use reasoning_engines.AdkApp() to wrap your agent to make it deployable to Agent Engine
app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

# --- 4. Create Remote Agent Engine ---
# Deploy the wrapped agent to Vertex AI Agent Engine
remote_agent = agent_engines.create(
    app,
    requirements=["google-cloud-aiplatform[agent_engines,adk]", "a2a-sdk"],
    extra_packages=["scrap_translate"]
)

# The remote_agent object can now be used to interact with the deployed agent.
# Example usage (commented out as this script is for deployment, not interaction):
# for event in remote_agent.stream_query(
#     user_id="user_123",
#     message="Summarize the following BLOG URL : https://medium.com/google-cloud/the-agent-advantage-why-smart-ai-is-better-than-simple-bots-and-how-to-know-whats-real-62bebc28a0e6"
# ):
#     print(event)

print(f"Agent deployed successfully. Remote agent object: {remote_agent}")
