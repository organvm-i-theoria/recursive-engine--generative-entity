# RE:GE - Recursive Engine: Generative Entity

A symbolic operating system for myth, identity, ritual, and recursive systems.

## Overview

RE:GE is both a conceptual framework expressed through interconnected documentation **and** a fully functional Python implementation. It provides a mythic-academic architecture for exploring personal mythology, symbolic computation, and recursive identity systems.

## Installation

```bash
# Clone the repository
git clone https://github.com/re-ge/recursive-engine.git
cd recursive-engine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Quick Start

### CLI Usage

```bash
# Execute a ritual invocation
rege invoke '::CALL_ORGAN MIRROR_CABINET
::WITH "I feel stuck"
::MODE emotional_reflection
::DEPTH standard
::EXPECT fragment_map'

# Check system status
rege status

# Interactive REPL mode
rege repl

# Manage fragments
rege fragments list
rege fragments create "My Fragment" --charge 60

# Checkpoint and recovery
rege checkpoint create "stable_state"
rege checkpoint list
rege recover partial MIRROR_CABINET
```

### Python API

```python
from rege.parser import parse_invocation
from rege.routing import Dispatcher

# Parse a ritual invocation
invocation = parse_invocation("""
::CALL_ORGAN HEART_OF_CANON
::WITH "a memory of significance"
::MODE mythic
::DEPTH full spiral
::EXPECT canon_event
""")

# Execute through dispatcher
dispatcher = Dispatcher()
result = dispatcher.dispatch(invocation)
```

## Architecture

### Project Structure

```
recursive-engine--generative-entity/
├── rege/                    # Python implementation
│   ├── core/                # Constants, models, exceptions
│   ├── parser/              # Invocation syntax parser
│   ├── routing/             # Soul Patchbay queue system
│   ├── organs/              # 10 organ handlers
│   ├── protocols/           # FUSE01, recovery, enforcement
│   ├── persistence/         # JSON archive system
│   └── tests/               # Test suite
├── docs/                    # Specification documentation
│   ├── core/                # Core system docs
│   ├── organs/              # Organ specifications (01-22)
│   ├── protocols/           # Protocol specifications
│   ├── interfaces/          # OS interface docs
│   ├── academic-wing/       # Academic expansion chambers
│   └── archive/             # Historical/symbolic fragments
├── CLAUDE.md                # Claude Code instructions
└── pyproject.toml           # Package configuration
```

### Core Concepts

#### Organs
The system consists of 22 thematically-named modules (organs):

| Organ | Function |
|-------|----------|
| HEART_OF_CANON | Core mythology and canon events |
| MIRROR_CABINET | Reflection and interpretation |
| MYTHIC_SENATE | Law governance |
| ARCHIVE_ORDER | Storage and retrieval |
| RITUAL_COURT | Ceremonial logic |
| CODE_FORGE | Symbol-to-code translation |
| BLOOM_ENGINE | Generative growth |
| SOUL_PATCHBAY | Modular routing hub |
| ECHO_SHELL | Recursion interface |
| DREAM_COUNCIL | Collective processing |
| MASK_ENGINE | Identity layers |

#### Invocation Syntax

Organs are called using ritual syntax:

```
::CALL_ORGAN [ORGAN_NAME]
::WITH [SYMBOL or INPUT]
::MODE [INTENTION_MODE]
::DEPTH [light | standard | full spiral]
::EXPECT [output_form]
```

#### Charge System

Content is governed by a 5-tier charge system:

| Tier | Range | Behavior |
|------|-------|----------|
| LATENT | 0-25 | Background, no processing |
| PROCESSING | 26-50 | Active consideration |
| ACTIVE | 51-70 | Full engagement |
| INTENSE | 71-85 | Canon candidate |
| CRITICAL | 86-100 | Immediate action required |

#### Tag System

Content is tagged for tracking: `CANON+`, `ECHO+`, `ARCHIVE+`, `VOLATILE+`, `RITUAL+`, `MIRROR+`, `REMIX+`, `MASK+`, `FUSE+`

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=rege

# Run specific test file
pytest rege/tests/test_parser.py -v
```

## Documentation

Full specifications are in the `docs/` directory:

- **Core**: System fundamentals and charge thresholds
- **Organs**: Detailed specifications for all 22 organs
- **Protocols**: FUSE01 fusion, system recovery, collaboration
- **Interfaces**: Ritual access controller, external bridges
- **Academic Wing**: Canonization engine, interlocutor protocols, genealogy

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://github.com/re-ge/recursive-engine#readme)
- [Issues](https://github.com/re-ge/recursive-engine/issues)
