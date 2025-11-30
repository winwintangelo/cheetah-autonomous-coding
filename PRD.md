# Autonomous Coding Agent - Product Requirements Document

## Overview

The Autonomous Coding Agent is a minimal harness demonstrating long-running autonomous coding with AI. It implements a **two-agent pattern** (initializer + coding agent) that can build complete applications over multiple sessions.

**Supports 100+ models** via OpenRouter API.

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                     autonomous_agent.py                         │
│                         (Entry Point)                                │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           agent.py                                   │
│                    (Agent Session Logic)                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ run_autonomous  │  │ run_agent      │  │ Session Management  │  │
│  │ _agent()        │──│ _session()     │──│ & Auto-continue     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        agents/ Package                               │
│  ┌─────────────────┐  ┌─────────────────────────────────────────┐  │
│  │ base.py         │  │ openrouter_agent.py                     │  │
│  │ BaseCodingAgent │  │ OpenRouterAgent (REST API + Playwright) │  │
│  └─────────────────┘  └─────────────────────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      OpenRouter API                                  │
│                (100+ models from multiple providers)                 │
│   Anthropic, OpenAI, Google, Meta, Mistral, DeepSeek, etc.          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         security.py                                  │
│                   (Bash Command Validation)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ Allowed         │  │ Command        │  │ Extra Validation    │  │
│  │ Commands List   │  │ Extraction     │  │ (pkill, chmod)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Two-Agent Pattern

1. **Initializer Agent (Session 1)**
   - Reads `app_spec.txt` specification
   - Creates `feature_list.json` with ~50 test cases
   - Creates `init.sh` setup script
   - Initializes Git repository
   - Sets up project structure

2. **Coding Agent (Sessions 2+)**
   - Picks up where the previous session left off
   - Implements features one by one
   - Tests with browser automation (Playwright)
   - Marks tests as passing in `feature_list.json`
   - Commits progress to git

### Session Management

- Each session runs with a **fresh context window**
- Progress persisted via `feature_list.json` and git commits
- Auto-continues between sessions (3 second delay)
- Press `Ctrl+C` to pause; run same command to resume
- **Graceful shutdown**: Proper async signal handling ensures `Ctrl+C` works even during API calls
  - Registers `SIGINT`/`SIGTERM` handlers in event loop
  - Cancels pending tasks cleanly
  - Handles `asyncio.CancelledError` for proper propagation

## Components

### Entry Point (`autonomous_agent.py`)

| Argument | Description | Default |
|----------|-------------|---------|
| `--project-dir` | Directory for the project | `./autonomous_demo_project` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Model to use | `anthropic/claude-sonnet-4` |

### Agents Package (`agents/`)

| File | Description |
|------|-------------|
| `__init__.py` | Factory function `get_agent()` and agent registry |
| `base.py` | `BaseCodingAgent` abstract class and `AgentConfig` dataclass |
| `openrouter_agent.py` | `OpenRouterAgent` - OpenRouter API implementation |

### Supported Models

Any model on OpenRouter can be used:

| Provider | Example Models |
|----------|----------------|
| Anthropic | `anthropic/claude-sonnet-4`, `anthropic/claude-opus-4` |
| OpenAI | `openai/gpt-4o`, `openai/gpt-4o-mini` |
| Google | `google/gemini-pro-1.5` |
| Meta | `meta-llama/llama-3.1-70b-instruct` |
| DeepSeek | `deepseek/deepseek-chat` |
| Mistral | `mistralai/mistral-large` |

Full list: https://openrouter.ai/models

### Agent Logic (`agent.py`)

- `run_autonomous_agent()` - Main loop managing sessions
- `run_agent_session()` - Single session execution
- Handles session headers, progress tracking, auto-continue

### Agent Configuration

Each agent supports a common `AgentConfig`:

```python
@dataclass
class AgentConfig:
    project_dir: Path          # Project directory
    model: str                 # Model identifier
    allowed_commands: set[str] # Bash command allowlist
    sandbox_enabled: bool      # OS-level sandbox
    system_prompt: str         # Custom system prompt
    max_turns: int             # Max conversation turns
    api_key: Optional[str]     # API key override
    extra_options: dict        # Agent-specific options
```

### OpenRouter Agent Features

