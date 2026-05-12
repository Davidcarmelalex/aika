# Contributing to AIKA

## Project Overview

AIKA is the conversational AI layer of the Voltex Network. It connects humans to the ecosystem through natural language — across Telegram, WhatsApp, and voice.

## Workflow

1. Branch from `main`: `git checkout -b feat/your-feature`
2. Write code with type hints and docstrings
3. Add or update tests
4. Open a PR with a clear description
5. Pass CI before merge

## Commit Convention

```
feat: add WhatsApp voice message handler
fix: resolve Telegram callback race condition
docs: update connector configuration guide
test: add context memory unit tests
refactor: simplify Ayooni integration bridge
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
```

## Code Standards

- Python 3.11+
- Type hints on all public functions
- Docstrings for all classes and public methods
- No hardcoded credentials — use `.env`
- Tests for all connector handlers
