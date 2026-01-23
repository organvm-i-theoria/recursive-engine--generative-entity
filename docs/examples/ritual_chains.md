# Ritual Chain Examples

Ritual chains are multi-step workflows that orchestrate multiple organ invocations.

## Built-in Chains

RE:GE includes these pre-defined chains:

| Chain | Purpose |
|-------|---------|
| `canonization_ceremony` | Canonize high-charge fragments |
| `contradiction_resolution` | Resolve conflicts between fragments |
| `grief_processing` | Multi-step grief ritual |
| `emergency_recovery` | System recovery sequence |
| `seasonal_bloom` | Seasonal mutation cycle |
| `fragment_lifecycle` | Complete fragment lifecycle |

## Using Chains

### List Available Chains

```bash
rege chain list
```

### View Chain Details

```bash
rege chain show canonization_ceremony
```

Output:
```
::RITUAL CHAIN: canonization_ceremony::
  Description: Ceremony for canonizing high-charge fragments
  Version: 1.0
  Tags: ceremony, canon, ritual
  Entry Phase: canon_assessment

  Phases (4):
    1. canon_assessment
       Organ: HEART_OF_CANON | Mode: assess_candidate
    2. court_deliberation
       Organ: RITUAL_COURT | Mode: deliberate
       Branches: 2
    3. fusion_merge
       Organ: FUSE01 | Mode: merge
    4. archive_record
       Organ: ARCHIVE_ORDER | Mode: record
```

### Execute a Chain

```bash
# Basic execution
rege chain run canonization_ceremony

# With initial context
rege chain run canonization_ceremony --context '{"charge": 85, "symbol": "important_event"}'

# Dry run (preview without executing)
rege chain run canonization_ceremony --dry-run

# Step mode (pause after each phase)
rege chain run canonization_ceremony --step
```

### View Execution History

```bash
rege chain history
rege chain history --chain-name grief_processing --limit 5
```

### View Statistics

```bash
rege chain stats
rege chain stats --chain-name canonization_ceremony
```

## Python API

### Executing Chains

```python
from rege.orchestration import get_chain_registry, RitualChainOrchestrator
from rege.orchestration.builtin_chains import register_builtin_chains

# Register built-in chains
register_builtin_chains()

# Create orchestrator
orchestrator = RitualChainOrchestrator()

# Execute chain
execution = orchestrator.execute_chain(
    "canonization_ceremony",
    context={"charge": 85, "symbol": "my_event"},
)

# Check results
print(f"Status: {execution.status.value}")
print(f"Duration: {execution.get_duration_ms()}ms")

for result in execution.phase_results:
    print(f"  {result.phase_name}: {result.status.value}")
```

### Creating Custom Chains

```python
from rege.orchestration import RitualChain
from rege.orchestration.phase import Phase, Branch, charge_condition

# Create chain
chain = RitualChain(
    name="my_custom_chain",
    description="Custom workflow",
)

# Add phases
chain.add_phase(Phase(
    name="initial_check",
    organ="HEART_OF_CANON",
    mode="assess",
    description="Initial assessment",
))

chain.add_phase(Phase(
    name="process_high",
    organ="RITUAL_COURT",
    mode="deliberate",
    condition=charge_condition(min_charge=71),
))

chain.add_phase(Phase(
    name="process_low",
    organ="ARCHIVE_ORDER",
    mode="store",
    condition=charge_condition(max_charge=70),
))

chain.add_phase(Phase(
    name="finalize",
    organ="ARCHIVE_ORDER",
    mode="record",
))

# Add branching
chain.add_branch(
    "initial_check",
    Branch(
        name="high_charge_path",
        condition=charge_condition(min_charge=71),
        target_phase="process_high",
        priority=10,
    ),
)

chain.add_branch(
    "initial_check",
    Branch(
        name="low_charge_path",
        condition=charge_condition(max_charge=70),
        target_phase="process_low",
        priority=5,
    ),
)

# Validate
validation = chain.validate()
if validation["valid"]:
    print("Chain is valid")
else:
    print(f"Errors: {validation['errors']}")

# Register
registry = get_chain_registry()
registry.register(chain)
```

### Using Condition Helpers

```python
from rege.orchestration.phase import (
    charge_condition,
    tag_condition,
    verdict_condition,
    status_condition,
    combined_condition,
)

# Charge range
high_charge = charge_condition(min_charge=71, max_charge=100)

# Tag presence
has_canon = tag_condition("CANON+")

# Verdict check
approved = verdict_condition("canonize")

# Status check
ready = status_condition("ready")

# Combined conditions
must_approve = combined_condition(
    charge_condition(min_charge=71),
    tag_condition("CANON+"),
    mode="and",
)

can_process = combined_condition(
    charge_condition(min_charge=50),
    tag_condition("RITUAL+"),
    mode="or",
)
```

### Step-by-Step Execution

```python
# Start in step mode
execution = orchestrator.execute_chain("grief_processing", step_mode=True)

while execution.status.value == "paused":
    print(f"Completed: {execution.current_phase}")
    input("Press Enter to continue...")

    # Resume
    execution = orchestrator.resume_execution(execution.execution_id, step_mode=True)

print(f"Final status: {execution.status.value}")
```

### Custom Phase Handlers

```python
# Register custom handler
def custom_handler(context):
    # Process and return result
    return {
        "status": "success",
        "processed": True,
        "charge": context.get("charge", 50) + 10,
    }

orchestrator.register_phase_handler(
    organ="CUSTOM_ORGAN",
    mode="process",
    handler=custom_handler,
)
```

## Canonization Ceremony Flow

```
                    ┌──────────────────┐
                    │ canon_assessment │
                    │  HEART_OF_CANON  │
                    └────────┬─────────┘
                             │
                    charge >= 71?
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼─────┐           │
              │  court    │           │
              │deliberate │           │
              └─────┬─────┘           │
                    │                 │
              verdict?                │
         ┌──────────┴────────┐        │
         │                   │        │
    ┌────▼────┐        ┌─────▼────┐   │
    │ fusion  │        │  skip    │   │
    │  merge  │        │          │   │
    └────┬────┘        └─────┬────┘   │
         │                   │        │
         └─────────┬─────────┘        │
                   │                  │
              ┌────▼────┐             │
              │ archive │◄────────────┘
              │ record  │
              └─────────┘
```

## Error Handling

```python
try:
    execution = orchestrator.execute_chain("canonization_ceremony")

    if execution.status.value == "failed":
        print(f"Chain failed: {execution.error}")

        # Check which phases completed
        for result in execution.phase_results:
            if result.status.value == "failed":
                print(f"Failed at: {result.phase_name}")
                print(f"Error: {result.error}")

except ValueError as e:
    print(f"Chain not found: {e}")
```

## Compensation

Phases can have compensation actions for failure recovery:

```python
# Main phase
main_phase = Phase(
    name="risky_operation",
    organ="FUSE01",
    mode="merge",
    required=True,
)

# Compensation phase
compensation = Phase(
    name="rollback_merge",
    organ="FUSE01",
    mode="rollback",
)

# Set compensation
chain.set_compensation("risky_operation", compensation)
```

When `risky_operation` fails, `rollback_merge` is automatically executed.
