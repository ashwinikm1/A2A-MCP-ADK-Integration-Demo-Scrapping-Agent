import streamlit as st
import asyncio
import httpx
import os
import logging
from uuid import uuid4
from typing import Any
from dotenv import load_dotenv

# A2A Client Library components
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)
from a2a.client import A2ACardResolver, A2AClient

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_agent_interaction(query: str) -> str:
    """
    Asynchronously interacts with the A2A agent to scrape a URL.
    """
    PUBLIC_AGENT_CARD_PATH = '/.well-known/agent.json'
    base_url = os.getenv('AGENT_REGISTRY_BASE_URL',
                         'https://search-agent-100889782425.us-central1.run.app')

    logger.info(f"Starting A2A client interaction with agent at: {base_url}")

    async with httpx.AsyncClient(timeout=300.0) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        final_agent_card_to_use: AgentCard | None = None

        try:
            public_card = await resolver.get_agent_card()
            logger.info("Successfully fetched public agent card.")
            final_agent_card_to_use = public_card
        except Exception as e:
            logger.error(
                f"Critical error fetching public agent card from {base_url}: {e}", exc_info=True)
            raise RuntimeError(
                "Failed to fetch the public agent card. Cannot continue.") from e

        client = A2AClient(httpx_client=httpx_client,
                           agent_card=final_agent_card_to_use)

        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': query}],
                'messageId': uuid4().hex,
            },
        }

        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )

        logger.info("Sending message to the agent...")
        response_record = await client.send_message(request)
        logger.info("Received response from the agent.")

        response_dict = response_record.model_dump(
            mode='json', exclude_none=True)

        agent_response_text = "No text content found in response or an error occurred."
        try:
            agent_response_text = response_dict['result']['status']['message']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing agent response structure: {e}")
            logger.error(f"Full response received: {response_dict}")

        return agent_response_text

# --- Streamlit UI ---
st.title("Multi-URL Scraper Agent")
st.write("Enter a URL below and click 'Scrape' to have the agent extract the content.")

url_input = st.text_input("URL to scrape", "https://medium.com/p/86a1735368e1")

if st.button("Scrape"):
    if url_input:
        with st.spinner("Scraping in progress..."):
            try:
                user_query = f"Scrape the title and first paragraph from this URL: {url_input}"
                result = asyncio.run(run_agent_interaction(user_query))
                st.success("Scraping complete!")
                st.text_area("Result", result, height=300)
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a URL.")
