# RE:GE Data Models Reference

This document describes the core data models used throughout RE:GE.

## Fragment

The fundamental unit of data in RE:GE.

```python
from rege.core.models import Fragment

# Create a fragment
fragment = Fragment(
    name="My Fragment",
    charge=65,
    tags=["CANON+", "ARCHIVE+"],
    status="active",
    metadata={"source": "user_input"},
)

# Access properties
print(fragment.id)        # Auto-generated UUID
print(fragment.name)      # "My Fragment"
print(fragment.charge)    # 65
print(fragment.tags)      # ["CANON+", "ARCHIVE+"]
print(fragment.status)    # "active"
print(fragment.created_at)  # ISO timestamp

# Serialize
data = fragment.to_dict()

# Deserialize
restored = Fragment.from_dict(data)
```

### Fragment Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique identifier (auto-generated if empty) |
| `name` | str | Human-readable name |
| `charge` | int | Charge level (0-100) |
| `tags` | List[str] | Associated tags |
| `status` | str | Current status ("active", "archived", "latent") |
| `version` | str | Version string |
| `created_at` | str | ISO timestamp of creation |
| `updated_at` | str | ISO timestamp of last update |
| `metadata` | Dict | Additional metadata |

## Invocation

Represents a ritual invocation to an organ.

```python
from rege.core.models import Invocation, DepthLevel

invocation = Invocation(
    organ="HEART_OF_CANON",
    mode="assess_candidate",
    input_symbol="my_symbol",
    depth=DepthLevel.STANDARD,
    charge=75,
    flags=["CANON+"],
)

# Access fields
print(invocation.organ)       # "HEART_OF_CANON"
print(invocation.mode)        # "assess_candidate"
print(invocation.depth)       # DepthLevel.STANDARD
print(invocation.invocation_id)  # Auto-generated
```

### Invocation Fields

| Field | Type | Description |
|-------|------|-------------|
| `invocation_id` | str | Unique identifier |
| `organ` | str | Target organ name |
| `mode` | str | Operation mode |
| `input_symbol` | str | Input data/symbol |
| `depth` | DepthLevel | Processing depth |
| `charge` | int | Charge level |
| `flags` | List[str] | Additional flags |
| `expect` | str | Expected output format |

## DepthLevel

Enum for processing depth limits.

```python
from rege.core.models import DepthLevel

# Available levels
DepthLevel.LIGHT      # Light processing (3 levels)
DepthLevel.STANDARD   # Standard processing (7 levels)
DepthLevel.EXTENDED   # Extended processing (12 levels)
DepthLevel.FULL       # Full spiral (21 levels)
DepthLevel.EMERGENCY  # Emergency mode (33 levels)
```

## Patch

Represents a patch in the Soul Patchbay queue.

```python
from rege.core.models import Patch, PatchStatus

patch = Patch(
    invocation=invocation,
    priority=7,
    status=PatchStatus.QUEUED,
)

# Patches are comparable for priority queue
patches = [patch1, patch2, patch3]
patches.sort()  # Sorted by priority (higher first)
```

### Patch Fields

| Field | Type | Description |
|-------|------|-------------|
| `patch_id` | str | Unique identifier |
| `invocation` | Invocation | The wrapped invocation |
| `priority` | int | Queue priority (higher = sooner) |
| `status` | PatchStatus | Current status |
| `queued_at` | str | Timestamp when queued |
| `processed_at` | str | Timestamp when processed |

### PatchStatus

```python
from rege.core.models import PatchStatus

PatchStatus.QUEUED     # Waiting in queue
PatchStatus.PROCESSING # Currently being processed
PatchStatus.COMPLETED  # Processing complete
PatchStatus.FAILED     # Processing failed
PatchStatus.CANCELLED  # Cancelled before processing
```

## FusedFragment

Represents multiple fragments fused together.

```python
from rege.core.models import FusedFragment

fused = FusedFragment(
    fused_id="FUSE_001",
    source_fragments=[fragment1, fragment2],
    output_route="ARCHIVE_ORDER",
    charge=85,
)

# Check rollback
if fused.rollback_available:
    # Can rollback fusion
    pass
```

### FusedFragment Fields

| Field | Type | Description |
|-------|------|-------------|
| `fused_id` | str | Unique fusion identifier |
| `source_fragments` | List[Fragment] | Original fragments |
| `output_route` | str | Destination organ |
| `charge` | int | Combined charge |
| `status` | str | Fusion status |
| `rollback_available` | bool | Can be rolled back |
| `rollback_deadline` | str | Deadline for rollback |
| `fused_at` | str | Timestamp of fusion |

## CanonEvent

Represents a canonized event in the system.

```python
from rege.core.models import CanonEvent

event = CanonEvent(
    name="Major Canon Event",
    charge=92,
    linked_nodes=["node1", "node2"],
    tags=["CANON+", "RITUAL+"],
)

# Event ID is auto-generated
print(event.event_id)
print(event.canonized_at)  # Set when canonized
```

### CanonEvent Fields

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | str | Unique identifier |
| `name` | str | Event name |
| `charge` | int | Event charge |
| `linked_nodes` | List[str] | Related nodes |
| `tags` | List[str] | Event tags |
| `canonized_at` | str | Canonization timestamp |
| `metadata` | Dict | Additional data |

## StateSnapshot

Represents a system state snapshot for recovery.

```python
from rege.core.models import StateSnapshot, RecoveryTrigger

snapshot = StateSnapshot(
    trigger=RecoveryTrigger.PANIC_CAPTURE,
    organ_states={"HEART_OF_CANON": {...}},
    queue_state={"pending": 5},
)
```

### RecoveryTrigger

```python
from rege.core.models import RecoveryTrigger

RecoveryTrigger.PANIC_CAPTURE    # Emergency capture
RecoveryTrigger.SCHEDULED        # Scheduled backup
RecoveryTrigger.USER_REQUESTED   # Manual request
RecoveryTrigger.DEPTH_EXCEEDED   # Depth limit triggered
RecoveryTrigger.SYSTEM_ERROR     # Error recovery
```

## Charge Tiers

Charge levels are grouped into tiers:

```python
from rege.core.constants import ChargeTier, CHARGE_THRESHOLDS

# Tiers
ChargeTier.LATENT      # 0-25: Background, minimal processing
ChargeTier.PROCESSING  # 26-50: Active consideration
ChargeTier.ACTIVE      # 51-70: Full engagement
ChargeTier.INTENSE     # 71-85: Canon candidate
ChargeTier.CRITICAL    # 86-100: Immediate action required

# Get tier for a charge value
from rege.core.constants import get_charge_tier
tier = get_charge_tier(75)  # Returns ChargeTier.INTENSE
```

## Tag System

Standard tags for content classification:

| Tag | Purpose |
|-----|---------|
| `CANON+` | Canon-related content |
| `ECHO+` | Echoed/repeated content |
| `ARCHIVE+` | For archival |
| `VOLATILE+` | Temporary/unstable |
| `RITUAL+` | Ritual-related |
| `MIRROR+` | Reflection content |
| `REMIX+` | Remixed content |
| `MASK+` | Identity/persona related |
| `FUSE+` | Fusion-related |
