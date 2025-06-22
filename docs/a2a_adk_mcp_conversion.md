# Converting an ADK Agent with MCP to A2A Compatibility: The Tale of the MultiURLBrowser Agent

This document tells the story of how the `MultiURLBrowser` agent, originally built using the Google Agent Development Kit (ADK) and relying on an MCP (Model Context Protocol) server tool (like FireCrawl) for its web-scraping prowess, was transformed to become compatible with the A2A (Agent-to-Agent) framework. We will use the provided code from the `agents/search_agent/` directory as our guide, exploring the key components that enabled this transformation: the Agent Definition, Agent Skill, Agent Card, the crucial `invoke` method, the diligent Task Manager, and how other agents or clients can interact with it.

Our hero, the `MultiURLBrowser`, is a specialized agent with a singular mission: to intelligently navigate the vast web and extract valuable content from multiple URLs provided by its users. It achieves this by leveraging the power of a Gemini model and integrating with the FireCrawl MCP tool, which acts as its trusty web-crawling sidekick.

## Project Structure: The Agent's Workshop

The essential components of the `MultiURLBrowser` agent's A2A-compatible form are found within its workshop, the `agents/search_agent/` directory:

```
agents/search_agent/
├── __main__.py
├── agent.py
├── client.py
└── task_manager.py
```

-   [`__main__.py`](agents/search_agent/__main__.py): This is the agent's public facade, defining its identity (Agent Card) and what it's capable of (Agent Skill). It's also the entry point for starting the A2A server that hosts our agent.
-   [`agent.py`](agents/search_agent/agent.py): This file contains the very heart of the `MultiURLBrowser` – its core logic. Here, it's defined, initialized, and its `invoke` method orchestrates the interaction with the ADK runner and its MCP tool.
-   [`task_manager.py`](agents/search_agent/task_manager.py): The diligent manager of the agent's tasks. It acts as the bridge between the A2A server framework and the specific instructions given to the `MultiURLBrowser`, ensuring tasks are handled efficiently and updates are reported.
-   [`client.py`](agents/search_agent/client.py): A helpful guide for anyone wanting to interact with the `MultiURLBrowser`, demonstrating how to connect, understand its capabilities, and send it a web-scraping mission.

## 1. The Agent's Core: Defining the MultiURLBrowser (`agent.py`)

The soul of our agent, the `MultiURLBrowser` class, resides within [`agent.py`](agents/search_agent/agent.py). This is where its fundamental abilities are defined, wrapping the power of the ADK `LlmAgent` and configuring its connection to the outside world via the MCP tool.

```python
# agents/search_agent/agent.py
# ... imports ...

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
                            "FIRECRAWL_API_KEY": "-----" # Replace with actual key or env var
                        }
                    ),
                    # You can filter for specific tools within the toolset if needed.
                    # Example: tool_filter=['crawl', 'scrape_url'] if FireCrawl offered distinct tools.
                )
            ]
        )
# ... invoke method below ...
```

Within the `__init__` method, the `MultiURLBrowser` prepares itself by building its core ADK `LlmAgent`. The `_build_agent` method is where the magic happens: it selects the powerful Gemini model as its brain, sets its core directive ("You are an expert web crawler..."), and crucially, equips itself with the `MCPToolset`. This toolset is configured to launch the `firecrawl-mcp` command, effectively giving our agent the ability to delegate the complex task of web scraping to its specialized MCP sidekick. This is the foundation of its web-browsing capability.

## 2. Declaring Expertise: The Agent Skill (`__main__.py`)

For other agents and systems to understand what the `MultiURLBrowser` can do, it needs to clearly declare its expertise. This is done through the `AgentSkill` definition in its public-facing file, [`__main__.py`](agents/search_agent/__main__.py).

```python
# agents/search_agent/__main__.py
# ... imports ...

def main(host: str, port: int):
    """
    This function initializes and starts the A2A (Agent-to-Agent) server for the
    MultiURLBrowser agent. It's designed to be run from the command line.
    """
    # ... logging ...

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

    # ... Agent Card and server setup below ...
```

The `AgentSkill` object is like the agent's resume. It lists its unique `id`, a friendly `name`, a concise `description` of its web-scraping ability, relevant `tags` for easy discovery, and practical `examples` of how to give it instructions. This allows other agents or users to quickly understand if the `MultiURLBrowser` is the right tool for their web-scraping needs.

