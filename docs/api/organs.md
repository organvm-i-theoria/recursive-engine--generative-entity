# RE:GE Organ API Reference

This document provides the API reference for RE:GE organs (organizational bodies).

## Overview

Organs are the functional units of the RE:GE system. Each organ handles specific types of invocations and provides specialized processing capabilities.

## Base Organ Interface

All organs extend the `OrganHandler` base class:

```python
from rege.organs.base import OrganHandler

class MyOrgan(OrganHandler):
    def process(self, invocation: Invocation) -> Dict[str, Any]:
        """Process an invocation and return results."""
        pass

    def get_modes(self) -> List[str]:
        """Return list of supported modes."""
        pass
```

## Organ Registry

The organ registry manages all available organs:

```python
from rege.organs.registry import get_organ_registry, register_default_organs

# Register all default organs
register_default_organs()

# Get the registry
registry = get_organ_registry()

# Check if an organ exists
exists = registry.has_organ("HEART_OF_CANON")

# Get an organ handler
handler = registry.get_organ("HEART_OF_CANON")

# List all organs
organs = registry.list_organs()
```

## Core Organs

### HEART_OF_CANON

The central mythology and canon event handler.

**Modes:**
- `assess_candidate` - Assess fragment for canon worthiness
- `detect_conflict` - Detect contradictions in canon
- `create` - Create new canon event

**Example:**
```python
invocation = Invocation(
    organ="HEART_OF_CANON",
    mode="assess_candidate",
    input_symbol="fragment to assess",
    charge=75,
)
result = dispatcher.dispatch(invocation)
```

### RITUAL_COURT

Ceremonial logic and contradiction resolution.

**Modes:**
- `deliberate` - Deliberate on ceremonial matter
- `judge_conflict` - Judge a contradiction
- `grief_ritual` - Process grief
- `closure` - Perform closure ritual
- `emergency_declaration` - Declare system emergency
- `shelter` - Provide ritual shelter

### ARCHIVE_ORDER

Storage and retrieval operations.

**Modes:**
- `store` - Store data
- `record` - Record an event
- `verify` - Verify system state
- `panic_capture` - Capture panic snapshot
- `check_versions` - Check version consolidation
- `record_bloom` - Record bloom event
- `record_resolution` - Record resolution event
- `auto_tag` - Automatically assign tags

### BLOOM_ENGINE

Generative growth and mutation.

**Modes:**
- `mutate` - Apply mutations
- `synthesize` - Generate synthesis
- `calculate_season` - Calculate bloom phase
- `calculate_charge` - Calculate charge
- `schedule_decay` - Schedule decay processing

### FUSE01

Fragment fusion protocol.

**Modes:**
- `merge` - Merge fragments
- `resolve_conflict` - Resolve conflict through fusion
- `consolidate` - Consolidate versions
- `emergency_fuse` - Emergency fusion

### MIRROR_CABINET

Reflection and interpretation.

**Modes:**
- `reflect_grief` - Reflect on grief
- `interpret` - Interpret symbols

### DREAM_COUNCIL

Collective processing and prophecy.

**Modes:**
- `collective_process` - Process collectively
- `prophesy` - Generate prophecy

### CODE_FORGE

Symbol-to-code translation.

**Modes:**
- `create_glyph` - Create symbolic glyph
- `translate` - Translate symbols to code

### RECOVERY

System recovery operations.

**Modes:**
- `execute` - Execute recovery protocol
- `snapshot` - Create recovery snapshot

### SOUL_PATCHBAY

Modular routing hub.

**Modes:**
- `route` - Route invocation to appropriate organ
- `queue` - Add to processing queue

## Creating Custom Organs

To create a custom organ:

```python
from rege.organs.base import OrganHandler
from rege.core.models import Invocation

class CustomOrgan(OrganHandler):
    """Custom organ implementation."""

    def __init__(self):
        super().__init__("CUSTOM_ORGAN")
        self._modes = ["mode1", "mode2"]

    def process(self, invocation: Invocation) -> Dict[str, Any]:
        mode = invocation.mode

        if mode == "mode1":
            return self._handle_mode1(invocation)
        elif mode == "mode2":
            return self._handle_mode2(invocation)
        else:
            return {"status": "error", "message": f"Unknown mode: {mode}"}

    def get_modes(self) -> List[str]:
        return self._modes.copy()

    def _handle_mode1(self, inv: Invocation) -> Dict[str, Any]:
        return {"status": "success", "mode": "mode1"}

    def _handle_mode2(self, inv: Invocation) -> Dict[str, Any]:
        return {"status": "success", "mode": "mode2"}

# Register the organ
registry = get_organ_registry()
registry.register(CustomOrgan())
```

## Invocation Processing Flow

1. **Parse** - Invocation syntax is parsed by `InvocationParser`
2. **Validate** - Invocation is validated by `InvocationValidator`
3. **Route** - Soul Patchbay routes to appropriate organ
4. **Process** - Organ processes the invocation
5. **Return** - Results returned to caller

```python
from rege.parser.invocation_parser import InvocationParser
from rege.routing.dispatcher import get_dispatcher

# Parse ritual syntax
parser = InvocationParser()
invocation = parser.parse("""
::CALL_ORGAN HEART_OF_CANON
::WITH my_symbol
::MODE assess_candidate
::DEPTH standard
""")

# Dispatch to organ
dispatcher = get_dispatcher()
result = dispatcher.dispatch(invocation)
```
