# =============================================================================
# a2a_client_example.py
# =============================================================================
# 🎯 Purpose:
# This script demonstrates how to interact with an A2A (Agent-to-Agent)
# compatible agent server using the A2A Python client library.
# It covers fetching the agent's capabilities (Agent Card) and sending
# a text message to it, then printing the agent's response.
# =============================================================================

# -----------------------------------------------------------------------------
# 📦 Essential Imports
# -----------------------------------------------------------------------------
from a2a.types import (
    AgentCard,           # Represents an agent's metadata and capabilities
    MessageSendParams,   # Parameters for sending a message
    SendMessageRequest,  # The request object for sending a non-streaming message
)
from a2a.client import A2ACardResolver, A2AClient
import logging         # For logging information and debugging
import os              # For environment variables
from typing import Any  # For type hints (e.g., dictionary content)
from uuid import uuid4  # For generating unique IDs
import httpx           # An asynchronous HTTP client for making requests

# Environment variable loading for configuration
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env file

# A2A Client Library components

# -----------------------------------------------------------------------------
# 🪵 Logging Setup
# Configure logging to display INFO level messages and above in the console.
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Get a logger instance for this module

# -----------------------------------------------------------------------------
# 🚀 Main Asynchronous Function
# This function orchestrates the client's interaction with the A2A agent.
# -----------------------------------------------------------------------------


async def main() -> None:
    """
    Main asynchronous function to run the A2A client example.
    It performs the following steps:
    1. Initializes an HTTP client.
    2. Resolves the agent's public Agent Card.
    3. Initializes the A2A client with the resolved Agent Card.
    4. Constructs and sends a message to the agent.
    5. Prints the agent's response.
    """
    # Define the standard path where an A2A agent's public card is exposed.
    PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'

    # The base URL of the A2A agent server we want to connect to.
    # Make sure your agent server (e.g., from the previous code) is running on this address.
    # Get from environment variable with fallback to default
    base_url = os.getenv('AGENT_REGISTRY_BASE_URL',
                         'https://search-agent-100889782425.us-central1.run.app')

    logger.info(f"Starting A2A client interaction with agent at: {base_url}")

    # Use httpx.AsyncClient for making asynchronous HTTP requests.
    # The 'timeout' is crucial for long-running agent operations.
    # Increased timeout for potentially long agent tasks
    async with httpx.AsyncClient(timeout=300.0) as httpx_client:
        # ---------------------------------------------------------------------
        # 1. Resolve Agent Card: Discover the agent's capabilities
        # ---------------------------------------------------------------------
        logger.info("Initializing A2ACardResolver to fetch agent capabilities.")
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
            # agent_card_path and extended_agent_card_path use defaults if not specified
        )

        final_agent_card_to_use: AgentCard | None = None

        try:
            logger.info(
                f"Attempting to fetch public agent card from: {base_url}{PUBLIC_AGENT_CARD_PATH}"
            )
            # Fetches the AgentCard from the standard public path.
            public_card = await resolver.get_agent_card()
            logger.info("Successfully fetched public agent card:")
            logger.info(
                public_card.model_dump_json(indent=2, exclude_none=True)
            )
            final_agent_card_to_use = public_card
            logger.info(
                "Using PUBLIC agent card for A2AClient initialization.")

        except Exception as e:
            logger.error(
                f"Critical error fetching public agent card from {base_url}: {e}",
                exc_info=True  # This prints the full traceback, very helpful for debugging
            )
            raise RuntimeError(
                "Failed to fetch the public agent card. Cannot continue."
            ) from e

        # ---------------------------------------------------------------------
        # 2. Initialize A2AClient: Set up to communicate with the agent
        # ---------------------------------------------------------------------
        logger.info("Initializing A2AClient with the fetched Agent Card.")
        client = A2AClient(
            httpx_client=httpx_client, agent_card=final_agent_card_to_use
        )

        # ---------------------------------------------------------------------
        # 3. Construct and Send Message: Define the user's query
        # ---------------------------------------------------------------------
        # The content of the message you want to send to the agent.
        # This example uses a query for the MultiURLBrowser agent.
        user_query = (
            "Scrape the title and first paragraph from this URL: https://medium.com/p/86a1735368e1"
        )
        logger.info(
            f"Preparing to send message to agent: '{user_query[:70]}...'")

        send_message_payload: dict[str, Any] = {
            'message': {
                # The role of the sender (e.g., 'user', 'agent')
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': user_query}
                ],
                'messageId': uuid4().hex,  # A unique ID for this specific message
            },
        }

        # Create the SendMessageRequest object using the payload.
        request = SendMessageRequest(
            id=str(uuid4()),  # A unique ID for the request itself
            params=MessageSendParams(**send_message_payload)
        )

        # Send the message to the agent and await its response.
        logger.info("Sending message to the agent...")
        response_record = await client.send_message(request)
        logger.info("Received response from the agent.")

        # ---------------------------------------------------------------------
        # 4. Process and Print Response: Extract the agent's answer
        # ---------------------------------------------------------------------
        # Convert the Pydantic response object to a dictionary (useful for inspection).
        response_dict = response_record.model_dump(
            mode='json', exclude_none=True
        )

        agent_response_text = "No text content found in response or an error occurred."
        try:
            # Directly access the text part, assuming the structure for a successful
            # completed task is guaranteed. The try-except block will catch
            # KeyError or IndexError if the structure is unexpected.
            agent_response_text = response_dict['result']['status']['message']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing agent response structure: {e}")
            logger.error(f"Full response received: {response_dict}")
            # The agent_response_text will remain the default "No text content..." message.

        logger.info("\n--- Agent's Final Response ---")
        # Print to stdout for easy visibility of the actual response
        print(agent_response_text)
        logger.info("----------------------------")

# -----------------------------------------------------------------------------
# Main execution block
# This ensures that the 'main()' async function is run when the script
# is executed directly.
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
