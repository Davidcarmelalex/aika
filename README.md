# AIKA

> The human communication layer of the Voltex Network.

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()
[![Part of](https://img.shields.io/badge/Voltex%20Network-FCRI-purple.svg)](https://fcri.science)

AIKA is the **conversational AI product** of the Voltex Network — the face that humans talk to. It handles natural language interaction across WhatsApp, Telegram, and voice interfaces, then routes intent to Ayooni for reasoning and execution.

---

## System Position

```
Human ──────────────────────────────────── Execution
  │                                             │
  ▼                                             ▼
AIKA          →          Ayooni          →   Automation
(conversation)         (cognition)          (execution)
  │
  ├── WhatsApp connector
  ├── Telegram connector
  └── Voice connector
```

---

## Architecture

```
aika/
├── agents/
│   ├── aika_core/        Core AIKA agent logic
│   ├── aika_pa/          Personal assistant agent
│   └── profiles/         Agent personality profiles
├── connectors/
│   ├── telegram/         Telegram bot connector
│   ├── whatsapp/         WhatsApp connector
│   └── voice/            Voice interface connector
├── conversation/
│   ├── context/          Session context management
│   └── memory/           Persistent user memory
├── integrations/
│   ├── ayooni/           Bridge to Ayooni cognitive layer
│   └── automation/       Direct automation hooks
├── api/                  HTTP API layer
├── config/               Connector and voice configuration
└── state/                Runtime state snapshots
```

---

## Quick Start

```bash
git clone https://github.com/Davidcarmelalex/aika
cd aika
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your connector tokens
python -m api.server
```

---

## Connectors

| Channel | Status | Notes |
|---------|--------|-------|
| Telegram | ✅ Active | Bot API via python-telegram-bot |
| WhatsApp | 🔨 Building | Via Meta Cloud API |
| Voice | 🔨 Building | Whisper STT + TTS synthesis |

---

## Configuration

```env
# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# WhatsApp
WHATSAPP_TOKEN=your-meta-token
WHATSAPP_PHONE_ID=your-phone-id

# Ayooni integration
AYOONI_URL=http://localhost:8000

# Voice
WHISPER_MODEL=base
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Part of the [Voltex Network](https://fcri.science).
