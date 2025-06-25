# =============================================================================
# agents/search_agent/task_manager.py
# =============================================================================
# 🎯 Purpose:
# This file defines the AgentTaskManager, which acts as the bridge between
# the A2A (Agent-to-Agent) server framework and our specific MultiURLBrowser agent.
# It manages the execution of agent tasks, handles input/output, and updates
# the task status within the A2A system.
# =============================================================================

# -----------------------------------------------------------------------------
# 📦 Essential Imports
# -----------------------------------------------------------------------------
import logging # For logging information and debugging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Task,
    TaskState,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

# 🤖 Import the actual agent implementation we want to use
from agents.search_agent.agent import MultiURLBrowser


# -----------------------------------------------------------------------------
# 🪵 Logging Setup
# Configure logging to display information and errors in the console.
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 🛠️ AgentTaskManager: Manages the execution of the MultiURLBrowser Agent
# -----------------------------------------------------------------------------
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
                    # Small delay to ensure the message is processed before exiting
                    import asyncio
                    await asyncio.sleep(0.1)
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

        Args:
            request (RequestContext): The context of the cancellation request.
            event_queue (EventQueue): The event queue for sending updates.

        Raises:
            ServerError: Always raises UnsupportedOperationError as cancellation
                         is not implemented for this agent.
        """
        logger.warning(f"Attempted to cancel task {request.current_task.id if request.current_task else 'N/A'}. Cancellation is not supported.")
        raise ServerError(error=UnsupportedOperationError())