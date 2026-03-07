#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error

ROOT = Path('/root/asgardia')
STATE = ROOT / 'state'
LOGS = ROOT / 'logs'
ENV_FILES = [
    ROOT / 'config' / 'aika_eleven.env',
    ROOT / 'config' / 'elevenlabs.env',
]
SECRETS_ENC = STATE / 'secrets_master.env.enc'
SECRETS_KEY = STATE / '.secrets_master.key'


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def load_env_file(path: Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())


def dequote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_env_blob(blob: str) -> dict:
    env = {}
    for line in blob.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = dequote(v.strip())
    return env


def load_secrets_env():
    if not SECRETS_ENC.exists() or not SECRETS_KEY.exists():
        return
    cmd = [
        'openssl',
        'enc',
        '-d',
        '-aes-256-cbc',
        '-pbkdf2',
        '-iter',
        '200000',
        '-in',
        str(SECRETS_ENC),
        '-pass',
        f'file:{SECRETS_KEY}',
    ]
    try:
        import subprocess
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception:
        return
    if p.returncode != 0:
        return
    for k, v in parse_env_blob(p.stdout).items():
        os.environ.setdefault(k, v)


def call_api(method: str, path: str, api_key: str, payload=None):
    url = f'https://api.elevenlabs.io{path}'
    headers = {'xi-api-key': api_key, 'accept': 'application/json'}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['content-type'] = 'application/json'
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode('utf-8')
            return resp.getcode(), (json.loads(body) if body else None)
    except error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {'raw': body[:500]}
        return e.code, parsed
    except Exception as e:
        return 0, {'error': str(e)}


def pick_agent_id(agents_payload, preferred_name):
    agents = agents_payload.get('agents', []) if isinstance(agents_payload, dict) else []
    if not agents:
        return None
    pref = preferred_name.lower().strip()
    for a in agents:
        name = str(a.get('name', '')).lower()
        if pref and pref in name:
            return a.get('agent_id')
    for a in agents:
        name = str(a.get('name', '')).lower()
        if 'aika' in name:
            return a.get('agent_id')
    return agents[0].get('agent_id')


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    for env_file in ENV_FILES:
        load_env_file(env_file)
    load_secrets_env()

    api_key = os.getenv('ELEVENLABS_API_KEY', '').strip()
    tw_sid = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
    tw_token = os.getenv('TWILIO_AUTH_TOKEN', '').strip()
    tw_from = os.getenv('TWILIO_FROM', '').strip()
    tw_to = os.getenv('TWILIO_TO', '').strip()
    preferred_agent_name = os.getenv('ELEVENLABS_AGENT_NAME', 'AIKA').strip()
    explicit_agent_id = os.getenv('ELEVENLABS_AGENT_ID', '').strip()
    do_outbound = os.getenv('ELEVENLABS_TRIGGER_OUTBOUND', 'false').lower() in {'1', 'true', 'yes', 'on'}

    report = {
        'ts': now(),
        'ok': False,
        'api_key_configured': bool(api_key),
        'agents_list_http': None,
        'agent_id': explicit_agent_id or None,
        'phone_numbers_list_http': None,
        'phone_number_id': None,
        'phone_import_http': None,
        'outbound_call_http': None,
        'outbound_result': None,
    }

    if not api_key:
        report['error'] = 'missing ELEVENLABS_API_KEY'
        (STATE / 'aika_eleven_status.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    code, agents = call_api('GET', '/v1/convai/agents', api_key)
    report['agents_list_http'] = code
    if code != 200:
        report['error'] = {'stage': 'list_agents', 'response': agents}
        (STATE / 'aika_eleven_status.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    if not report['agent_id']:
        report['agent_id'] = pick_agent_id(agents, preferred_agent_name)

    code, nums = call_api('GET', '/v1/convai/phone-numbers', api_key)
    report['phone_numbers_list_http'] = code
    if code != 200:
        report['error'] = {'stage': 'list_phone_numbers', 'response': nums}
        (STATE / 'aika_eleven_status.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return

    num_list = nums if isinstance(nums, list) else []
    for n in num_list:
        if str(n.get('phone_number', '')).strip() == tw_from:
            report['phone_number_id'] = n.get('phone_number_id')
            break

    if not report['phone_number_id'] and tw_sid and tw_token and tw_from:
        payload = {
            'provider': 'twilio',
            'label': 'AIKA Twilio Line',
            'phone_number': tw_from,
            'sid': tw_sid,
            'token': tw_token,
        }
        code, imp = call_api('POST', '/v1/convai/phone-numbers', api_key, payload)
        report['phone_import_http'] = code
        if code == 200 and isinstance(imp, dict):
            report['phone_number_id'] = imp.get('phone_number_id')
        else:
            report['phone_import_response'] = imp

    if do_outbound and report['agent_id'] and report['phone_number_id'] and tw_to:
        payload = {
            'agent_id': report['agent_id'],
            'agent_phone_number_id': report['phone_number_id'],
            'to_number': tw_to,
        }
        code, out = call_api('POST', '/v1/convai/twilio/outbound-call', api_key, payload)
        report['outbound_call_http'] = code
        report['outbound_result'] = out

    report['ok'] = bool(report.get('agent_id')) and bool(report.get('phone_number_id'))

    (STATE / 'aika_eleven_status.json').write_text(json.dumps(report, indent=2))
    with (LOGS / 'aika_eleven_connector.log').open('a') as f:
        f.write(json.dumps(report) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