## 3. The Agent's Identity Card: The Agent Card (`__main__.py`)

Beyond just its skills, the `MultiURLBrowser` needs a public identity within the A2A network. This is provided by the `AgentCard` in [`__main__.py`](agents/search_agent/__main__.py), which acts as its official passport and metadata.

```python
# agents/search_agent/__main__.py
# ... imports and skill definition ...

def main(host: str, port: int):
    # ... logging and skill definition ...

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

    # ... request handler and server setup below ...
```

The `AgentCard` is the `MultiURLBrowser`'s public profile. It includes its official `name`, a more detailed `description` of its purpose, the `url` where it can be found, its current `version`, and information about the types of input and output it handles. Crucially, it lists the `skills` it possesses, linking back to the `AgentSkill` defined earlier. This card is the primary way other agents or systems discover and learn about the `MultiURLBrowser`.

## 4. Taking Action: The Invoke Method (`agent.py`)

When the `MultiURLBrowser` receives a mission (a user query), it springs into action through its `invoke` method in [`agent.py`](agents/search_agent/agent.py). This is where it processes the request and directs its internal ADK runner to perform the necessary steps, including utilizing its MCP tool.

```python
# agents/search_agent/agent.py
# ... imports and class definition ...

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
```

The `invoke` method is the agent's execution engine. It receives the `query` and a `session_id` to maintain context. It prepares the query for its internal ADK brain and then initiates the `self._runner.run_async` process. This is where the ADK agent, guided by its instructions and equipped with the MCP tool, figures out how to fulfill the request – likely by instructing the FireCrawl tool to scrape the specified URLs. As the ADK runner works, it yields events, allowing the `invoke` method to stream back updates ("Processing the web crawling request...") and eventually the final extracted `content`.

## 5. The Task Master: The Task Manager (`task_manager.py`)

To fit seamlessly into the A2A framework, the `MultiURLBrowser` needs a dedicated Task Manager. The `AgentTaskManager` in [`task_manager.py`](agents/search_agent/task_manager.py) fulfills this role, acting as the interface between the A2A server's task management system and the agent's core logic.

```python
# agents/search_agent/task_manager.py
# ... imports ...

class AgentTaskManager(AgentExecutor):
    """
    Implements the AgentExecutor interface to integrate the MultiURLBrowser
    agent into the A2A server framework. This class is responsible for:
    - Initializing the MultiURLBrowser agent.
    - Handling incoming user requests and mapping them to agent invocations.
    - Managing task state updates (e.g., 'working', 'completed').
    - Formatting agent responses into A2A Messages.
    """

    def __init__(self):
        """
        👷 Initializes the AgentTaskManager.
        It creates an instance of our MultiURLBrowser agent, which will be
        responsible for performing the actual web scraping tasks.
        """
        self.agent = MultiURLBrowser()
        logger.info("AgentTaskManager initialized with MultiURLBrowser agent.")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Executes a new task for the agent based on the user's input.
        This method retrieves the user's query, manages the task lifecycle,
        and streams updates or the final response back to the A2A server.

        Args:
            context (RequestContext): Contains information about the current request,
                                      including user input and task details.
            event_queue (EventQueue): An asynchronous queue to send task updates
                                      and messages back to the A2A server.
        """
        # Extract the user's input query from the request context.
        query = context.get_user_input()
        logger.info(f"Executing task for query: {query[:100]}...")

        # Get the current task from the context. If it's a new request without
        # an existing task, create a new A2A Task object.
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task) # Enqueue the newly created task
            logger.info(f"Created new task with ID: {task.id}")
        else:
            logger.info(f"Continuing existing task with ID: {task.id}")

        # Initialize the TaskUpdater to easily send status updates for this task.
        updater = TaskUpdater(event_queue, task.id, task.contextId)

        try:
            # 🚀 Invoke the MultiURLBrowser agent and stream its responses.
            # The agent.invoke method is an asynchronous generator that yields
            # progress updates and the final result.
            async for item in self.agent.invoke(query, task.contextId):
                is_task_complete = item.get('is_task_complete', False) # Safely get the flag

                if not is_task_complete:
                    # Agent is still working; send a 'working' status update.
                    update_message = item.get('updates', 'Agent is processing...')
                    logger.debug(f"Agent update: {update_message}")
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            update_message, task.contextId, task.id
                        ),
                    )
                else:
                    # Agent has completed the task; send the final content and mark as 'completed'.
                    final_content = item.get('content', 'No content received.')
                    logger.info(f"Task {task.id} completed. Final content length: {len(final_content)} characters.")

                    message = new_agent_text_message(
                        final_content, task.contextId, task.id
                    )
                    await updater.update_status(
                        TaskState.completed, message
                    )
                    break # Exit the loop once the task is complete

        except Exception as e:
            # Catch any exceptions during agent execution and update task status to failed.
            logger.exception(f"Error during agent execution for task {task.id}: {e}")
            error_message = f"An error occurred: {str(e)}"
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(error_message, task.contextId, task.id),
            )
            raise # Re-raise the exception after logging and updating task status

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """
        Handles requests to cancel an ongoing task.
        For simplicity, this agent does not support cancellation and will
        raise an UnsupportedOperationError.
        """
        # ... cancellation logic ...
```

