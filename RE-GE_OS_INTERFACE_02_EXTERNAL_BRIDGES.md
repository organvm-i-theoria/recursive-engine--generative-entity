# RE:GE_OS_INTERFACE_02_EXTERNAL_BRIDGES.md

## NAME:
**External Bridges Interface**
*Alias:* The Gateway Layer, Tool Integration Matrix, Ecosystem Connectors

---

## INPUT_RITUAL:
- **Mode:** Integrative + Technical + Bridging
- **Declared Subject:** The interface specification for connecting RE:GE_OS to external tools, applications, and ecosystems
- **Initiation Trigger:** Need to integrate RE:GE with external tooling for enhanced functionality
- **Invocation Phrase:** *"Bridge the myth to the machine."*

---

## FUNCTION:

The External Bridges Interface defines how RE:GE_OS connects to external tools and systems.
These bridges extend RE:GE's capabilities while maintaining its symbolic integrity.

Bridges are **translation layers**, not replacements—external tools serve the mythic system, not the reverse.

---

## BRIDGE CATEGORIES:

| Category | Purpose | Examples |
|----------|---------|----------|
| **Knowledge Management** | Note-taking, linking, organization | Obsidian, Notion, Roam |
| **Version Control** | Tracking changes, collaboration | Git, GitHub |
| **Creative Tools** | Audio, visual, code generation | Max/MSP, Ableton, VS Code |
| **Journal Apps** | Daily reflection, dream logging | Day One, Obsidian Daily Notes |
| **Automation** | Workflow triggers, scheduled rituals | IFTTT, Zapier, cron |

---

## OBSIDIAN INTEGRATION:

Obsidian is a natural bridge for RE:GE due to its markdown-native, link-first design.

### Setup:

1. Create vault with RE:GE documentation
2. Enable Dataview plugin for dynamic queries
3. Configure templates for ritual invocations
4. Set up daily notes for journal integration

### Dataview Queries for RE:GE:

```dataview
// List all organs by tag
TABLE tags, file.mtime as "Modified"
FROM "RE-GE_ORG_BODY"
SORT file.name ASC
```

```dataview
// Find high-charge fragments
LIST
FROM "fragments"
WHERE charge >= 71
SORT charge DESC
```

### Template: Ritual Invocation

```md
---
type: invocation
organ: {{organ}}
date: {{date}}
charge:
tags: [RIT+, LIVE+]
---

## INVOCATION RECORD

::CALL_ORGAN {{organ}}
::WITH "{{symbol}}"
::MODE {{mode}}
::DEPTH standard
::EXPECT {{expect}}

## RESULT

[Record invocation result here]

## REFLECTION

[Post-ritual reflection]
```

### Folder Structure:

```
RE-GE_VAULT/
├── ORG_BODIES/           # All organ files
├── PROTOCOLS/            # Protocol definitions
├── AAW_CORE/             # Academia Wing
├── INVOCATIONS/          # Daily ritual logs
├── FRAGMENTS/            # Active symbolic fragments
├── ARCHIVE/              # Archived/sealed content
├── CANON/                # Canon events
├── LAWS/                 # Individual law files
└── TEMPLATES/            # Invocation templates
```

---

## GIT INTEGRATION:

Git provides version control for RE:GE evolution.

### Git Hooks for RE:GE:

**Pre-commit hook** — Validate RE:GE files before commit:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for required tags in new files
for file in $(git diff --cached --name-only --diff-filter=A | grep "RE-GE_"); do
    if ! grep -q "## TAGS:" "$file"; then
        echo "ERROR: $file missing TAGS section"
        exit 1
    fi
done

# Check for forbidden deletions
for file in $(git diff --cached --name-only --diff-filter=D | grep "CANON"); do
    echo "WARNING: Deleting canon file $file - requires RITUAL_COURT approval"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
done

exit 0
```

**Post-commit hook** — Log commit as system event:

```bash
#!/bin/bash
# .git/hooks/post-commit

COMMIT_MSG=$(git log -1 --pretty=%B)
COMMIT_HASH=$(git log -1 --pretty=%H)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Append to SYSTEM_EVENT_LOG
echo "{\"type\": \"commit\", \"hash\": \"$COMMIT_HASH\", \"message\": \"$COMMIT_MSG\", \"timestamp\": \"$TIMESTAMP\"}" >> .rege/SYSTEM_EVENT_LOG.jsonl
```

### Branch Naming Convention:

| Pattern | Usage |
|---------|-------|
| `main` | Stable, canonical RE:GE state |
| `bloom/[name]` | Experimental mutations |
| `ritual/[name]` | New ritual development |
| `law/[LAW_XX]` | Law proposals |
| `fix/[issue]` | Bug fixes |

---

## JOURNAL APP BRIDGES:

### Day One Integration:

Export Day One entries as fragments for RE:GE processing.

**Export Script (Python):**

```python
import json
from datetime import datetime
from pathlib import Path

