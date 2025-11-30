#!/usr/bin/env python3
"""
Autonomous Coding Agent
=======================

A minimal harness demonstrating long-running autonomous coding with AI agents.
This script implements the two-agent pattern (initializer + coding agent) and
supports 100+ models via OpenRouter API.

Example Usage:
    # Start a new project
    python autonomous_agent.py --project-dir ./my_project

    # Use a specific model
    python autonomous_agent.py --project-dir ./my_project --model openai/gpt-4o

    # Limit iterations for testing
    python autonomous_agent.py --project-dir ./my_project --max-iterations 5
"""

import argparse
import asyncio
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, skip

from agent import run_autonomous_agent, get_default_model
from agents import DEFAULT_AGENT


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous Coding Agent - Long-running agent harness with 100+ model support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start fresh project with default model
  python autonomous_agent.py --project-dir ./my_project

  # Use a specific model (any OpenRouter model)
  python autonomous_agent.py --project-dir ./my_project --model openai/gpt-4o
  python autonomous_agent.py --project-dir ./my_project --model google/gemini-pro-1.5
  python autonomous_agent.py --project-dir ./my_project --model meta-llama/llama-3.1-70b-instruct

  # Limit iterations for testing
  python autonomous_agent.py --project-dir ./my_project --max-iterations 5

  # Continue existing project
  python autonomous_agent.py --project-dir ./my_project

Supported Model Providers (via OpenRouter):
  - anthropic/* (Claude models)
  - openai/* (GPT models)
  - google/* (Gemini models)
  - meta-llama/* (Llama models)
  - deepseek/* (DeepSeek models)
  - mistralai/* (Mistral models)
  - And 100+ more at https://openrouter.ai/models

Environment Variables:
  OPENROUTER_API_KEY    Your OpenRouter API key (required)
                        Get your key from: https://openrouter.ai/keys
  
  OPENROUTER_MODEL      Default model to use (optional)
                        Default: anthropic/claude-sonnet-4
        """,
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("./autonomous_demo_project"),
        help="Directory for the project (default: generations/autonomous_demo_project). "
        "Relative paths automatically placed in generations/ directory.",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of agent iterations (default: unlimited)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (default: OPENROUTER_MODEL env var or anthropic/claude-sonnet-4). "
        "See https://openrouter.ai/models for available models.",
    )

    return parser.parse_args()


def check_api_key() -> bool:
    """Check if the required API key is set."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY environment variable not set")
        print("\nGet your API key from: https://openrouter.ai/keys")
        print("\nThen set it:")
        print("  export OPENROUTER_API_KEY='your-api-key-here'")
        print("\nOr add it to a .env file in this directory.")
        return False
    return True


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Check for API key
    if not check_api_key():
        return

    # Automatically place projects in generations/ directory unless already specified
    project_dir = args.project_dir
    if not str(project_dir).startswith("generations/"):
        # Convert relative paths to be under generations/
        if project_dir.is_absolute():
            # If absolute path, use as-is
            pass
        else:
            # Prepend generations/ to relative paths
            project_dir = Path("generations") / project_dir

    # Use default model if not specified
    model = args.model
    if model is None:
        model = get_default_model()

    # Run the agent with proper signal handling
    import signal
    
    async def run_with_signal_handling():
        """Wrapper that handles Ctrl+C properly during async operations."""
        loop = asyncio.get_running_loop()
        
        # Create an event to signal shutdown
        shutdown_event = asyncio.Event()
        
        def signal_handler():
            print("\n\n⚠️  Interrupt received, shutting down gracefully...")
            shutdown_event.set()
        
        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        
        try:
            # Run agent with shutdown check
            task = asyncio.create_task(
                run_autonomous_agent(
                    project_dir=project_dir,
                    agent_type=DEFAULT_AGENT,
                    model=model,
                    max_iterations=args.max_iterations,
                )
            )
            
            # Wait for either task completion or shutdown signal
            done, pending = await asyncio.wait(
                [task, asyncio.create_task(shutdown_event.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any pending tasks
            for t in pending:
                t.cancel()
                try:
                    await t
                except asyncio.CancelledError:
                    pass
            
            # If shutdown was triggered, raise KeyboardInterrupt
            if shutdown_event.is_set():
                raise KeyboardInterrupt()
                
        finally:
            # Remove signal handlers
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.remove_signal_handler(sig)
    
    try:
        asyncio.run(run_with_signal_handling())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print("To resume, run the same command again")
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise


if __name__ == "__main__":
    main()

