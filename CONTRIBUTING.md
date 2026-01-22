# Contributing to RE:GE

Thank you for your interest in contributing to the Recursive Engine: Generative Entity project.

## Code of Conduct

Be respectful and constructive. This project explores themes of myth, identity, and symbolic systems - diversity of perspective is valued.

## How to Contribute

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include clear reproduction steps for bugs
- For documentation issues, specify which file and section

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit with clear messages
6. Push and open a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/recursive-engine.git
cd recursive-engine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest -v
```

## Contribution Types

### Python Code (`rege/`)

- Follow PEP 8 style guidelines
- Add type hints where possible
- Write tests for new functionality
- Document public APIs with docstrings

### Documentation (`docs/`)

When editing specification documents:

- Maintain the ritual/mythic tone and formatting conventions
- Use the established tag system (`CANON+`, `ECHO+`, `ARCHIVE+`, etc.)
- Respect inter-organ routing logic (Soul Patchbay as hub)
- Follow the file naming convention: `RE-GE_[TYPE]_[NUMBER]_[NAME].md`

### Adding New Organs

1. Create specification in `docs/organs/RE-GE_ORG_BODY_XX_NAME.md`
2. Implement handler in `rege/organs/name.py`
3. Register in `rege/organs/registry.py`
4. Add valid modes to `rege/parser/validator.py`
5. Write tests in `rege/tests/`

### Adding New Protocols

1. Create specification in `docs/protocols/RE-GE_PROTOCOL_NAME.md`
2. Implement in `rege/protocols/name.py`
3. Write tests in `rege/tests/`

## Testing

All contributions should include tests:

```bash
# Run full test suite
pytest

# Run with coverage report
pytest --cov=rege --cov-report=html

# Run specific tests
pytest rege/tests/test_parser.py -v -k "test_parse_basic"
```

## Commit Messages

Use clear, descriptive commit messages:

```
Add shadow_work mode to MirrorCabinet organ

- Implement shadow archetype detection
- Add integration with Ritual Court for high-charge reflections
- Update validator with new mode
```

## Questions

Open an issue with the "question" label for any clarifications.
