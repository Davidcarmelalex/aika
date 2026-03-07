#!/usr/bin/env python3
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error

ROOT = Path('/root/asgardia')
CONFIG_DIR = ROOT / 'config'
AGENTS_DIR = ROOT / 'agents' / 'aika'
STATE_DIR = ROOT / 'state'
LOG_DIR = ROOT / 'logs'

TARGETS = [
    ('asgardia', Path('/root/asgardia')),
    ('ayooni', Path('/root/ayooni')),
    ('voltex', Path('/root/voltex')),
]

BLOCK_RULES = [
    ('go_service', re.compile(r'\.go$')),
    ('python_service', re.compile(r'\.py$')),
    ('node_service', re.compile(r'package\.json$|\.mjs$|\.cjs$|\.js$')),
    ('frontend', re.compile(r'\.html$|\.css$|\.tsx?$|\.jsx?$')),
    ('infra', re.compile(r'docker-compose\.ya?ml$|Dockerfile$|\.service$|nginx|systemd')),
    ('config', re.compile(r'\.ya?ml$|\.json$|\.toml$|\.env$')),
    ('docs', re.compile(r'README|\.md$')),
]


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def classify_path(path: str):
    for label, pat in BLOCK_RULES:
        if pat.search(path):
            return label
    return 'other'


def scan_project(name: str, base: Path):
    blocks = {}
    if not base.exists():
        return {'name': name, 'root': str(base), 'missing': True, 'blocks': []}

    for p in base.rglob('*'):
        if not p.is_file():
            continue
        rel = str(p.relative_to(base))
        if '/.git/' in f'/{rel}/' or rel.startswith('.git/'):
            continue
        if '/node_modules/' in f'/{rel}/':
            continue
        btype = classify_path(rel)
        top = rel.split('/', 1)[0]
        block_id = f'{name}:{top}:{btype}'
        b = blocks.setdefault(block_id, {
            'id': block_id,
            'project': name,
            'component': top,
            'type': btype,
            'files': 0,
            'sample_paths': [],
            'skills': set(),
        })
        b['files'] += 1
        if len(b['sample_paths']) < 5:
            b['sample_paths'].append(rel)
        if btype == 'infra':
            b['skills'].add('deployment')
            b['skills'].add('ops-reliability')
        elif btype == 'backend' or btype.endswith('_service'):
            b['skills'].add('backend-engineering')
        elif btype == 'frontend':
            b['skills'].add('frontend-engineering')
        elif btype == 'config':
            b['skills'].add('config-governance')
        elif btype == 'docs':
            b['skills'].add('knowledge-distillation')
        else:
            b['skills'].add('general-analysis')

    output = []
    for b in blocks.values():
        b['skills'] = sorted(b['skills'])
        output.append(b)
    output.sort(key=lambda x: (x['project'], x['component'], x['type']))
    return {'name': name, 'root': str(base), 'missing': False, 'blocks': output}


def build_learning_tracks(projects):
    all_blocks = []
    for p in projects:
        all_blocks.extend(p.get('blocks', []))

    tracks = {
        'foundation': [],
        'execution': [],
        'scale': [],
    }
    for b in all_blocks:
        t = b['type']
        if t in ('docs', 'config'):
            tracks['foundation'].append(b['id'])
        elif t in ('python_service', 'go_service', 'node_service', 'frontend'):
            tracks['execution'].append(b['id'])
        else:
            tracks['scale'].append(b['id'])
    for k in tracks:
        tracks[k] = sorted(set(tracks[k]))
    return tracks


def elevenlabs_status():
    api_key = os.getenv('ELEVENLABS_API_KEY', '').strip()
    voice_ids = load_json(CONFIG_DIR / 'aika_voice_map.json', {})
    status = {
        'configured': bool(api_key),
        'reachable': False,
        'voices_loaded': False,
        'voice_map_entries': len(voice_ids) if isinstance(voice_ids, dict) else 0,
        'checked_at': now_iso(),
    }
    if not api_key:
        return status

    req = request.Request(
        'https://api.elevenlabs.io/v1/voices',
        headers={'xi-api-key': api_key, 'accept': 'application/json'},
        method='GET',
    )
    try:
        with request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
            voices = payload.get('voices', []) if isinstance(payload, dict) else []
            status['reachable'] = True
            status['voices_loaded'] = len(voices) > 0
            status['voice_count'] = len(voices)
    except error.HTTPError as e:
        status['http_error'] = int(e.code)
    except Exception as e:
        status['error'] = str(e)
    return status


def collect_aika_agents():
    result = []
    for f in sorted(AGENTS_DIR.glob('*.json')):
        j = load_json(f, {})
        result.append({
            'id': j.get('name', f.stem),
            'file': str(f),
            'persona': j.get('persona', ''),
            'priority': j.get('priority', ''),
            'voice': j.get('elevenlabs_voice', ''),
            'skills': j.get('domain_skills', []),
        })
    return result


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    projects = [scan_project(name, path) for name, path in TARGETS]
    tracks = build_learning_tracks(projects)
    agents = collect_aika_agents()
    eleven = elevenlabs_status()

    blueprint = {
        'ts': now_iso(),
        'owner_agent': 'Aika-Architect',
        'mission': 'Break project into composable blocks and map efficient skill-learning paths.',
        'projects': projects,
        'learning_tracks': tracks,
        'aika_agents': agents,
        'elevenlabs': eleven,
    }

    out_file = STATE_DIR / 'aika_skill_blueprint.json'
    out_file.write_text(json.dumps(blueprint, indent=2))

    summary = {
        'ts': blueprint['ts'],
        'owner_agent': blueprint['owner_agent'],
        'projects': {p['name']: len(p.get('blocks', [])) for p in projects},
        'learning_tracks': {k: len(v) for k, v in tracks.items()},
        'elevenlabs': eleven,
        'output': str(out_file),
    }
    (STATE_DIR / 'aika_skill_summary.json').write_text(json.dumps(summary, indent=2))

    with (LOG_DIR / 'aika_skill_planner.log').open('a') as fh:
        fh.write(json.dumps(summary) + '\n')

    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
