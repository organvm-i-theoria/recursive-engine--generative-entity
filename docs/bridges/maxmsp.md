# Max/MSP Bridge

Integration between RE:GE and Max/MSP via OSC (Open Sound Control).

## Overview

The Max/MSP bridge enables real-time communication between RE:GE and Max/MSP for:
- Sending fragment data to Max patches
- Triggering bloom phase changes
- Streaming charge values
- Audio/visual response generation

## Prerequisites

1. Max/MSP installed (tested with Max 8+)
2. Python `pythonosc` library (optional, for actual OSC)
3. RE:GE installed (`pip install rege`)

## Installation

```bash
# Install with OSC support
pip install pythonosc

# Or the bridge works in mock mode without it
```

## Setup

### Configuration

```bash
# Connect to Max/MSP
rege bridge connect maxmsp --host localhost --port 7400

# Environment variables
export REGE_BRIDGE_MAXMSP_HOST=localhost
export REGE_BRIDGE_MAXMSP_PORT=7400
rege bridge connect maxmsp
```

### Max/MSP Patch Setup

Create a Max patch with `udpreceive` object:

```
[udpreceive 7400]
    |
[route /rege/fragment /rege/charge /rege/bloom/phase /rege/canon /rege/status]
```

## OSC Address Patterns

| Address | Arguments | Description |
|---------|-----------|-------------|
| `/rege/fragment` | id, name, charge, tags, status | Fragment data |
| `/rege/charge` | charge (int) | Charge value |
| `/rege/bloom/phase` | phase (str), phase_num (int) | Bloom phase |
| `/rege/canon` | event_id, charge, status | Canon event |
| `/rege/status` | key1, val1, key2, val2, ... | Generic status |
| `/rege/depth` | current, max | Depth levels |
| `/rege/queue` | pending, processing | Queue state |

## Usage

### Sending Fragment Data

```python
from rege.bridges.maxmsp import MaxMSPBridge

bridge = MaxMSPBridge(config={"host": "localhost", "port": 7400})
bridge.connect()

# Send fragment
result = bridge.send({
    "type": "fragment",
    "fragment": {
        "id": "FRAG_001",
        "name": "My Fragment",
        "charge": 75,
        "tags": ["CANON+", "RITUAL+"],
        "status": "active",
    }
})

# OSC message sent: /rege/fragment "FRAG_001" "My Fragment" 75 "CANON+,RITUAL+" "active"
```

### Sending Charge Values

```python
# Real-time charge updates
bridge.send_charge(85)
# OSC: /rege/charge 85

# Or via send method
bridge.send({"type": "charge", "charge": 85})
```

### Bloom Phase Triggers

```python
# Bloom phases mapped to numeric values
# dormant=0, spring=1, growth=2, peak=3, wilt=4, decay=5

bridge.send_bloom_phase("peak")
# OSC: /rege/bloom/phase "peak" 3
```

### Canon Events

```python
bridge.send({
    "type": "canon_event",
    "event": {
        "event_id": "CANON_001",
        "charge": 92,
        "status": "glowing",
    }
})
# OSC: /rege/canon "CANON_001" 92 "glowing"
```

### Batch Messages

```python
bridge.send({
    "type": "batch",
    "messages": [
        {"type": "charge", "charge": 75},
        {"type": "bloom_phase", "phase": "growth"},
        {"type": "fragment", "fragment": {...}},
    ]
})
```

## Max/MSP Example Patch

```max
----------begin_max5_patcher----------
{
    "patcher": {
        "boxes": [
            {"box": {"maxclass": "newobj", "text": "udpreceive 7400"}},
            {"box": {"maxclass": "newobj", "text": "route /rege/fragment /rege/charge /rege/bloom/phase"}},
            {"box": {"maxclass": "message", "text": "fragment: $1 $2 $3"}},
            {"box": {"maxclass": "number", "comment": "charge"}},
            {"box": {"maxclass": "message", "text": "bloom: $1"}}
        ]
    }
}
----------end_max5_patcher----------
```

## Python API

```python
from rege.bridges.maxmsp import MaxMSPBridge

# Create bridge
bridge = MaxMSPBridge(config={
    "host": "localhost",
    "port": 7400,
})

# Connect
if bridge.connect():
    print(f"Connected to {bridge.get_host()}:{bridge.get_port()}")

# Check if using real OSC or mock mode
state = bridge.receive()
print(f"Mock mode: {state['mock_mode']}")

# Send data
bridge.send_fragment({
    "id": "FRAG_001",
    "name": "Test",
    "charge": 65,
})

bridge.send_charge(80)
bridge.send_bloom_phase("spring")

# Disconnect
bridge.disconnect()
```

## Mock Mode

When `pythonosc` is not installed, the bridge operates in mock mode:
- All operations succeed but no OSC messages are sent
- Useful for testing without Max/MSP running
- `receive()` returns `{"mock_mode": True}`

```python
bridge = MaxMSPBridge()
bridge.connect()  # Works even without pythonosc

state = bridge.receive()
if state["mock_mode"]:
    print("Running in mock mode")
```

## Real-time Monitoring

For continuous monitoring, create a loop:

```python
import time
from rege.routing.depth_tracker import get_depth_tracker
from rege.routing.patchbay import get_patchbay_queue

bridge = MaxMSPBridge()
bridge.connect()

while True:
    # Send depth info
    tracker = get_depth_tracker()
    bridge.send({
        "type": "generic",
        "depth": tracker.current_depth,
        "max_depth": tracker.max_depth_reached,
    })

    # Send queue info
    queue = get_patchbay_queue()
    state = queue.get_queue_state()
    bridge.send({
        "type": "generic",
        "pending": state["pending_count"],
        "processed": state["processed_count"],
    })

    time.sleep(0.1)  # 10Hz update rate
```

## Troubleshooting

### No messages received in Max

1. Check UDP port is not blocked
2. Verify host/port match between bridge and `udpreceive`
3. Confirm `pythonosc` is installed

### "pythonosc not installed"

Install the library:
```bash
pip install python-osc
```

### High latency

- Reduce update frequency
- Use batch messages for multiple values
- Consider using TCP for reliability (not supported)
