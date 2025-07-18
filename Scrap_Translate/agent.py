# agent.py
import os
from a2a.client import A2AClient, A2ACardResolver
import logging
from uuid import uuid4
from google.adk.tools.function_tool import FunctionTool
from google.genai import types
from google.adk.runners import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.agents.llm_agent import LlmAgent
import httpx
from dotenv import load_dotenv
from a2a.types import (
    AgentCard
)
import logging

from a2a.types import (
    AgentCard,
    SendMessageRequest,
)

load_dotenv()
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)


# Retrieve the Google model name from environment variables with a default fallback.
model_name = os.getenv("GOOGLE_MODEL_NAME", "gemini-2.5-pro")

# Retrieve the A2A agent registry base URL from environment variables with a default fallback.
AGENT_REGISTRY_BASE_URL = os.getenv(
    "AGENT_REGISTRY_BASE_URL", "https://search-agent-100889782425.us-central1.run.app/")

# Extracted list_agents function


async def list_agents() -> list[dict]:
    """
    Fetch all AgentCard metadata from the registry,
    return as a list of plain dicts.
    """
    async with httpx.AsyncClient() as httpx_client:
        base_url = AGENT_REGISTRY_BASE_URL.rstrip("/")
        # response = await client.get(url, timeout=50.0)

        logger.info("Initializing A2ACardResolver to fetch agent capabilities.")
        resolver = A2ACardResolver(
            httpx_client=httpx.AsyncClient(timeout=3000),
            base_url=base_url,
            # agent_card_path and extended_agent_card_path use defaults if not specified
        )
        final_agent_card_to_use: AgentCard | None = None

        try:
            logger.info(
                f"Attempting to fetch public agent card from: {base_url}"
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

        cards_data = final_agent_card_to_use
        # Assuming AgentCard has a 'name' attribute, print the name instead of length
        print(f"Fetched agent '{cards_data.name}' from registry at {base_url}")
        print(f"Agent data: {cards_data}")
        return cards_data

# Extracted call_agent function


async def call_agent(agent_name: str, message: str) -> str:
    """
    Given an agent_name string and a user message,
    find that agent's URL, send the task, and return its reply.
    """
    cards = await list_agents()  # Use the module-level list_agents

    client = A2AClient(httpx_client=httpx.AsyncClient(timeout=3000),
                       agent_card=cards)

    print("Connected to A2AClient at", AGENT_REGISTRY_BASE_URL)
    session_id = "transalation_session"
    # Find the agent card by name
    task_id = uuid4().hex

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": message
                    }
                ],
                "messageId": uuid4().hex
            },
            "metadata": {}
        }
    }

    # Using user_id as session_id for simplicity as in original code

    response_rec = await client.send_message(SendMessageRequest(**payload))
    # print("Response from send_message:", reasponse_rec.model_dump(
    #     mode='json', exclude_none=True))

    print("Response from send_message:", response_rec)

    response = response_rec.model_dump(mode='json', exclude_none=True)
    # print("Formatted Response:", response)
    # print("parse", response['result']['status']['message']['parts'][0]['text'])
    return (response['result']['status']['message']['parts'][0]['text'])

# System instruction for the LLM
system_instr = (
    "You are a root orchestrator agent. You have two tools:\n"
    "1) list_agents() → Use this tool to see a list of all available agents and their capabilities.\n"
    "2) call_agent(agent_name: str, message: str) → Use this tool to send a message to a specific agent by its name and get its response.\n"
    "Use these tools to fulfill user requests by discovering and interacting with other agents as needed.\n"
)

# Create the LlmAgent instance directly
root_agent = LlmAgent(
    model=model_name,
    name="root_orchestrator",
    description="Discovers and orchestrates other agents",
    instruction=system_instr,
    tools=[
        FunctionTool(list_agents),
        FunctionTool(call_agent),
    ],
)

# Main execution logic using the Runner


async def main():
    # This main function is for local testing and is not used for deployment.
    runner = Runner(
        app_name=root_agent.name,
        agent=root_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

    user_id = "test_user"  # Use a different user_id for the main execution example
    session_id = "test_session_123"
    query = "List the available agents."  # Example query

    print(f"Running query: '{query}'")

    # Wrap the user's text in a Gemini Content object
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=query)]
    )

    last_event = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        last_event = event
        # Optional: print events as they happen
        # print(f"Event: {event}")

    # After the agent has finished processing, extract and print the final response.
    if last_event and last_event.content and last_event.content.parts:
        response_text = "\n".join(
            [p.text for p in last_event.content.parts if p.text])
        print(f"Agent Response:\n{response_text}")
    else:
        print("No response received.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