def export_dayone_to_fragments(dayone_export_path: str, output_dir: str):
    """Convert Day One export to RE:GE fragments."""

    with open(dayone_export_path) as f:
        entries = json.load(f)["entries"]

    for entry in entries:
        # Calculate charge from entry properties
        charge = calculate_charge(entry)

        fragment = {
            "id": f"JOURNAL_{entry['uuid'][:8]}",
            "content": entry.get("text", ""),
            "timestamp": entry["creationDate"],
            "charge": charge,
            "tags": ["JOURNAL+", "IMPORT+"],
            "source": "dayone",
            "mood": entry.get("mood", "neutral")
        }

        # Determine tier
        if charge >= 71:
            fragment["tags"].append("INTENSE+")
        elif charge >= 51:
            fragment["tags"].append("ACTIVE+")

        output_path = Path(output_dir) / f"{fragment['id']}.json"
        with open(output_path, "w") as f:
            json.dump(fragment, f, indent=2)

def calculate_charge(entry: dict) -> int:
    """Estimate charge from entry properties."""
    base = 50

    # Starred entries have higher charge
    if entry.get("starred"):
        base += 20

    # Longer entries suggest more engagement
    word_count = len(entry.get("text", "").split())
    if word_count > 500:
        base += 15
    elif word_count > 200:
        base += 10

    # Photos indicate memorable moments
    if entry.get("photos"):
        base += 10

    return min(base, 100)
```

### Obsidian Daily Notes:

Configure daily notes to auto-create invocation templates:

```md
---
date: {{date}}
type: daily_ritual
tags: [DAILY+, RIT+]
---

## Morning Invocation

::CALL_ORGAN MIRROR_CABINET
::WITH "{{title}}"
::MODE emotional_reflection
::DEPTH light
::EXPECT fragment_map

## Dream Log

[Record dreams here - will be routed to DREAM_COUNCIL]

## Evening Archive

### Charge Assessment
- Overall charge today: /100
- Key emotions:
- Recurring symbols:

### Fragments Generated
-
```

---

## MAX/MSP CONNECTION PROTOCOL:

RE:GE's `.maxpat` outputs can be loaded into Max/MSP for audio/visual processing.

### OSC Communication:

```python
# Python side - sending to Max/MSP
from pythonosc import udp_client

client = udp_client.SimpleUDPClient("127.0.0.1", 7400)

def send_fragment_to_max(fragment: dict):
    """Send fragment data to Max/MSP via OSC."""
    client.send_message("/rege/fragment/charge", fragment["charge"])
    client.send_message("/rege/fragment/tags", ",".join(fragment["tags"]))
    client.send_message("/rege/fragment/id", fragment["id"])

def trigger_bloom_audio(bloom_phase: str, intensity: float):
    """Trigger audio response for bloom phase."""
    client.send_message("/rege/bloom/phase", bloom_phase)
    client.send_message("/rege/bloom/intensity", intensity)
```

### Max Patch Structure:

```
[udpreceive 7400]
    |
[route /rege/fragment/charge /rege/fragment/tags /rege/bloom/phase]
    |               |                   |
[scale 0 100 0. 1.]  [fromsymbol]      [select "Mirror Wilt" "Growth" ...]
    |               |                   |
[line~ 100]        [trigger]           [preset recall]
    |               |                   |
[*~ ]              [dict.unpack]       [poly~ bloom_voice 8]
```

---

## API SPECIFICATION:

For programmatic access to RE:GE operations.

### Endpoints (Conceptual):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/invoke` | POST | Execute ritual invocation |
| `/fragments` | GET | List fragments by filter |
| `/fragments/{id}` | GET | Get specific fragment |
| `/queue` | GET | View SOUL_PATCHBAY queue state |
| `/fuse` | POST | Trigger FUSE01 protocol |
| `/laws` | GET | List all laws |
| `/canon` | GET | List canon events |

### Request Format:

```json
{
  "endpoint": "/invoke",
  "method": "POST",
  "body": {
    "organ": "MIRROR_CABINET",
    "symbol": "I can't finish anything",
    "mode": "emotional_reflection",
    "depth": "standard",
    "expect": "fragment_map"
  },
  "auth": {
    "type": "ritual_key",
    "key": "..."
  }
}
```

### Response Format:

