# Obsidian Bridge

Integration between RE:GE and Obsidian note-taking application.

## Overview

The Obsidian bridge enables bidirectional sync between RE:GE fragments and Obsidian markdown notes. Fragments are exported with YAML frontmatter containing RE:GE metadata.

## Setup

### Prerequisites

1. An Obsidian vault (folder with `.obsidian/` directory)
2. RE:GE installed (`pip install rege`)

### Configuration

```bash
# Connect to Obsidian vault
rege bridge connect obsidian --path /path/to/vault

# Or set via environment variable
export REGE_BRIDGE_OBSIDIAN_PATH=/path/to/vault
rege bridge connect obsidian
```

## Vault Structure

When connected, the bridge creates these folders in your vault:

```
vault/
├── .obsidian/           # Obsidian config
├── ORG_BODIES/          # Organ documentation
├── FRAGMENTS/           # RE:GE fragments
├── ARCHIVE/             # Archived items
├── CANON/               # Canonized events
├── INVOCATIONS/         # Invocation logs
└── TEMPLATES/           # Ritual templates
```

## Usage

### Exporting Fragments

```bash
# Export single fragment
rege export obsidian --fragment FRAG_001

# Export all fragments
rege export obsidian --all
```

### Fragment Markdown Format

Exported fragments include YAML frontmatter:

```markdown
---
id: FRAG_abc123
name: My Fragment
charge: 75
status: active
version: 1.0
tags: [CANON+, ARCHIVE+]
created_at: 2024-01-15T10:30:00
source: RE:GE
---

# My Fragment

**Charge:** 75
**Status:** active

**Tags:** CANON+, ARCHIVE+

## Metadata

- **author:** system
- **context:** ritual
```

### Importing from Obsidian

```bash
# Import all fragments from vault
rege import obsidian

# Preview what would be imported
rege import obsidian --dry-run

# Import specific file
rege import obsidian --file path/to/note.md
```

### Bidirectional Sync

```python
from rege.bridges import get_bridge_registry

registry = get_bridge_registry()
bridge = registry.get_bridge("obsidian")

# Sync to vault
result = bridge.sync_to_vault(fragments)

# Sync from vault
result = bridge.sync_from_vault()
```

## Python API

```python
from rege.bridges.obsidian import ObsidianBridge

# Create and configure bridge
bridge = ObsidianBridge(config={"vault_path": "/path/to/vault"})

# Connect
if bridge.connect():
    print("Connected to vault")

# Export fragment
result = bridge.send({
    "fragment": {
        "id": "FRAG_001",
        "name": "Test Fragment",
        "charge": 65,
        "tags": ["ARCHIVE+"],
    }
})

# Import from vault
data = bridge.receive()
fragments = data.get("fragments", [])

# Disconnect
bridge.disconnect()
```

## Conflict Resolution

When syncing, conflicts are resolved by timestamp:

1. Compare `updated_at` timestamps
2. Newer version wins
3. Older version is backed up to `ARCHIVE/`

Override with `--force` flag to always overwrite:

```bash
rege export obsidian --all --force
```

## Templates

The bridge creates templates in `TEMPLATES/`:

- `ritual_invocation.md` - Template for invoking rituals
- `fragment_creation.md` - Template for new fragments
- `daily_note.md` - Daily notes with RE:GE sections

## Troubleshooting

### "Not an Obsidian vault"

Ensure the path contains a `.obsidian/` folder. If creating a new vault, open it in Obsidian first.

### "Permission denied"

Check file permissions on the vault directory.

### Sync not updating

Clear the sync cache:

```python
bridge._last_sync = None
result = bridge.sync_from_vault()
```