- Uses OpenRouter REST API (OpenAI-compatible)
- Supports 100+ models from multiple providers
- Built-in tool execution: `read_file`, `write_file`, `batch_read_files`, `batch_list_directories`, `run_command`, `list_directory`, `manage_server`
- Command validation against security allowlist
- Authentication: `OPENROUTER_API_KEY` env var
- Enhanced system prompt with tool documentation (parameters, examples, allowed commands)
- Dev server management with start/stop/restart/status support
- **Browser automation via Playwright**:
  - `browser_navigate` - Navigate to URL, launches browser automatically
  - `browser_screenshot` - Capture screenshots (full page, viewport, or element)
  - `browser_click` - Click elements by CSS selector
  - `browser_fill` - Fill input fields
  - `browser_evaluate` - Execute JavaScript in browser context
  - `browser_close` - Close browser instance
  - Screenshots saved to `screenshots/` directory in project
- **Session management**:
  - Max 100 tool calls per session (enough for full feature cycle)
  - Warns when max iterations reached
  - Reports when sessions explore but don't write files
  - Robust error detection (only matches "Error:" prefix, not file content)
  - **Duration tracking**: Shows execution time in ms for each tool call and total session time
  - **Thinking duration tracking**: Logs time between API call and response
  - **Progressive nudges**: At 10, 20, 35 tool calls without writes, injects increasingly urgent reminders
  - **Positive reinforcement**: Encourages agent after first write_file with next steps
  - **Context-aware prompts**: Includes specific failing tests and tells agent to skip redundant exploration
  - **Dual logging**: All output goes to both stdout AND log files in `{project}/logs/agent_session_{timestamp}.log`
  - **Full timestamps**: Log entries include date and time (`[2025-11-29 22:41:45]`)
- **Efficiency optimizations**:
  - **Project snapshot in prompt**: Includes directory listing, source structure, git log, progress notes, dev server URL, app spec summary - eliminates need for pwd, ls, cat commands
  - **batch_read_files tool**: Read up to 10 files in one call instead of 10 separate read_file calls
  - **batch_list_directories tool**: List multiple directories in one call (e.g., `{"paths": [".", "src", "server"]}`)
  - **Efficiency tips in prompt**: Guides agent to complete a feature cycle in ~30 calls vs 100
  - **Explicit "DO NOT" list**: Tells agent which commands to skip (pwd, ls, cat, git log, wrong port)
  - **Dev server port auto-detection**: Parses vite.config.ts to include correct URL in snapshot
  - **Auto-completion detection**: Stops agent loop when all tests pass (100% completion)
  - **Vite default port detection**: Correctly identifies port 5173 for Vite projects without explicit config
  - **Post-initializer guidance**: Prevents wasted verification commands (git log, ls, wc) after completing mandatory files

### Security (`security.py`)

**Allowed Commands:**
| Category | Commands |
|----------|----------|
| File inspection | `ls`, `cat`, `head`, `tail`, `wc`, `grep` |
| File discovery | `find` (current directory only, no `-exec`/`-delete`) |
| File operations | `cp`, `mkdir`, `chmod` (+x only) |
| Directory/output | `pwd`, `echo` |
| Node.js | `npm`, `npx`, `pnpm`, `node` |
| Version control | `git` |
| Process management | `ps`, `lsof`, `sleep`, `pkill` (dev processes only) |
| Script execution | `bash`, `sh`, `init.sh` |

**Commands with Extra Validation:**
| Command | Validation Rules |
|---------|------------------|
| `find` | Path must start with `.` or `./`; blocks `-exec`, `-execdir`, `-delete`, `-ok` |
| `pkill` | Only dev processes: `node`, `npm`, `npx`, `vite`, `next` |
| `chmod` | Only `+x` mode allowed (e.g., `chmod +x`, `chmod u+x`) |
| `init.sh` | Only `./init.sh` or paths ending in `/init.sh` |
| `bash`/`sh` | Blocks `-c` flag to prevent command injection |

### Progress Tracking (`progress.py`)

- Counts passing/total tests from `feature_list.json`
- Prints session headers and progress summaries

### Logging (`logging_util.py`)

- **Dual output**: All messages go to both stdout and log file
- **Timestamped logs**: Every entry includes `[YYYY-MM-DD HH:MM:SS]`
- **Tool call duration**: Shows execution time in milliseconds
- **Thinking duration**: Logs time waiting for API response
- **Session markers**: Clear start/end markers in log files

### Prompt Loading (`prompts.py`)

- Loads prompts from `prompts/` directory
- Copies `app_spec.txt` to project directory

## Prompt Templates

### Initializer Prompt (`prompts/initializer_prompt.md`)

Tasks:
1. Read `app_spec.txt` specification
2. Create `feature_list.json` with ~50 test cases
3. Create `init.sh` setup script
4. Initialize Git repository
5. Set up project structure
6. Optionally start implementation

