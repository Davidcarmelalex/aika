# Aika Personal PA Agent Template

## Purpose
Aika-level personal PA for:
- input capture
- reminder alignment
- task organization
- auto-reprioritization

## Runtime
- Profile: `/root/asgardia/agents/aika-pa/profile.json`
- Engine: `/root/asgardia/ops/aika_pa_agent.py`
- State: `/root/asgardia/state/aika_pa_state.json`
- Task source: `/root/asgardia/state/tasks.json`

## Commands
- Add input as task:
`python3 /root/asgardia/ops/aika_pa_agent.py intake --title "..." --action "..." --priority high --target @TheArchitectOfAsgardia`

- Reprioritize pending tasks:
`python3 /root/asgardia/ops/aika_pa_agent.py reprioritize`

## Prioritization Logic
- urgency weight: 40%
- impact weight: 35%
- deadline proximity weight: 25%
- outputs: `aika_pa_score` and `aika_pa_band` (critical/high/medium/low)

## Suggested cadence
- run reprioritize hourly via timer
- send top 3 tasks to command center every hour
