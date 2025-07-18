import uvicorn
import os
import click
import logging

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

# Import your agent-specific logic
from agents.search_agent.task_manager import AgentTaskManager
# Not directly used but good to keep if it's the agent class itself
from agents.search_agent.agent import MultiURLBrowser

# -----------------------------------------------------------------------------
# Logging Setup
# Configure logging to display information and errors in the console.
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Main Entry Function - Configurable via Command-Line Interface (CLI)
# This function sets up and starts the agent server.
# -----------------------------------------------------------------------------


@click.command()
@click.option("--host", default=None, help="The host address to bind the server to. Overridden by environment for Cloud Run.")
@click.option("--port", default=None, type=int, help="The port for the server. Overridden by PORT env var for Cloud Run.")
@click.option("--public-url", default=None, help="Public URL of the agent. Overridden by PUBLIC_URL env var for Cloud Run.")
def main(host: str, port: int, public_url: str):
    """
    This function initializes and starts the A2A (Agent-to-Agent) server for the
    MultiURLBrowser agent. It's designed to be run from the command line.

    Example usage:
    `python -m agents.search_agent`
    """
    # For Cloud Run, the host must be 0.0.0.0 and the port is provided by
    # the 'PORT' environment variable.
    port = int(os.environ.get("PORT", port or 8080))
    # In a containerized environment like Cloud Run, listen on all available network interfaces.
    # For local development, default to 'localhost'.
    host = host or ("0.0.0.0" if "PORT" in os.environ else "localhost")

    # The agent's public URL is crucial for the Agent Card.
    # In Cloud Run, this URL is assigned on deployment. We pass it in via an
    # environment variable, 'PUBLIC_URL'.
    final_public_url = public_url or os.environ.get("PUBLIC_URL")
    if not final_public_url:
        # Fallback for local development if no public URL is provided
        final_public_url = f"http://{host}:{port}/"

    logger.info(
        f"Starting MultiURLBrowser Agent Server on http://{host}:{port}")
    logger.info(f"Agent Card URL will be set to: {final_public_url}")

    # Define the skill that this agent provides.
    # This information is used by directories and user interfaces to understand
    # what the agent can do.
    skill = AgentSkill(
        # A unique identifier for this skill.
        id="MultiURLBrowser",
        # A human-readable name for the skill.
        name="MultiURLBrowser_Agent",
        # A brief explanation of the skill's functionality.
        description="Agent to scrape content from the URLs specified by the user.",
        # Optional keywords for easier searching/categorization.
        tags=["multi-url", "browser", "scraper", "web"],
        examples=[
            "Scrape the URL: https://medium.com/@neeraj_agrawal/an-ai-travel-agent-in-action-a-detailed-look-at-how-two-agents-plan-a-trip-86a1735368e1",
            "Extract data from: https://www.example.com/page1 and https://www.example.com/page2"
        ]  # Example queries demonstrating how to use the skill.
    )

    # Create an Agent Card, which serves as a public identity and metadata
    # for this agent. It's crucial for agent discovery and interaction.
    agent_card = AgentCard(
        # The public name of the agent.
        name="MultiURLBrowser",
        # A detailed description.
        description="Agent designed to efficiently scrape specified content from multiple URLs or single URL provided by the user.",
        # The public URL where this agent can be accessed.
        url=final_public_url,
        # The current version of the agent.
        version="1.0.0",
        # Specifies the types of input this agent primarily accepts (e.g., text, image).
        defaultInputModes=['text'],
        # Specifies the types of output this agent primarily produces.
        defaultOutputModes=['text'],
        # Declares advanced capabilities like streaming responses.
        capabilities=AgentCapabilities(streaming=True),
        # A list of skills this agent offers.
        skills=[skill],
        # Indicates if the agent supports an authenticated extended card.
    )

    # Initialize the request handler for the agent server.
    # The DefaultRequestHandler bridges incoming requests to your agent's logic.
    request_handler = DefaultRequestHandler(
        # Your custom logic for executing agent tasks.
        agent_executor=AgentTaskManager(),
        # A simple in-memory store for managing task states.
        task_store=InMemoryTaskStore(),
        # For production, consider persistent storage.
    )

    # Create the A2A Starlette application.
    # This application acts as the web server, handling incoming HTTP requests
    # and routing them to the appropriate request handler.
    server = A2AStarletteApplication(
        agent_card=agent_card,  # The agent's identity and capabilities.
        # The component that processes incoming requests.
        http_handler=request_handler
    )

    # Start the server using Uvicorn.
    # uvicorn is an ASGI web server, recommended for production deployments
    # of Starlette applications.
    logger.info("Uvicorn server starting...")
    uvicorn.run(server.build(), host=host, port=port)


# -----------------------------------------------------------------------------
# Script Entry Point
# This ensures that the 'main()' function is called only when the script
# is executed directly (e.g., `python your_script.py`), not when imported
# as a module.
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
