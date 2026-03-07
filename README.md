# AIKA

AIKA is a human-like conversational AI system designed to interact naturally across messaging and voice interfaces.

AIKA is the human communication layer of the Grossphere ecosystem.

## Capabilities

- WhatsApp and chat conversations
- Voice connector integration
- Context and memory-oriented interaction
- Task routing toward Ayooni/Automation

## High-Level Flow

User -> AIKA -> AYOONI -> Agents -> Automation

## Repository Structure

- `agents/`: core and PA agent logic and profile packs
- `connectors/`: channel connectors (voice/WhatsApp/Telegram)
- `conversation/`: memory/context modules
- `integrations/`: Ayooni and Automation bridges
- `docs/`: AIKA policy/profile documentation
- `state/`: AIKA state snapshots
- `config/`: AIKA connector/voice maps