The `AgentTaskManager` is the diligent administrator. It initializes an instance of the `MultiURLBrowser` agent. Its core responsibility lies in the `execute` method, which is triggered by the A2A server upon receiving a new request. The manager retrieves the user's `query`, ensures a proper A2A `Task` is in place, and then delegates the actual work to the `MultiURLBrowser`'s `invoke` method. As the agent streams back updates, the manager uses the `TaskUpdater` to keep the A2A server informed of the task's status – marking it as `working`, `completed`, or `failed`.

## 6. Connecting with the Agent: Client Interaction (`client.py`)

Finally, for other agents or applications to harness the `MultiURLBrowser`'s web-scraping power, they need a way to connect and communicate. The [`client.py`](agents/search_agent/client.py) script provides a blueprint for this interaction using the `a2a.client` library.

```python
# agents/search_agent/client.py
# ... imports ...

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
    # ... logging ...

    # The base URL of the A2A agent server we want to connect to.
    base_url = 'http://localhost:10000' # Updated to match the previous server's default port

    # ... httpx client setup ...

    # 1. Resolve Agent Card: Discover the agent's capabilities
    logger.info("Initializing A2ACardResolver to fetch agent capabilities.")
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url,
    )

    # ... fetch public card ...

    # 2. Initialize A2AClient: Set up to communicate with the agent
    logger.info("Initializing A2AClient with the fetched Agent Card.")
    client = A2AClient(
        httpx_client=httpx_client, agent_card=final_agent_card_to_use
    )

    # 3. Construct and Send Message: Define the user's query
    user_query = (
        "Scrape the title and first paragraph from this URL: "
        "https://medium.com/google-cloud/mastering-cross-project-service-account-impersonation-in-google-cloud-265f6f352cf2 "
        "and also from this URL: https://www.geeksforgeeks.org/introduction-to-web-scraping/"
    )
    logger.info(f"Preparing to send message to agent: '{user_query[:70]}...'")

    send_message_payload: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [
                {'kind': 'text', 'text': user_query}
            ],
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

    # 4. Process and Print Response: Extract the agent's answer
    # ... process and print response ...

# ... main execution block ...
```

The client script acts as an adventurer seeking the `MultiURLBrowser`'s help. It first uses the `A2ACardResolver` to find the agent's public `AgentCard`, learning its address and capabilities. With the card in hand, it initializes an `A2AClient` to establish communication. It then crafts a `SendMessageRequest`, formulating the web-scraping mission as an A2A message, and dispatches it using `client.send_message`. Upon receiving the `response_record`, the client extracts the valuable extracted `content`, completing the interaction.

## The Journey Completed

By implementing the `AgentExecutor` interface in the Task Manager, defining its capabilities with `AgentSkill` and `AgentCard`, and structuring its core logic to be invoked by the manager, the `MultiURLBrowser` agent successfully transitioned from an ADK agent with an MCP tool to a fully A2A-compatible agent. This allows it to participate in the broader A2A ecosystem, offering its specialized web-scraping skills to other agents and applications.

---

## Orchestrating Agents: The Tale of the Scrap & Translate Agent