Includes:
- **Allowed Bash Commands** section listing permitted commands
- **Browser Automation** tools reference for optional verification
- **Stop after committing** guidance to prevent wasted verification commands

### Coding Prompt (`prompts/coding_prompt.md`)

Steps:
1. **Orient** - Read files, check git history, count remaining tests
2. **Start servers** - Run `init.sh`
3. **Verify** - Test existing passing features for regressions
4. **Choose** - Pick highest-priority failing feature
5. **Implement** - Write code
6. **Test** - Use browser automation (mandatory!)
7. **Update** - Mark test as passing (only change `"passes"` field)
8. **Commit** - Git commit with descriptive message
9. **Progress** - Update `progress.txt`
10. **Clean exit** - Ensure no broken state

Includes:
- **Efficiency Tips** section with batch tools and wasteful command warnings
- **Allowed Bash Commands** section listing permitted commands
- **Browser Automation Tools** section with full tool reference

## Demo Application Spec

Default spec (`prompts/app_spec.txt`) builds a project management clone:

| Component | Technology |
|-----------|------------|
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Backend | Node.js + Express + TypeScript |
| Database | SQLite with Drizzle ORM |

## Dependencies

### Python Dependencies (`requirements.txt`)

```
httpx>=0.27.0           # For OpenRouter API
python-dotenv>=1.0.0    # For .env file support
playwright>=1.40.0      # Browser automation
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter API key (required) |
| `OPENROUTER_MODEL` | Default model (optional, defaults to `anthropic/claude-sonnet-4`) |

Get your key from: https://openrouter.ai/keys

All variables can be set in a `.env` file (copy from `env.example`).

### Validation Script (`validate_agent.py`)

Validates agent setup and can run live tests:

```bash
python validate_agent.py                    # Validate setup
python validate_agent.py --test             # Run live test (uses API credits)
python validate_agent.py --commands         # Run comprehensive command tests
python validate_agent.py --test --commands  # Both test types
```

**Command Tests** (`--commands`): Comprehensive tool/command tests (~35 tests):

| Category | Tests |
|----------|-------|
| **File Tools** | `write_file`, `read_file`, `list_directory`, `batch_read_files`, `batch_list_directories` |
| **Bash - File Inspection** | `ls`, `cat`, `head`, `tail`, `wc`, `grep`, `find` |
| **Bash - File Operations** | `cp`, `mkdir`, `chmod` |
| **Bash - Directory/Git** | `pwd`, `git init`, `git status` |
| **Bash - Process** | `ps`, `sleep` |
| **Server Management** | `manage_server (status)`, `manage_server (start)`, `manage_server (stop)` |
| **Browser Automation** | `browser_navigate`, `browser_screenshot`, `browser_click`, `browser_fill`, `browser_evaluate`, `browser_close` |
| **Security (blocked)** | `rm`, `mv`, `curl`, `wget` |
| **Error Handling** | file not found, directory not found, command exit codes, false positive check (file with "Error" in content) |

## Generated Project Structure

After running, the project directory contains:

```
my_project/
├── feature_list.json         # Test cases (source of truth)
├── app_spec.txt              # Copied specification
├── init.sh                   # Environment setup script
├── progress.txt              # Session progress notes
├── logs/                     # Agent session logs
│   └── agent_session_*.log   # Timestamped log files
└── [application files]       # Generated application code
```

## Key Design Principles

1. **Defense in depth** - Multiple security layers (filesystem + allowlist)
2. **Session persistence** - Progress saved via `feature_list.json` and git commits
3. **Fresh context windows** - Each session starts clean (no memory pollution)
4. **Browser-based testing** - Mandatory Playwright verification (no curl-only testing)
5. **Immutable test specs** - Never remove/edit features, only mark as passing

## Usage Examples

### Start a new project
```bash
python autonomous_agent.py --project-dir ./my_project
```

### Use a specific model
```bash
python autonomous_agent.py --project-dir ./my_project --model openai/gpt-4o
python autonomous_agent.py --project-dir ./my_project --model google/gemini-pro-1.5
python autonomous_agent.py --project-dir ./my_project --model meta-llama/llama-3.1-70b-instruct
```

### Limit iterations for testing
```bash
python autonomous_agent.py --project-dir ./my_project --max-iterations 3
```

### Validate agent setup
```bash
python validate_agent.py --test      # Live test
python validate_agent.py --commands  # Command tests
```

---

*Last Updated: November 30, 2025*
