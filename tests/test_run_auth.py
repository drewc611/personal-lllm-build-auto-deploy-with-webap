import importlib
import os
import secrets
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeJob:
    def __init__(self, running=True):
        self.running = running

    def poll(self):
        return None if self.running else 0


@pytest.fixture
def client_and_token(monkeypatch):
    token = secrets.token_hex(16)
    monkeypatch.setenv('FLASK_SECRET_KEY', secrets.token_hex(16))
    monkeypatch.setenv('RUN_API_TOKEN', token)
    monkeypatch.syspath_prepend(REPO_ROOT)
    sys.modules.pop('app', None)
    app_module = importlib.import_module('app')
    started = []

    def fake_popen(cmd, **kwargs):
        job = FakeJob()
        started.append((cmd, job))
        return job

    monkeypatch.setattr(app_module.subprocess, 'Popen', fake_popen)
    app_module.app.testing = True
    yield app_module.app.test_client(), token, started
    sys.modules.pop('app', None)


def bearer(token):
    return {'Authorization': f'Bearer {token}'}


def test_run_without_token_is_rejected(client_and_token):
    client, _, started = client_and_token
    resp = client.post('/run', json={'action': 'lora'})
    assert resp.status_code == 401
    assert started == []


def test_run_with_wrong_token_is_rejected(client_and_token):
    client, _, started = client_and_token
    resp = client.post('/run', json={'action': 'lora'}, headers=bearer(secrets.token_hex(16)))
    assert resp.status_code == 401
    assert started == []


def test_run_with_non_ascii_token_is_rejected_not_500(client_and_token):
    client, _, _ = client_and_token
    resp = client.post('/run', json={'action': 'lora'}, headers=bearer('tést'.encode('utf-8').decode('latin-1')))
    assert resp.status_code == 401


def test_run_with_valid_token_starts_one_job(client_and_token):
    client, token, started = client_and_token
    resp = client.post('/run', json={'action': 'lora'}, headers=bearer(token))
    assert resp.status_code == 200
    assert len(started) == 1


def test_second_job_is_refused_while_first_runs(client_and_token):
    client, token, started = client_and_token
    assert client.post('/run', json={'action': 'lora'}, headers=bearer(token)).status_code == 200
    assert client.post('/run', json={'action': 'nanogpt'}, headers=bearer(token)).status_code == 409
    assert len(started) == 1


def test_new_job_allowed_after_first_finishes(client_and_token):
    client, token, started = client_and_token
    client.post('/run', json={'action': 'lora'}, headers=bearer(token))
    started[0][1].running = False
    assert client.post('/run', json={'action': 'nanogpt'}, headers=bearer(token)).status_code == 200
    assert len(started) == 2


@pytest.mark.parametrize('body', [{'action': 'rm -rf'}, {'action': 5}, {}, [], 'lora'])
def test_bad_input_is_400(client_and_token, body):
    client, token, started = client_and_token
    resp = client.post('/run', json=body, headers=bearer(token))
    assert resp.status_code == 400
    assert started == []


def test_oversized_body_is_413(client_and_token):
    client, token, started = client_and_token
    resp = client.post('/run', data=b'{"action": "' + b'a' * 200000 + b'"}',
                       content_type='application/json', headers=bearer(token))
    assert resp.status_code == 413
    assert started == []


def test_app_refuses_to_start_without_run_token(monkeypatch):
    monkeypatch.setenv('FLASK_SECRET_KEY', secrets.token_hex(16))
    monkeypatch.delenv('RUN_API_TOKEN', raising=False)
    monkeypatch.syspath_prepend(REPO_ROOT)
    sys.modules.pop('app', None)
    with pytest.raises(KeyError):
        importlib.import_module('app')
    sys.modules.pop('app', None)


def test_completion_error_does_not_leak_upstream_detail(client_and_token, monkeypatch):
    client, _, _ = client_and_token
    app_module = sys.modules['app']
    marker = secrets.token_hex(8)

    def boom(*args, **kwargs):
        raise app_module.requests.RequestException(f'connect failed {marker}')

    monkeypatch.setattr(app_module.requests, 'post', boom)
    resp = client.post('/completion', json={'prompt': 'hi'})
    assert resp.status_code == 502
    assert marker not in resp.get_data(as_text=True)
