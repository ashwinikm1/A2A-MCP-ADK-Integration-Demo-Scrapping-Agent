# agent.py
from a2a.client import A2AClient
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
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)

load_dotenv()
logger = logging.getLogger(__name__)


AGENT_REGISTRY_BASE_URL = "http://localhost:10000"

# Extracted list_agents function


async def list_agents() -> list[dict]:
    """
    Fetch all AgentCard metadata from the registry,
    return as a list of plain dicts.
    """
    async with httpx.AsyncClient() as client:
        url = AGENT_REGISTRY_BASE_URL.rstrip("/") + "/.well-known/agent.json"
        response = await client.get(url, timeout=50.0)
    cards_data = response.json()
    print(f"Fetched {len(cards_data)} agents from registry at {url}")
    print(f"Agent data: {cards_data}")
    return cards_data

# Extracted call_agent function


async def call_agent(agent_name: str, message: str) -> str:
    """
    Given an agent_name string and a user message,
    find that agent’s URL, send the task, and return its reply.
    """
    cards = await list_agents()  # Use the module-level list_agents

    client = A2AClient(httpx_client=httpx.AsyncClient(timeout=3000),
                       url=AGENT_REGISTRY_BASE_URL)

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
    model="gemini-2.5-pro-preview-03-25",
    name="root_orchestrator",
    description="Discovers and orchestrates other agents",
    instruction=system_instr,
    tools=[
        FunctionTool(list_agents),
        FunctionTool(call_agent),
    ],
)

# Create the Runner instance directly
runner = Runner(
    app_name=root_agent.name,
    agent=root_agent,
    artifact_service=InMemoryArtifactService(),
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
)

# Main execution logic using the Runner


async def main():
    user_id = "test_user"  # Use a different user_id for the main execution example
    session_id = "test_session_123"
    query = "List the available agents."  # Example query

    print(f"Running query: '{query}'")

    # Wrap the user’s text in a Gemini Content object
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

    if last_event and last_event.content and last_event.content.parts:
        response_text = "\n".join(
            [p.text for p in last_event.content.parts if p.text])
        print(f"Agent Response:\n{response_text}")
    else:
        print("No response received.")

    user_id = "test_user"  # Use a different user_id for the main execution example
    session_id = "test_session_123"
    query = "List the available agents."  # Example query for the orchestrator.

    print(f"Running query: '{query}'")

    # Wrap the user’s text in a Gemini Content object
    # This prepares the user's query in a format suitable for the LLM.
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=query)]
    )

    last_event = None
    # Run the agent asynchronously and iterate through the events it generates.
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