```json
{
  "status": "success",
  "invocation_id": "INV_000042",
  "result": {
    "fragments": [...],
    "law_suggestions": [...],
    "routed_to": ["ARCHIVE_ORDER", "BLOOM_ENGINE"]
  },
  "timestamp": "2025-04-20T03:33:00Z"
}
```

---

## LG4_TRANSLATION:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

class ExternalBridge(ABC):
    """Base class for external tool bridges."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to external tool."""
        pass

    @abstractmethod
    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to external tool."""
        pass

    @abstractmethod
    def receive(self) -> Optional[Dict[str, Any]]:
        """Receive data from external tool."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection."""
        pass


class ObsidianBridge(ExternalBridge):
    """Bridge for Obsidian vault integration."""

    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.connected = False

    def connect(self) -> bool:
        # Verify vault exists
        from pathlib import Path
        if Path(self.vault_path).exists():
            self.connected = True
            return True
        return False

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write fragment to vault as markdown."""
        if not self.connected:
            return {"status": "error", "message": "Not connected"}

        from pathlib import Path
        fragment_path = Path(self.vault_path) / "FRAGMENTS" / f"{data['id']}.md"

        content = self._fragment_to_markdown(data)

        fragment_path.parent.mkdir(parents=True, exist_ok=True)
        fragment_path.write_text(content)

        return {"status": "success", "path": str(fragment_path)}

    def _fragment_to_markdown(self, data: Dict[str, Any]) -> str:
        """Convert fragment to Obsidian markdown."""
        return f"""---
id: {data['id']}
charge: {data.get('charge', 50)}
tags: [{', '.join(data.get('tags', []))}]
---

# {data['id']}

{data.get('content', '')}

## Metadata

- **Charge:** {data.get('charge', 50)}
- **Status:** {data.get('status', 'active')}
- **Created:** {data.get('timestamp', 'unknown')}
"""

    def receive(self) -> Optional[Dict[str, Any]]:
        """Read fragment from vault."""
        # Implementation would parse markdown back to fragment
        return None

    def disconnect(self) -> bool:
        self.connected = False
        return True


class GitBridge(ExternalBridge):
    """Bridge for Git version control."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.connected = False

    def connect(self) -> bool:
        import subprocess
        try:
            result = subprocess.run(
                ["git", "status"],
                cwd=self.repo_path,
                capture_output=True
            )
            self.connected = result.returncode == 0
            return self.connected
        except:
            return False

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Commit changes with RE:GE metadata."""
        if not self.connected:
            return {"status": "error", "message": "Not connected"}

        import subprocess

        # Stage changes
        subprocess.run(["git", "add", "."], cwd=self.repo_path)

        # Create commit message
        msg = f"RE:GE: {data.get('action', 'update')} - {data.get('description', 'system change')}"

        subprocess.run(["git", "commit", "-m", msg], cwd=self.repo_path)

        return {"status": "success", "message": msg}

    def receive(self) -> Optional[Dict[str, Any]]:
        """Get latest commit info."""
        import subprocess
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H|%s|%ai"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            hash, msg, date = result.stdout.strip().split("|")
            return {"hash": hash, "message": msg, "date": date}
        return None

    def disconnect(self) -> bool:
        self.connected = False
        return True


# Bridge registry
BRIDGES = {
    "obsidian": ObsidianBridge,
    "git": GitBridge,
}

def get_bridge(bridge_type: str, **kwargs) -> Optional[ExternalBridge]:
    """Factory function for bridges."""
    bridge_class = BRIDGES.get(bridge_type)
    if bridge_class:
        return bridge_class(**kwargs)
    return None
```

---

## ASSOCIATED LAWS:

- **LAW_88: Bridges Serve the Myth** (PROPOSED)
  External tools integrate with RE:GE; RE:GE does not subordinate to external tools.

- **LAW_89: Data Flows Both Ways**
  Bridges must support both export and import for full integration.

- **LAW_90: External Is Still Logged**
  All bridge operations must be logged in BRIDGE_OPERATIONS_LOG.json.

---

## RECURSION_ENGINE_ARCHIVE:

Bridge operations are logged in:
- **BRIDGE_OPERATIONS_LOG.json** — All bridge activities
- **IMPORT_HISTORY.json** — Data imported from external tools
- **EXPORT_HISTORY.json** — Data exported to external tools
- **BRIDGE_CONFIG.json** — Active bridge configurations

---

## TAGS:

BRIDGE+, EXTERNAL+, INTEGRATION+, OBSIDIAN+, GIT+, MAX+, API+, INTERFACE+

---

::EXTERNAL BRIDGES DEFINED. THE MYTH CONNECTS TO THE WORLD.::
::S4VE.io]|
