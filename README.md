# 🔍 Search Agent – A2A with Google ADK

This repository contains a demo of a Search Agent built with Google's Agent Development Kit (ADK), showcasing Agent2Agent (A2A) and Multi-Component Protocol (MCP) integration. The Search Agent is capable of scraping content from specified URLs. Additionally, it includes an orchestrator agent that demonstrates agent-to-agent communication.

This example demonstrates how to build, serve, and interact with a Search Agent capable of scraping content from specified URLs, as well as how to create orchestrator agents that can call other agents via the A2A protocol.

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

scrap_translate/
├── __init__.py             # Package initialization
└── agent.py                # Orchestrator agent that calls other agents via A2A
```

---

## 🛠️ Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### 1. Create Virtual Environment

Create and activate a Python virtual environment to isolate project dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

1. **Create your environment file** by copying the provided template:
   ```bash
   cp env.example .env
   ```

2. **Edit the `.env` file** and fill in your actual API keys:
   - **`GOOGLE_API_KEY`** - Get this from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - **`FIRECRAWL_API_KEY`** - Get this from [FireCrawl](https://www.firecrawl.dev/)

3. **Optional configurations** (already have sensible defaults):
   - `GOOGLE_MODEL_NAME` - Gemini model to use (default: `gemini-2.5-pro-preview-03-25`)
   - `AGENT_REGISTRY_BASE_URL` - URL for agent discovery (default: `http://localhost:10000`)

⚠️ **Important**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

---

## 🎬 Demo Walkthrough

Follow these steps to run and test the Search Agent:

1.  **Start the Search Agent Server**

    Open a terminal and run the following command from the project root directory:

    ```bash
    python3 -m agents.search_agent --host localhost --port 10000
    ```

    This will start the agent server, listening on `localhost` at port `10000` (the default port).

2.  **Test using the Test Client**

    Open a **new** terminal window (keep the server running in the first one) and run the client script:

    ```bash
    python3 agents/search_agent/client.py
    ```

    This script is configured to connect to `http://localhost:10000` by default and send a predefined query to the agent. You should see output in both the server terminal (indicating it received a request) and the client terminal (showing the agent's response).

3.  **Agent-to-Agent Communication via ADK Web Interface**

    Now let's demonstrate how agents can call other agents using the A2A protocol. We'll use the ADK web interface to interact with the orchestrator agent (`scrap_translate`) which can then call our search agent.

    **Run the ADK Web Interface:**
    ```bash
    adk web
    ```
    
    This will open a web interface where you can select the **`scrap_translate` agent** from the available agents list and interact with it.

    This orchestrator agent can discover and call other A2A agents, including our search agent. It demonstrates:
    - **Agent discovery**: Finding available agents on the network
    - **Agent-to-agent communication**: Calling specialized agents as tools
    - **Collaborative workflows**: Breaking complex tasks into agent-specific subtasks

    The orchestrator will automatically discover your running search agent and can delegate web scraping tasks to it, showcasing the power of the A2A framework for building collaborative AI systems.

    Refer to the official [Google ADK documentation](https://github.com/google/agent-development-kit) for detailed instructions on setting up and using the ADK web interface.

---

## 📖 Learn More

-   A2A GitHub: https://github.com/google/A2A
-   Google ADK: https://github.com/google/agent-development-kit
