# AGENTS.md

## Packages

- **Root** (`/`) - Main workspace with Jupyter notebooks and `poetry.lock`
- **advanced-ta** (`/advanced-ta/`) - Technical analysis library (Lorentzian Classification)
- **robo-trader** (`/robo-trader/`) - Automated trading library, depends on advanced-ta

## Commands

```bash
# Install all dependencies (from root)
poetry install

# Run tests for advanced-ta (must be in advanced-ta directory)
cd advanced-ta && poetry run pytest

# Run tests for robo-trader
cd robo-trader && poetry run pytest
```

**Note**: advanced-ta tests use `os.chdir('tests')` internally - tests must be run from the `advanced-ta/` directory.

## Dependencies

- advanced-ta: local path dependency in root `pyproject.toml` (`advanced-ta` and `robo-trader` are both included)
- robo-trader: depends on advanced-ta via local path

## Jupyter Notebooks

Notebooks in `/notebooks/` use the root Poetry environment. No separate activation needed.