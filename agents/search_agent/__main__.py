import uvicorn
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
from agents.search_agent.agent import MultiURLBrowser # Not directly used but good to keep if it's the agent class itself

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
@click.option("--host", default="localhost", help="The host address to bind the server to. Default is 'localhost'.")
@click.option("--port", default=10002, type=int, help="The port number for the server to listen on. Default is 10002.")
def main(host: str, port: int):
    """
    This function initializes and starts the A2A (Agent-to-Agent) server for the
    MultiURLBrowser agent. It's designed to be run from the command line.

    Example usage:
    `python -m agents.google_adk --host 0.0.0.0 --port 12345`
    (Note: The module path 'agents.google_adk' should be updated to your actual
    script's module path, e.g., 'your_project.your_script_name' if this
    is saved as a script.)
    """
    logger.info(f"Starting MultiURLBrowser Agent Server on http://{host}:{port}")

    # Define the skill that this agent provides.
    # This information is used by directories and user interfaces to understand
    # what the agent can do.
    skill = AgentSkill(
        id="MultiURLBrowser",                                 # A unique identifier for this skill.
        name="MultiURLBrowser_Agent",                         # A human-readable name for the skill.
        description="Agent to scrape content from the URLs specified by the user.", # A brief explanation of the skill's functionality.
        tags=["multi-url", "browser", "scraper", "web"],      # Optional keywords for easier searching/categorization.
        examples=[
            "Scrape the URL: https://medium.com/@neeraj_agrawal/an-ai-travel-agent-in-action-a-detailed-look-at-how-two-agents-plan-a-trip-86a1735368e1",
            "Extract data from: https://www.example.com/page1 and https://www.example.com/page2"
        ]  # Example queries demonstrating how to use the skill.
    )

    # Create an Agent Card, which serves as a public identity and metadata
    # for this agent. It's crucial for agent discovery and interaction.
    agent_card = AgentCard(
        name="MultiURLBrowser",                               # The public name of the agent.
        description="Agent designed to efficiently scrape specified content from multiple URLs or single URL provided by the user.", # A detailed description.
        url=f"http://{host}:{port}/",                         # The public URL where this agent can be accessed.
        version="1.0.0",                                      # The current version of the agent.
        defaultInputModes=['text'],                           # Specifies the types of input this agent primarily accepts (e.g., text, image).
        defaultOutputModes=['text'],                          # Specifies the types of output this agent primarily produces.
        capabilities=AgentCapabilities(streaming=True),       # Declares advanced capabilities like streaming responses.
        skills=[skill],                                       # A list of skills this agent offers.
        supportsAuthenticatedExtendedCard=True,               # Indicates if the agent supports an authenticated extended card.
    )

    # Initialize the request handler for the agent server.
    # The DefaultRequestHandler bridges incoming requests to your agent's logic.
    request_handler = DefaultRequestHandler(
        agent_executor=AgentTaskManager(),  # Your custom logic for executing agent tasks.
        task_store=InMemoryTaskStore(),     # A simple in-memory store for managing task states.
                                            # For production, consider persistent storage.
    )

    # Create the A2A Starlette application.
    # This application acts as the web server, handling incoming HTTP requests
    # and routing them to the appropriate request handler.
    server = A2AStarletteApplication(
        agent_card=agent_card,  # The agent's identity and capabilities.
        http_handler=request_handler # The component that processes incoming requests.
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