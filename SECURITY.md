# Security Policy — AIKA

## Reporting

Report privately via [GitHub Security Advisories](../../security/advisories/new). We respond within 48 hours.

## Scope

- All AIKA connector handlers (Telegram, WhatsApp, Voice)
- Message routing and intent parsing
- User context and memory storage
- Ayooni integration bridge

## High Priority

- Unauthorized command injection through conversation channels
- User identity spoofing across connectors
- Prompt manipulation to bypass safety policies
- Credential exposure in connector configurations
