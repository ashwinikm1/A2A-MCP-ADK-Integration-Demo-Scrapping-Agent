# 🔍 Search Agent – A2A with Google ADK

This repository contains a demo of a Search Agent built with Google's Agent Development Kit (ADK), showcasing Agent2Agent (A2A) and Multi-Component Protocol (MCP) integration. The Search Agent is capable of scraping content from specified URLs.

This example demonstrates how to build, serve, and interact with a Search Agent capable of scraping content from specified URLs.

---

## 📦 Project Structure

This agent is located within the `agents/search_agent/` directory.

```bash
agents/
└── search_agent/
    ├── __main__.py         # Starts the Search Agent server
    ├── agent.py            # Gemini-based search agent logic
    ├── client.py           # Test client to interact with the agent
    └── task_manager.py     # In-memory task handler for the Search Agent
```

---

## 🛠️ Setup

This project likely shares setup steps with the main A2A demo. Please refer to the main `README.md` for detailed instructions on setting up the Python environment and installing dependencies.

You will also need to set up the necessary API keys in a `.env` file at the project root. If you don't have one, create it and add the following lines:

```bash
GOOGLE_API_KEY=------
FIRECRAWL_API_KEY=------
```

Ensure these keys are kept confidential and are not committed to version control. Replace `-----` and `----` with your actual keys.

---

## 🎬 Demo Walkthrough

Follow these steps to run and test the Search Agent:

1.  **Start the Search Agent Server**

    Open a terminal and run the following command from the project root directory:

    ```bash
    python3 -m agents.search_agent --host localhost --port 10000
    ```

    This will start the agent server, listening on `localhost` at port `10000`.

2.  **Test using the Test Client**

    Open a **new** terminal window (keep the server running in the first one) and run the client script:

    ```bash
    python3 agents/search_agent/client.py
    ```

    This script is configured to connect to `http://localhost:10000` by default and send a predefined query to the agent. You should see output in both the server terminal (indicating it received a request) and the client terminal (showing the agent's response).

    *Note: The client script currently attempts to connect to port 10000. If your server is running on a different port (like the default 10002 as instructed above), you may need to update the `base_url` variable in `agents/search_agent/client.py` to match the server's port for the client to connect successfully.*

3.  **Interacting via ADK Web**

    Once the Search Agent server is running (Step 1), you can also interact with it using the Google ADK web interface. This provides a graphical way to discover and communicate with your running agents.

    If your ADK web interface is configured to discover local agents, the Search Agent should automatically appear. You can then send queries to it directly from the web interface and observe the responses.

    Refer to the official [Google ADK documentation](https://github.com/google/agent-development-kit) for detailed instructions on setting up and using the ADK web interface.

---

## ☁️ Cloud Run Deployment (Search Agent)

This section explains how to deploy the Search Agent to Google Cloud Run.

1.  **Containerize the Agent**: The agent is containerized using the [`Dockerfile`](search_deploy_utils/Dockerfile) located in the `search_deploy_utils` directory. This Dockerfile sets up the Python environment, installs dependencies, and defines the entry point for the agent server.

2.  **Set up Configuration**: Before deploying, update the variables in [`search_deploy_utils/deploy.md`](search_deploy_utils/deploy.md) with your Google Cloud Project ID, desired region, and Artifact Registry repository name.

    ```markdown
    PROJECT_ID="your-gcp-project-id"
    REGION="your-gcp-region"
    REPO_NAME="your-artifact-registry-repo-name"
    ```

3.  **Create Artifact Registry Repository**: Create a Docker repository in Artifact Registry to store your container images. You only need to do this once per project/region/repo name.

    ```bash
    gcloud artifacts repositories create ${REPO_NAME} \
      --repository-format=docker \
      --location=${REGION} \
      --description="Docker repository for the multi-url browser agent"
    ```

4.  **Build and Push Docker Image**: Build the Docker image using the Dockerfile and push it to your Artifact Registry repository. Ensure you are in the project root directory when running this command.

    ```bash
    gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/multiurl-browser-agent
    ```

5.  **Deploy to Cloud Run**: Deploy the container image to Cloud Run. This will create a new Cloud Run service. Note the public URL provided after the deployment is complete.

    ```bash
    gcloud run deploy multiurl-browser-agent \
      --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/multiurl-browser-agent \
      --platform managed \
      --region ${REGION} \
      --allow-unauthenticated
    ```

6.  **Redeploy with Public URL**: Redeploy the Cloud Run service, setting the `PUBLIC_URL` environment variable to the URL obtained in the previous step. This allows the agent to know its own public address, which is necessary for some A2A functionalities.

    ```bash
    gcloud run deploy multiurl-browser-agent --image \
     ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/multiurl-browser-agent\
      --set-env-vars="PUBLIC_URL=https://your-cloud-run-url.run.app" \
      --region=${REGION} --platform=managed --allow-unauthenticated
    ```
    Replace `https://your-cloud-run-url.run.app` with the actual URL from the previous step.

---

## 🚀 Vertex AI Agent Engine Deployment (Scrap and Translate Agent)

This section explains how to deploy the Scrap and Translate agent using Vertex AI Agent Engine, as demonstrated in the [`deploy.py`](deploy.py) script.

1.  **Set up Configuration**: Ensure the following environment variables are set in your environment or a `.env` file:
    -   `GOOGLE_CLOUD_PROJECT`: Your Google Cloud Project ID.
    -   `GOOGLE_CLOUD_LOCATION`: The GCP region for deployment (e.g., `us-central1`).
    -   `STAGING_BUCKET_URI`: A Google Cloud Storage bucket URI for staging (e.g., `gs://your-staging-bucket`).

2.  **Initialize Vertex AI SDK**: The [`deploy.py`](deploy.py) script initializes the Vertex AI SDK with your project, location, and staging bucket.

    ```python
    vertexai.init(
        project=GCP_PROJECT_ID,
        location=GCP_LOCATION,
        staging_bucket=STAGING_BUCKET_URI
    )
    ```

3.  **Define Dependencies**: The script specifies the required PyPI packages that the Agent Engine service needs to install for your agent to run.

    ```python
    requirements = [
        "google-cloud-aiplatform[reasoningengine,adk]",
        "httpx",
        "python-dotenv",
        "a2a-sdk",
    ]
    ```

4.  **Wrap Agent with AdkApp**: The core agent logic (`root_agent` from `scrap_translate.agent`) is wrapped using `reasoning_engines.AdkApp()`. This makes the agent compatible with the Agent Engine deployment framework.

    ```python
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )
    ```

5.  **Create Remote Agent Engine**: The wrapped agent (`app`) is deployed to Vertex AI Agent Engine using `agent_engines.create()`. This command handles the packaging, uploading, and deployment of your agent to a managed service.

    ```python
    remote_agent = agent_engines.create(
        app,
        requirements=["google-cloud-aiplatform[agent_engines,adk]", "a2a-sdk"],
        extra_packages=["scrap_translate"]
    )
    ```
    The `requirements` and `extra_packages` parameters ensure that necessary dependencies and your agent's code are included in the deployment.

6.  **Run the Deployment Script**: Execute the [`deploy.py`](deploy.py) script to perform the deployment.

    ```bash
    python deploy.py
    ```
    Upon successful execution, the script will output information about the deployed `remote_agent` object.

---

## 📖 Learn More

-   A2A GitHub: https://github.com/google/A2A
-   Google ADK: https://github.com/google/agent-development-kit
