# RE:GE CLI Command Reference

Complete reference for all RE:GE command-line interface commands.

## Installation

```bash
pip install rege
# or
pip install -e .  # For development
```

## Basic Usage

```bash
rege [command] [options]
```

## Commands

### invoke

Execute a ritual invocation.

```bash
# Direct invocation
rege invoke "::CALL_ORGAN HEART_OF_CANON ::WITH my_symbol ::MODE assess"

# From file
rege invoke --file invocation.txt

# With options
rege invoke "..." --charge 75 --depth standard --json
```

**Options:**
- `--file, -f` - Read invocation from file
- `--charge, -c` - Override charge level (0-100)
- `--depth, -d` - Set depth level (light/standard/extended/full)
- `--json, -j` - Output as JSON

### status

Show system status.

```bash
rege status
rege status --json
```

### fragments

Manage fragments.

```bash
# List all fragments
rege fragments list
rege fragments list --json

# Show specific fragment
rege fragments show FRAG_001

# Create new fragment
rege fragments create "Fragment Name" --charge 65 --tags "CANON+,ARCHIVE+"
```

### checkpoint

Manage system checkpoints.

```bash
# Create checkpoint
rege checkpoint create
rege checkpoint create --name "before_major_change"

# List checkpoints
rege checkpoint list

# Restore checkpoint
rege checkpoint restore CHECKPOINT_ID
```

### recover

System recovery operations.

```bash
# View recovery status
rege recover

# Execute recovery
rege recover --mode standard
rege recover --mode emergency --confirm
```

### repl

Interactive REPL mode.

```bash
rege repl
```

**REPL Commands:**
- `:help` - Show help
- `:status` - Show system status
- `:organs` - List available organs
- `:modes <organ>` - List modes for organ
- `:last` - Show last result
- `:vars` - Show session variables
- `:set <var> <value>` - Set session variable
- `:history` - Show command history
- `:clear` - Clear screen
- `:load <file>` - Execute invocations from file
- `:export <file>` - Export session to file
- `:quit` - Exit REPL

### laws

Manage system laws.

```bash
# List all laws
rege laws list
rege laws list --active-only

# Show specific law
rege laws show LAW_01

# Activate/deactivate law
rege laws activate LAW_01
rege laws deactivate LAW_01

# View violations
rege laws violations
```

### fusion

Manage fragment fusions.

```bash
# List fusions
rege fusion list
rege fusion list --active-only

# Show fusion details
rege fusion show FUSE_001

# Rollback fusion
rege fusion rollback FUSE_001 --confirm

# Show eligible fragments
rege fusion eligible
```

### depth

View depth tracking.

```bash
# View status
rege depth status

# View limits
rege depth limits

# View exhaustion log
rege depth log

# Clear log
rege depth clear-log --confirm
```

### queue

Manage the Soul Patchbay queue.

```bash
# List queue contents
rege queue list
rege queue list --priority critical

# View statistics
rege queue stats

# Process items
rege queue process 5

# Clear queue
rege queue clear --confirm
```

### batch

Execute multiple invocations from file.

```bash
# Execute batch
rege batch invocations.txt

# Dry run
rege batch invocations.txt --dry-run

# Continue on errors
rege batch invocations.txt --continue-on-error
```

**Batch file format:**
```
# Comment lines start with #
::CALL_ORGAN HEART_OF_CANON
::WITH symbol1
::MODE assess

::CALL_ORGAN ARCHIVE_ORDER
::WITH symbol2
::MODE store
```

### bridge

Manage external bridges.

```bash
# List available bridges
rege bridge list

# Connect to bridge
rege bridge connect obsidian --path /path/to/vault
rege bridge connect git --path /path/to/repo
rege bridge connect maxmsp --host localhost --port 7400

# Disconnect
rege bridge disconnect obsidian

# View status
rege bridge status

# View/set config
rege bridge config obsidian
```

### export

Export data to external systems.

```bash
# Export to Obsidian
rege export obsidian --fragment FRAG_001
rege export obsidian --all
```

### import

Import data from external systems.

```bash
# Import from Obsidian
rege import obsidian
rege import obsidian --file /path/to/note.md
rege import obsidian --dry-run
```

### chain

Manage ritual chains (workflow orchestration).

```bash
# List chains
rege chain list

# Show chain details
rege chain show canonization_ceremony

# Execute chain
rege chain run canonization_ceremony
rege chain run canonization_ceremony --context '{"charge": 80}'
rege chain run canonization_ceremony --dry-run
rege chain run canonization_ceremony --step

# View history
rege chain history
rege chain history --chain-name canonization_ceremony

# View statistics
rege chain stats
```

## Global Options

These options work with most commands:

- `--json, -j` - Output as JSON
- `--help` - Show help for command

## Environment Variables

- `REGE_CONFIG` - Path to configuration file
- `REGE_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `REGE_BRIDGE_OBSIDIAN_PATH` - Default Obsidian vault path
- `REGE_BRIDGE_GIT_PATH` - Default Git repository path
- `REGE_BRIDGE_MAXMSP_HOST` - Default Max/MSP host
- `REGE_BRIDGE_MAXMSP_PORT` - Default Max/MSP port

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid arguments
- `3` - Resource not found
- `4` - Permission denied
