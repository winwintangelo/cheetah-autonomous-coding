"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.
Supports 100+ models via OpenRouter API.
"""

import asyncio
from pathlib import Path
from typing import Optional

from agents import AgentConfig, BaseCodingAgent, get_agent, list_available_agents, DEFAULT_AGENT
from logging_util import init_logger, log, close_logger
from progress import print_session_header, print_progress_summary, count_passing_tests
from prompts import get_initializer_prompt, get_coding_prompt, get_coding_prompt_with_context, copy_spec_to_project


# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3

# Default model (can be overridden via environment variable OPENROUTER_MODEL)
DEFAULT_MODEL = "anthropic/claude-sonnet-4"


def get_default_model() -> str:
    """
    Get the default model.
    
    Checks OPENROUTER_MODEL environment variable first, then falls back to hardcoded default.
    """
    import os
    
    # Check for environment variable override
    env_model = os.environ.get("OPENROUTER_MODEL")
    if env_model:
        return env_model
    
    # Fall back to hardcoded default
    return DEFAULT_MODEL


async def run_agent_session(
    agent: BaseCodingAgent,
    message: str,
    project_dir: Path,
) -> tuple[str, str]:
    """
    Run a single agent session using the provided coding agent.

    Args:
        agent: The coding agent to use
        message: The prompt to send
        project_dir: Project directory path

    Returns:
        (status, response_text) where status is:
        - "continue" if agent should continue working
        - "error" if an error occurred
    """
    response = await agent.run_session(message)

    if response.status == "error":
        return "error", response.error or "Unknown error"

    return response.status, response.text


async def run_autonomous_agent(
    project_dir: Path,
    agent_type: str = DEFAULT_AGENT,
    model: Optional[str] = None,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        agent_type: Type of coding agent to use (default: "openrouter")
        model: Model to use (defaults to OPENROUTER_MODEL env var or anthropic/claude-sonnet-4)
        max_iterations: Maximum number of iterations (None for unlimited)
    """
    # Validate agent type
    available_agents = list_available_agents()
    if agent_type not in available_agents:
        print(f"Error: Unknown agent type '{agent_type}'")
        print(f"Available agents: {', '.join(available_agents)}")
        return

    # Use default model if not specified
    if model is None:
        model = get_default_model()

    print("\n" + "=" * 70)
    print("  AUTONOMOUS CODING AGENT")
    print("=" * 70)
    print(f"\nAgent: OpenRouter")
    print(f"Project directory: {project_dir}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Initialize logger
    logger = init_logger(project_dir)
    log(f"Log file: {logger.log_path}")

    # Check if this is a fresh start or continuation
    tests_file = project_dir / "feature_list.json"
    is_first_run = not tests_file.exists()

    if is_first_run:
        print("Fresh start - will use initializer agent")
        print()
        print("=" * 70)
        print("  NOTE: First session takes 10-20+ minutes!")
        print("  The agent is generating ~50 feature test cases.")
        print("  This may appear to hang - it's working. Watch for [Tool: ...] output.")
        print("=" * 70)
        print()
        # Copy the app spec into the project directory for the agent to read
        copy_spec_to_project(project_dir)
    else:
        print("Continuing existing project")
        print_progress_summary(project_dir)

    # Create agent configuration
    config = AgentConfig(
        project_dir=project_dir,
        model=model,
        sandbox_enabled=True,
    )

    # Main loop
    iteration = 0

    while True:
        iteration += 1

        # Check max iterations
        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            print("To continue, run the script again without --max-iterations")
            break

        # Print session header
        print_session_header(iteration, is_first_run)

        # Create agent instance (fresh context for each session)
        agent = get_agent(agent_type, config)

        # Print agent configuration summary
        agent.print_config_summary()

        # Choose prompt based on session type
        if is_first_run:
            prompt = get_initializer_prompt()
            is_first_run = False  # Only use initializer once
        else:
            # Use context-aware prompt that includes failing tests
            prompt = get_coding_prompt_with_context(project_dir, iteration)

        # Run session with async context manager
        async with agent:
            status, response = await run_agent_session(agent, prompt, project_dir)

        # Check for completion (all tests passing)
        passing, total = count_passing_tests(project_dir)
        if total > 0 and passing == total:
            log(f"\n🎉 ALL TESTS PASSING ({passing}/{total})! Project complete.")
            print_progress_summary(project_dir)
            break

        # Handle status
        if status == "continue":
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            print_progress_summary(project_dir)
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        elif status == "error":
            print("\nSession encountered an error")
            print("Will retry with a fresh session...")
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        # Small delay between sessions
        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            await asyncio.sleep(1)

    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print_progress_summary(project_dir)

    # Print instructions for running the generated application
    log("\n" + "-" * 70)
    log("  TO RUN THE GENERATED APPLICATION:")
    log("-" * 70)
    log(f"\n  cd {project_dir.resolve()}")
    log("  ./init.sh           # Run the setup script")
    log("  # Or manually:")
    log("  npm install && npm run dev")
    log("\n  Then open http://localhost:5173 (or check init.sh for the URL)")
    log("-" * 70)

    log("\nDone!")
    
    # Close logger
    close_logger()
