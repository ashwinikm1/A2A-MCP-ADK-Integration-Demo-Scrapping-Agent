# =============================================================================
# agents/search_agent/agent.py
# =============================================================================
# 🎯 Purpose:
# This file defines the MultiURLBrowser agent.
# It leverages Google's ADK (Agent Development Kit) and a Gemini model
# to intelligently scrape content from multiple URLs, acting as a smart browser.
# =============================================================================

# -----------------------------------------------------------------------------
# 📦 Essential Imports
# -----------------------------------------------------------------------------
import os
from collections.abc import AsyncIterable # For asynchronous generators

# Google ADK (Agent Development Kit) core components
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.genai import types # For Gemini content types

# Tools for the agent to interact with external services
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Environment variable loading for API keys (crucial for security)
from dotenv import load_dotenv
load_dotenv() # Load variables like FIRECRAWL_API_KEY from your .env file

# -----------------------------------------------------------------------------
# 🪵 Logging Setup
# Configure logging to display information and errors in the console.
# -----------------------------------------------------------------------------
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 🧠 MultiURLBrowser: Your AI Agent for Web Scraping
# -----------------------------------------------------------------------------

class MultiURLBrowser:
    """
    This agent specializes in crawling and extracting information from
    multiple URLs provided by the user. It uses a Gemini-powered LLM
    and integrates with the FireCrawl tool for web content extraction.
    """
    # This agent is designed to handle and produce plain text content.
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        """
        👷 Initializes the MultiURLBrowser Agent.
        This setup involves:
        - Building the core LLM agent (powered by Gemini).
        - Configuring session management, memory, and the ADK Runner
          to orchestrate agent execution.
        """
        # Set up the Gemini-based agent with its specific tools.
        self._agent = self._build_agent()
        # Use a consistent user ID for managing sessions within this agent.
        self._user_id = "multiurlbrowser_agent_user"

        # The Runner orchestrates the agent's environment, handling
        # sessions, memory, and artifacts.
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(), # Used for file-like data (not directly in this example)
            session_service=InMemorySessionService(),    # Manages conversational state between interactions.
            memory_service=InMemoryMemoryService(),      # Stores past messages for contextual understanding.
        )

    def _build_agent(self) -> LlmAgent:
        """
        ⚙️ Configures and returns an `LlmAgent` instance.
        This is where you define the LLM model, its instructions, and the
        external tools it can use.

        Returns:
            LlmAgent: An initialized agent object from Google's ADK.
        """
        # Retrieve the Firecrawl API key from environment variables.
        # It's vital to set FIRECRAWL_API_KEY in your .env file or environment.
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        if not firecrawl_api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable not set. Please set it in your .env file.")

        return LlmAgent(
            model="gemini-2.5-pro-preview-03-25", # Specifies the Gemini model version to use.
            name="MultiURLBrowserAgent",          # A descriptive name for the agent.
            description="Assists users by intelligently crawling and extracting information from multiple specified URLs.",
            instruction="You are an expert web crawler. Your primary task is to extract content from URLs provided by the user. Use the available tools to fetch content from the web. Respond with the extracted content or a summary as requested.", # System prompt guiding the agent's behavior.
            tools=[
                MCPToolset( # Multi-Component Protocol Toolset for integrating external services.
                    connection_params=StdioServerParameters(
                        command='npx',
                        # Arguments to run the FireCrawl MCP tool via npx.
                        args=["-y", "firecrawl-mcp"],
                        # Pass the API key as an environment variable to the npx process.
                        # This is how the FireCrawl MCP server expects to receive the key.
                        env={
                            "FIRECRAWL_API_KEY": "fc-e6aad8663d2c432facc1d20db42f76df"
                        }
                    ),
                    # You can filter for specific tools within the toolset if needed.
                    # Example: tool_filter=['crawl', 'scrape_url'] if FireCrawl offered distinct tools.
                )
            ]
        )

    async def invoke(self, query: str, session_id: str) -> AsyncIterable[dict]:
        """
        Receives a user query and processes it using the agent.
        This method is an asynchronous generator, allowing it to stream
        updates back to the caller as the agent processes the request.

        Args:
            query (str): The user's input query, typically containing URLs to scrape.
            session_id (str): A unique identifier for the current conversation session.

        Yields:
            dict: A dictionary containing progress updates or the final response.
                  - {'is_task_complete': False, 'updates': str} for progress.
                  - {'is_task_complete': True, 'content': str} for the final result.
        """
        logger.info(f"Received query for session {session_id}: {query[:100]}...") # Log beginning of query

        # 1. Attempt to retrieve an existing session to maintain conversation context.
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )

        # 2. If no session is found, create a new one.
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id,
                state={}, # Optionally, prefill memory or state here for new sessions.
            )
            logger.info(f"Created new session {session_id}.")

        # 3. Wrap the user's text query into a Gemini `Content` object.
        user_content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )

        # 🚀 Execute the agent's run cycle and stream events.
        # The `run_async` method yields events as the agent thinks and responds.
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=user_content
        ):
            if event.is_final_response():
                # When the agent provides a final answer.
                response_text = ""
                # Check if the last part of the content is text.
                if event.content and event.content.parts and event.content.parts[-1].text:
                    response_text = event.content.parts[-1].text

                logger.info(f"Final response for session {session_id}.")
                yield {
                    'is_task_complete': True,
                    'content': response_text,
                }
            else:
                # Provide intermediate updates to the caller.
                # You could refine this to give more specific updates based on `event.type`.
                yield {
                    'is_task_complete': False,
                    'updates': "Processing the web crawling request...",
                }
                                
 