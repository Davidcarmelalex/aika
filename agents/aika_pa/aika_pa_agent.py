#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

TASKS_FILE = Path('/root/asgardia/state/tasks.json')
PROFILE_FILE = Path('/root/asgardia/agents/aika-pa/profile.json')
STATE_FILE = Path('/root/asgardia/state/aika_pa_state.json')


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return fallback


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding='utf-8')


def parse_due(due_utc: str) -> float:
    if not due_utc:
        return 0.0
    try:
        return datetime.fromisoformat(due_utc.replace('Z', '+00:00')).timestamp()
    except Exception:
        return 0.0


def score_task(task: dict, now_ts: float) -> int:
    priority_map = {'low': 20, 'medium': 50, 'high': 80, 'critical': 95}
    base = priority_map.get(task.get('priority', 'medium'), 50)

    impact = 70
    title = (task.get('title') or '').lower()
    if 'launch' in title or 'client' in title or 'revenue' in title:
        impact = 90
    elif 'update' in title or 'check' in title:
        impact = 60

    due_ts = parse_due(task.get('due_utc', ''))
    if due_ts > 0:
        hours_left = max(0.0, (due_ts - now_ts) / 3600.0)
        deadline = 95 if hours_left < 2 else 80 if hours_left < 8 else 65 if hours_left < 24 else 40
    else:
        deadline = 45

    urgency = base
    score = int((urgency * 0.4) + (impact * 0.35) + (deadline * 0.25))
    return max(0, min(100, score))


def band(score: int) -> str:
    if score >= 85:
        return 'critical'
    if score >= 65:
        return 'high'
    if score >= 40:
        return 'medium'
    return 'low'


def intake(title: str, action: str, owner: str, target: str, priority: str, due_utc: str) -> dict:
    tasks = load_json(TASKS_FILE, [])
    if not isinstance(tasks, list):
        tasks = []
    task_id = f"tsk-{len(tasks)+1:04d}"
    task = {
        'id': task_id,
        'title': title,
        'action': action,
        'owner': owner,
        'priority': priority,
        'target': target,
        'due_utc': due_utc,
        'status': 'pending',
        'created_at_utc': now_iso(),
        'source': 'aika-pa'
    }
    tasks.append(task)
    save_json(TASKS_FILE, tasks)
    return task


def reprioritize() -> dict:
    tasks = load_json(TASKS_FILE, [])
    if not isinstance(tasks, list):
        tasks = []
    now_ts = datetime.now(timezone.utc).timestamp()
    ranked = []
    for t in tasks:
        if t.get('status') != 'pending':
            continue
        s = score_task(t, now_ts)
        t['aika_pa_score'] = s
        t['aika_pa_band'] = band(s)
        ranked.append(t)

    ranked.sort(key=lambda x: x.get('aika_pa_score', 0), reverse=True)
    save_json(TASKS_FILE, tasks)

    summary = {
        'ts': now_iso(),
        'pending_count': len(ranked),
        'top_10': [{
            'id': x.get('id'),
            'title': x.get('title'),
            'score': x.get('aika_pa_score'),
            'band': x.get('aika_pa_band'),
            'priority': x.get('priority')
        } for x in ranked[:10]]
    }
    save_json(STATE_FILE, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_intake = sub.add_parser('intake')
    p_intake.add_argument('--title', required=True)
    p_intake.add_argument('--action', default='follow-up')
    p_intake.add_argument('--owner', default='Aika-PA')
    p_intake.add_argument('--target', default='@TheArchitectOfAsgardia')
    p_intake.add_argument('--priority', default='medium')
    p_intake.add_argument('--due-utc', default='')

    sub.add_parser('reprioritize')

    args = parser.parse_args()

    load_json(PROFILE_FILE, {})

    if args.cmd == 'intake':
        task = intake(args.title, args.action, args.owner, args.target, args.priority, args.due_utc)
        print(json.dumps(task, ensure_ascii=True, indent=2))
        return 0

    if args.cmd == 'reprioritize':
        summary = reprioritize()
        print(json.dumps(summary, ensure_ascii=True, indent=2))
        return 0

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