In the world of A2A, agents don't just work in isolation; they can collaborate and leverage each other's unique skills. This is where the concept of an **Orchestrator Agent** comes in. An orchestrator agent acts as a conductor, understanding a user's complex request and breaking it down into smaller tasks that can be delegated to other specialized agents. It then gathers the results from these agents and synthesizes them into a final response for the user.

Let's explore the `Scrap_Translate` agent, located in the `Scrap_Translate/` directory, as an example of an orchestrator agent that can call other agents as tools.

```
Scrap_Translate/
├── __init__.py
└── agent.py
```

The full code for this agent can be found in the project's Git repository at `www.example.com`. Below, we highlight the key sections in [`Scrap_Translate/agent.py`](Scrap_Translate/agent.py) relevant to agent orchestration.

The core logic for our orchestrator agent resides in [`Scrap_Translate/agent.py`](Scrap_Translate/agent.py).

**Key Snippet: Discovering Agents (`list_agents` function)**

The `list_agents` function demonstrates how an orchestrator can discover other available agents in the A2A network by querying a well-known endpoint on an agent registry.

```python
# Scrap_Translate/agent.py
# ... imports ...
AGENT_REGISTRY_BASE_URL = "http://localhost:10000"

async def list_agents() -> list[dict]:
    """
    Fetch all AgentCard metadata from the registry...
    """
    async with httpx.AsyncClient() as client:
        url = AGENT_REGISTRY_BASE_URL.rstrip("/") + "/.well-known/agent.json"
        response = await client.get(url, timeout=50.0)
    cards_data = response.json()
    return cards_data
```

**Key Snippet: Calling Other Agents (`call_agent` function)**

The `call_agent` function is the orchestrator's primary means of interacting with other agents, using the `a2a.client.A2AClient` to send messages.

```python
# Scrap_Translate/agent.py
# ... imports ...
async def call_agent(agent_name: str, message: str) -> str:
    """
    Given an agent_name string and a user message,
    find that agent’s URL, send the task, and return its reply.
    """
    client = A2AClient(httpx_client=httpx.AsyncClient(timeout=3000),
                       url=AGENT_REGISTRY_BASE_URL) # Or use agent_card if resolved

    # ... construct payload ...
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "message/send",
        "params": {
            "message": {'role': 'user', 'parts': [{'kind': 'text', 'text': message}], 'messageId': uuid4().hex},
            "metadata": {}
        }
    }

    response_rec = await client.send_message(SendMessageRequest(**payload))
    response = response_rec.model_dump(mode='json', exclude_none=True)
    return (response['result']['status']['message']['parts'][0]['text'])
```
*Note: In a real-world scenario, the `call_agent` function might first use `list_agents` or an `A2ACardResolver` to get the target agent's `AgentCard` and then initialize the `A2AClient` with that card for direct communication, rather than relying solely on the registry URL for `send_message`.*

**Key Snippet: LLM Instructions and Tools**

The orchestrator agent's `LlmAgent` is configured with instructions and `FunctionTool`s that allow the LLM to use the `list_agents` and `call_agent` functions.

```python
# Scrap_Translate/agent.py
# ... imports and function definitions ...
system_instr = (
    "You are a root orchestrator agent. You have two tools:\n"
    "1) list_agents() → Use this tool to see a list of all available agents...\n"
    "2) call_agent(agent_name: str, message: str) → Use this tool to send a message...\n"
    "Use these tools to fulfill user requests by discovering and interacting with other agents as needed.\n"
)

root_agent = LlmAgent(
    model="gemini-2.5-pro-preview-03-25",
    name="root_orchestrator",
    description="Discovers and orchestrates other agents",
    instruction=system_instr,
    tools=[
        FunctionTool(list_agents), # Expose list_agents as a tool
        FunctionTool(call_agent),  # Expose call_agent as a tool
    ],
)
# ... Runner and main execution logic ...
```
This snippet shows how the `system_instr` guides the LLM and how the Python functions are exposed as tools using `FunctionTool`.

By combining the ability to discover other agents and the mechanism to call them using the A2A protocol, an orchestrator agent like `Scrap_Translate` can effectively leverage the capabilities of specialized agents (like our `MultiURLBrowser`) to handle more complex and multi-step tasks. This demonstrates the power of the A2A framework in enabling agents to collaborate and form a distributed system of intelligence.
