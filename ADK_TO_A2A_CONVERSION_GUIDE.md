# ADK to A2A Conversion Guide

A practical guide for converting Google ADK agents to be compatible with the A2A (Agent-to-Agent) framework.

## 🎯 Overview

This guide demonstrates how to transform an ADK agent using MCP tools into an A2A-compatible agent that can be discovered and called by other agents.

## 📁 Project Structure

```
agents/search_agent/
├── __main__.py         # A2A server setup and agent metadata
├── agent.py            # Core ADK agent logic
├── task_manager.py     # A2A framework bridge
└── client.py           # Example A2A client
```

## 🔧 Key Components

### 1. Agent Definition (`agent.py`)

**Core Concept**: Wrap your existing ADK agent in a class with an async `invoke` method.

```python
class MultiURLBrowser:
    def __init__(self):
        self._agent = self._build_agent()  # Your ADK LlmAgent
        self._runner = Runner(...)         # ADK Runner setup
    
    async def invoke(self, query: str, session_id: str) -> AsyncIterable[dict]:
        # Process query with ADK runner
        # Yield progress updates and final results
        yield {'is_task_complete': False, 'updates': 'Processing...'}
        yield {'is_task_complete': True, 'content': final_result}
```

### 2. A2A Server Setup (`__main__.py`)

**Core Concept**: Define your agent's capabilities and start the A2A server.

```python
# Define what your agent can do
skill = AgentSkill(
    id="MultiURLBrowser",
    name="Web Scraper Agent",
    description="Scrapes content from URLs",
    examples=["Scrape https://example.com"]
)

# Create agent identity for A2A network
agent_card = AgentCard(
    name="MultiURLBrowser",
    skills=[skill],
    url=f"http://{host}:{port}/"
)
```

### 3. Task Management (`task_manager.py`)

**Core Concept**: Bridge between A2A framework and your agent.

```python
class AgentTaskManager(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        # Get user query
        query = context.get_user_input()
        
        # Call your agent and stream responses
        async for result in self.agent.invoke(query, session_id):
            if result['is_task_complete']:
                await updater.update_status(TaskState.completed, message)
```

## 🔄 Agent Communication

### Direct Client Usage
```python
# Connect to agent
client = A2AClient(agent_card=agent_card)

# Send message
response = await client.send_message(request)
```

### Agent-to-Agent Communication (`scrap_translate/agent.py`)
```python
# Example from scrap_translate/agent.py - Orchestrator agent calling search agent
async def call_agent(agent_name: str, message: str) -> str:
    cards = await list_agents()
    client = A2AClient(agent_card=cards)
    response = await client.send_message(request)
    return response.content
```

## ✅ Conversion Checklist

- [ ] **Agent Class**: Create async `invoke` method that yields progress/results
- [ ] **Agent Skill**: Define capabilities and examples  
- [ ] **Agent Card**: Set up public identity and metadata
- [ ] **Task Manager**: Bridge A2A requests to your agent
- [ ] **Server Setup**: Configure A2A server with your agent card
- [ ] **Environment Config**: Use env variables for API keys and settings

## 🎯 Key Benefits

1. **Discoverability**: Other agents can find and use your agent
2. **Standardization**: Common A2A protocol for all agent interactions  
3. **Scalability**: Agents can call multiple specialized agents
4. **Flexibility**: Mix and match different agent capabilities

## 🔗 Example Architectures

### Single Agent
```
Client → A2A Agent → ADK Runner → MCP Tool → External Service
```

### Multi-Agent System  
```
Orchestrator Agent → list_agents() → call_agent() → Search Agent → Web Scraping
                                  → call_agent() → Translation Agent → Language Processing  
                                  → call_agent() → Summary Agent → Content Summarization
```

## 🚀 Getting Started

1. **Wrap your ADK agent** in a class with async `invoke` method
2. **Define agent skills** to describe capabilities
3. **Create task manager** to handle A2A requests  
4. **Set up A2A server** with agent card
5. **Test with client** or other agents

This conversion enables your ADK agent to participate in collaborative AI workflows while maintaining all its original capabilities.
