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

## 📖 Learn More

-   A2A GitHub: https://github.com/google/A2A
-   Google ADK: https://github.com/google/agent-development-kit
