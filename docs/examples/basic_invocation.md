# Basic Invocation Examples

This guide demonstrates basic ritual invocations in RE:GE.

## Invocation Syntax

The standard invocation format:

```
::CALL_ORGAN [ORGAN_NAME]
::WITH [INPUT_SYMBOL]
::MODE [OPERATION_MODE]
::DEPTH [light|standard|full spiral]
::EXPECT [output_format]
```

## Simple Invocations

### Heart of Canon Assessment

```bash
rege invoke "
::CALL_ORGAN HEART_OF_CANON
::WITH my_important_symbol
::MODE assess_candidate
::DEPTH standard
"
```

### Archive Storage

```bash
rege invoke "
::CALL_ORGAN ARCHIVE_ORDER
::WITH fragment_to_store
::MODE store
::DEPTH light
"
```

### Bloom Generation

```bash
rege invoke "
::CALL_ORGAN BLOOM_ENGINE
::WITH seed_concept
::MODE mutate
::DEPTH full spiral
"
```

## Using Charge Levels

Charge affects processing priority and canon eligibility:

```bash
# High charge (canon candidate)
rege invoke "::CALL_ORGAN HEART_OF_CANON ::WITH symbol ::MODE assess" --charge 85

# Normal charge
rege invoke "::CALL_ORGAN ARCHIVE_ORDER ::WITH data ::MODE store" --charge 50

# Low charge (background processing)
rege invoke "::CALL_ORGAN BLOOM_ENGINE ::WITH idea ::MODE grow" --charge 25
```

## Depth Levels

Control processing depth:

```bash
# Light - Quick surface processing
rege invoke "..." --depth light

# Standard - Normal processing (default)
rege invoke "..." --depth standard

# Extended - Deeper analysis
rege invoke "..." --depth extended

# Full spiral - Maximum depth
rege invoke "..." --depth full
```

## From File

Create an invocation file:

```text
# invocation.txt
::CALL_ORGAN RITUAL_COURT
::WITH grief_symbol
::MODE grief_ritual
::DEPTH standard
::EXPECT closure
```

Execute:

```bash
rege invoke --file invocation.txt
```

## JSON Output

Get structured output:

```bash
rege invoke "::CALL_ORGAN HEART_OF_CANON ::WITH test ::MODE assess" --json
```

Output:
```json
{
  "status": "success",
  "organ": "HEART_OF_CANON",
  "mode": "assess",
  "result": {
    "assessment": "canon_candidate",
    "charge": 75,
    "tags": ["CANON+"]
  }
}
```

## Python API

```python
from rege.parser.invocation_parser import InvocationParser
from rege.routing.dispatcher import get_dispatcher
from rege.organs.registry import register_default_organs

# Initialize
register_default_organs()
dispatcher = get_dispatcher()
parser = InvocationParser()

# Parse and execute
invocation = parser.parse("""
::CALL_ORGAN HEART_OF_CANON
::WITH my_symbol
::MODE assess_candidate
::DEPTH standard
""")

result = dispatcher.dispatch(invocation)
print(f"Status: {result.status}")
print(f"Result: {result.data}")
```

## Common Patterns

### Create, Assess, Archive

```bash
# Step 1: Create fragment
rege invoke "::CALL_ORGAN BLOOM_ENGINE ::WITH concept ::MODE create"

# Step 2: Assess for canon
rege invoke "::CALL_ORGAN HEART_OF_CANON ::WITH fragment_id ::MODE assess"

# Step 3: Archive result
rege invoke "::CALL_ORGAN ARCHIVE_ORDER ::WITH fragment_id ::MODE store"
```

### Ritual Chain

Use the chain command for multi-step workflows:

```bash
rege chain run canonization_ceremony --context '{"charge": 80}'
```

## Error Handling

```bash
# Check exit code
rege invoke "::CALL_ORGAN UNKNOWN ::WITH test ::MODE mode"
echo $?  # Non-zero on error

# Get error details with JSON
rege invoke "::CALL_ORGAN UNKNOWN ::WITH test ::MODE mode" --json 2>&1
```

## Tips

1. **Use REPL for experimentation**: `rege repl`
2. **Check organ modes**: `:modes HEART_OF_CANON` in REPL
3. **Start with light depth** for quick testing
4. **Use JSON output** for scripting
