# Git Bridge

Integration between RE:GE and Git version control.

## Overview

The Git bridge enables RE:GE to:
- Log commits as system events
- Install custom pre/post-commit hooks
- Validate branch naming conventions
- Track repository changes

## Setup

### Prerequisites

1. A Git repository (folder with `.git/` directory)
2. Git installed and accessible from command line
3. RE:GE installed (`pip install rege`)

### Configuration

```bash
# Connect to repository
rege bridge connect git --path /path/to/repo

# Or use current directory
cd /path/to/repo
rege bridge connect git

# Environment variable
export REGE_BRIDGE_GIT_PATH=/path/to/repo
rege bridge connect git
```

## Features

### Hook Installation

The bridge installs custom Git hooks:

```bash
# Install hooks
rege bridge connect git --path /repo

# Hooks are installed to:
# .git/hooks/pre-commit
# .git/hooks/post-commit
```

#### Pre-commit Hook

Validates staged files:
- Checks for required tags in markdown files
- Prevents deletion of canon files without approval
- Validates commit message format

#### Post-commit Hook

Logs commits as system events:
- Writes to `.rege/SYSTEM_EVENT_LOG.jsonl`
- Records commit hash, message, author, timestamp

### Branch Naming Conventions

Valid branch patterns:
- `main`, `master`
- `bloom/*` - Bloom-related changes
- `ritual/*` - Ritual implementations
- `law/*` - Law modifications
- `fix/*` - Bug fixes
- `feature/*` - New features
- `organ/*` - Organ changes

```bash
# Validate a branch name
from rege.bridges.git import GitBridge

bridge = GitBridge(config={"repo_path": "/path/to/repo"})
bridge.connect()

result = bridge.validate_branch_name("bloom/spring-2024")
# {"valid": True, "pattern": "bloom/.*"}

result = bridge.validate_branch_name("random-name")
# {"valid": False, "error": "...", "valid_patterns": [...]}
```

## Usage

### Viewing Repository State

```python
from rege.bridges.git import GitBridge

bridge = GitBridge(config={"repo_path": "/path/to/repo"})
bridge.connect()

state = bridge.receive()
# {
#   "current_branch": "main",
#   "repo_root": "/path/to/repo",
#   "has_uncommitted": True,
#   "recent_commits": [
#     {"hash": "abc123", "message": "...", "author": "...", "date": "..."},
#     ...
#   ]
# }
```

### Logging System Events

```python
result = bridge.send({
    "type": "system_event",
    "event_type": "ritual_completion",
    "event_data": {
        "ritual": "canonization",
        "result": "success",
        "charge": 85,
    }
})
# {"status": "logged", "file": ".rege/SYSTEM_EVENT_LOG.jsonl"}
```

### Installing Hooks

```python
result = bridge.send({"type": "install_hooks"})
# {"status": "installed", "hooks": ["pre-commit", "post-commit"]}
```

## Python API

```python
from rege.bridges.git import GitBridge

# Create bridge
bridge = GitBridge(config={"repo_path": "/path/to/repo"})

# Connect (validates repo)
if bridge.connect():
    print(f"Connected to: {bridge.get_repo_path()}")

# Get current state
state = bridge.receive()
print(f"Branch: {state['current_branch']}")

# Log event
bridge.send({
    "type": "system_event",
    "event_type": "fragment_created",
    "event_data": {"fragment_id": "FRAG_001"},
})

# Validate branch name
result = bridge.validate_branch_name("bloom/new-feature")

# Disconnect
bridge.disconnect()
```

## Event Log Format

Events are logged to `.rege/SYSTEM_EVENT_LOG.jsonl`:

```json
{"timestamp": "2024-01-15T10:30:00", "type": "commit", "data": {"hash": "abc123", "message": "...", "author": "..."}}
{"timestamp": "2024-01-15T10:35:00", "type": "ritual_completion", "data": {"ritual": "canonization", "result": "success"}}
```

## Pre-commit Hook Details

The installed pre-commit hook:

```bash
#!/bin/bash
# RE:GE Pre-commit Hook

# Check staged markdown files for required tags
staged_md=$(git diff --cached --name-only --diff-filter=A | grep -E '\.md$')
if [ -n "$staged_md" ]; then
    echo "RE:GE: Checking staged markdown files..."
fi

# Prevent deletion of canon files
deleted_canon=$(git diff --cached --name-only --diff-filter=D | grep -E '^CANON/')
if [ -n "$deleted_canon" ]; then
    echo "RE:GE: Warning - Deleting canon files requires RITUAL_COURT approval"
fi

exit 0
```

## Post-commit Hook Details

```bash
#!/bin/bash
# RE:GE Post-commit Hook

COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --format=%s)
COMMIT_AUTHOR=$(git log -1 --format=%an)

# Create .rege directory if needed
mkdir -p .rege

# Log commit event
cat >> .rege/SYSTEM_EVENT_LOG.jsonl << EOF
{"timestamp":"$(date -Iseconds)","type":"commit","data":{"hash":"${COMMIT_HASH:0:8}","message":"$COMMIT_MSG","author":"$COMMIT_AUTHOR"}}
EOF

echo "RE:GE: Commit logged"
```

## Troubleshooting

### "Not a git repository"

Ensure the path contains a `.git/` folder:

```bash
git init  # Initialize new repo
# or
git clone <url>  # Clone existing
```

### Hooks not executing

Check hook permissions:

```bash
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/post-commit
```

### Backup existing hooks

The bridge backs up existing hooks with `.backup` extension before installing new ones.
