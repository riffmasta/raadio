"""Manual verification inside the deployed container; creates one short test recording."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

url = 'http://127.0.0.1:8788'
password = os.environ.get('WEB_PASS', '')
assert password, 'Password must be configured'
auth = 'Basic ' + base64.b64encode((os.environ.get('WEB_USER', 'raadio') + ':' + password).encode()).decode()
def get(path, headers=None):
    return urllib.request.urlopen(urllib.request.Request(url+path, headers={'Authorization': auth, **(headers or {})}), timeout=10)
try:
    urllib.request.urlopen(url+'/api/config', timeout=10)
    raise AssertionError('Unauthenticated config was accessible')
except urllib.error.HTTPError as e:
    assert e.code == 401
print('PASS: unauthenticated API returns 401', flush=True)
with get('/api/status') as r:
    status = json.load(r)
age = (datetime.now(timezone.utc) - datetime.fromisoformat(status['updated'])).total_seconds()
assert 0 <= age < 180, 'Recorder status is stale'
with get('/api/schedule') as r:
    schedule = json.load(r)
assert len(schedule['stations']) == 10
print('PASS: authenticated API and fresh recorder status; 10 stations', flush=True)
assert os.getuid() == 1000
assert not Path('/app/.env').exists()
assert not Path('/app/docker/config.env').exists()
try:
    Path('/app/.smoke-write').write_text('must fail')
    raise AssertionError('Root filesystem is writable')
except OSError as e:
    assert e.errno == 30, e
print('PASS: non-root, read-only root filesystem, no environment files in image', flush=True)
marker = Path('/state/deployment-smoke.json')
if not marker.exists():
    with get('/api/config') as r:
        config = json.load(r)
    assert not any(config.get(k) for k in ['shows', 'episodes', 'timers']), 'Do not run initial recording test with user subscriptions'
    subprocess.run([sys.executable, 'recorder/kuku_recorder.py', '--test', '20', 'vikerraadio'], check=True, timeout=90)
    with get('/api/recordings') as r:
        recordings = json.load(r)
    assert recordings, 'Test recording missing'
    rec = next(r for r in recordings if r['station'] == 'vikerraadio')
    assert rec['size'] > 0 and rec['duration'] >= 10, 'Test recording is empty or too short'
    marker.write_text(json.dumps({'key':rec['key']}))
    print('PASS: live Vikerraadio recording saved', flush=True)
else:
    print('PASS: state marker survived container recreation', flush=True)
rec = json.loads(marker.read_text())
with get('/audio/'+rec['key'], {'Range':'bytes=0-999'}) as r:
    assert r.status == 206
    assert len(r.read()) == 1000
with get('/api/recordings') as r:
    assert any(item['key'] == rec['key'] for item in json.load(r))
print('PASS: recording metadata, audio playback, and HTTP Range seeking', flush=True)
