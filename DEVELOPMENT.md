# Development Guide

## Virtual Environment Setup

This project uses a Python virtual environment to isolate dependencies.

### Initial Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install the package in editable mode with dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Daily Development

```bash
# Activate virtual environment
source venv/bin/activate

# Your virtual environment is now active
# You can run kiro-analyzer commands
kiro-analyzer --version

# Deactivate when done
deactivate
```

### Building the Package

```bash
# Activate virtual environment
source venv/bin/activate

# Install build tools
pip install build

# Build the wheel
python -m build

# The wheel will be in dist/
ls dist/
```

### Testing Installation

```bash
# Install from the built wheel
pip install dist/kiro_analyzer-0.1.0-py3-none-any.whl

# Verify installation
kiro-analyzer --version
kiro-analyzer --help
```

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=kiro_analyzer --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Project Structure

```
Kiro-DevProductivityCLI/
├── src/
│   └── kiro_analyzer/
│       ├── __init__.py
│       ├── cli.py
│       ├── analyzers/
│       ├── commands/
│       ├── parsers/
│       ├── reporters/
│       ├── services/
│       └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── pyproject.toml
├── setup.py
├── README.md
├── LICENSE
└── venv/  (not in git)
```

## Notes

- The `venv/` directory is excluded from git via `.gitignore`
- Always activate the virtual environment before working on the project
- Use `pip list` to see installed packages in the virtual environment
- Use `pip freeze > requirements.txt` to export dependencies (optional)
