# Autonomous Coding Agent

A minimal harness demonstrating long-running autonomous coding with AI agents. This project implements a two-agent pattern (initializer + coding agent) that can build complete applications over multiple sessions.

**Supports 100+ models** via OpenRouter API (Anthropic, OpenAI, Google, Meta, Mistral, and more).

## Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (for UI testing)
playwright install chromium

# Set up API key (choose one method):
# Option 1: Environment variable
export OPENROUTER_API_KEY='your-api-key-here'

# Option 2: Create .env file
cp env.example .env
# Then edit .env and add your API key
```

Get your OpenRouter API key from: https://openrouter.ai/keys

## Quick Start

### Start a new project:
```bash
python autonomous_agent.py --project-dir ./my_project
```

### Use a specific model:
```bash
python autonomous_agent.py --project-dir ./my_project --model openai/gpt-4o
python autonomous_agent.py --project-dir ./my_project --model google/gemini-pro-1.5
python autonomous_agent.py --project-dir ./my_project --model meta-llama/llama-3.1-70b-instruct
```

### For testing with limited iterations:
```bash
python autonomous_agent.py --project-dir ./my_project --max-iterations 3
```

### Validate your setup:
```bash
python validate_agent.py           # Check setup
python validate_agent.py --test    # Run live test
python validate_agent.py --commands # Run comprehensive command tests
```

## Important Timing Expectations

> **Warning: This demo takes time to run!**

- **First session (initialization):** The agent generates a `feature_list.json` with ~50 test cases. This takes several minutes.

- **Subsequent sessions:** Each coding iteration can take **5-15 minutes** depending on complexity.

- **Full app:** Building all 50 features typically requires **several hours** of total runtime across multiple sessions.

**Tip:** If you want faster demos, you can modify `prompts/initializer_prompt.md` to reduce the feature count (e.g., 10-20 features for a quicker demo).

## How It Works

### Two-Agent Pattern

1. **Initializer Agent (Session 1):** Reads `app_spec.txt`, creates `feature_list.json` with ~50 test cases, sets up project structure, and initializes git.

2. **Coding Agent (Sessions 2+):** Picks up where the previous session left off, implements features one by one, and marks them as passing in `feature_list.json`.

### Session Management

- Each session runs with a fresh context window
- Progress is persisted via `feature_list.json` and git commits
- The agent auto-continues between sessions (3 second delay)
- Press `Ctrl+C` to pause; run the same command to resume

## Supported Models

Any model available on OpenRouter can be used. Popular options:

| Provider | Model | Notes |
|----------|-------|-------|
| Anthropic | `anthropic/claude-sonnet-4` | Default, excellent coding |
| Anthropic | `anthropic/claude-opus-4` | Most capable |
| OpenAI | `openai/gpt-4o` | Strong all-around |
| OpenAI | `openai/gpt-4o-mini` | Fast and efficient |
| Google | `google/gemini-pro-1.5` | Long context |
| Meta | `meta-llama/llama-3.1-70b-instruct` | Open weights |
| DeepSeek | `deepseek/deepseek-chat` | Cost effective |

Full list: https://openrouter.ai/models

## Security Model

This project uses a defense-in-depth security approach (see `security.py`):

1. **Filesystem Restrictions:** File operations restricted to the project directory only
2. **Bash Allowlist:** Only specific commands are permitted:
   - File inspection: `ls`, `cat`, `head`, `tail`, `wc`, `grep`
   - Node.js: `npm`, `npx`, `pnpm`, `node`
   - Version control: `git`
   - Process management: `ps`, `lsof`, `sleep`, `pkill` (dev processes only)

Commands not in the allowlist are blocked by the security hook.

## Project Structure

```
autonomous-coding/
├── autonomous_agent.py  # Main entry point
├── agent.py                  # Agent session logic
├── agents/                   # Agent abstraction layer
│   ├── __init__.py           # Agent factory and registry
│   ├── base.py               # BaseCodingAgent abstract class
│   └── openrouter_agent.py   # OpenRouter API implementation
├── security.py               # Bash command allowlist and validation
├── progress.py               # Progress tracking utilities
├── prompts.py                # Prompt loading utilities
├── logging_util.py           # Dual logging (stdout + file)
├── validate_agent.py         # Agent setup validation script
├── prompts/
│   ├── app_spec.txt          # Application specification
│   ├── initializer_prompt.md # First session prompt
│   └── coding_prompt.md      # Continuation session prompt
├── requirements.txt          # Python dependencies
└── PRD.md                    # Product requirements document
```

## Generated Project Structure

After running, your project directory will contain:

```
my_project/
├── feature_list.json         # Test cases (source of truth)
├── app_spec.txt              # Copied specification
├── init.sh                   # Environment setup script
├── progress.txt              # Session progress notes
├── logs/                     # Agent session logs
└── [application files]       # Generated application code
```

## Running the Generated Application

After the agent completes (or pauses), you can run the generated application:

```bash
cd generations/my_project

# Run the setup script created by the agent
./init.sh

# Or manually (typical for Vite + React apps):
cd client && npm install && npm run dev
```

The application will typically be available at `http://localhost:5173` (check the agent's output or `init.sh` for the exact URL).

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Directory for the project | `./autonomous_demo_project` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Model to use | `anthropic/claude-sonnet-4` |

## Customization

### Changing the Application

Edit `prompts/app_spec.txt` to specify a different application to build.

### Adjusting Feature Count

Edit `prompts/initializer_prompt.md` and change the "50 features" requirement to a smaller number for faster demos.

### Modifying Allowed Commands

Edit `security.py` to add or remove commands from `ALLOWED_COMMANDS`.

## Troubleshooting

**"Appears to hang on first run"**
This is normal. The initializer agent is generating detailed test cases, which takes significant time. Watch for `[Tool: ...]` output to confirm the agent is working.

**"Command blocked by security hook"**
The agent tried to run a command not in the allowlist. This is the security system working as intended. If needed, add the command to `ALLOWED_COMMANDS` in `security.py`.

**"API key not set"**
Ensure `OPENROUTER_API_KEY` is exported in your shell environment or added to `.env` file.

## License

MIT License
