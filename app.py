import json
import os
import secrets
import subprocess
import sys
import threading

import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
# Fail closed: there is no default. Generate a value with
#   python3 -c "import secrets; print(secrets.token_hex(32))"
# and export it as FLASK_SECRET_KEY (or put it in a gitignored .env).
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
# Every endpoint takes a small JSON body; reject anything larger with a 413.
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024

# Fail closed: POST /run starts training jobs, so the service refuses to start
# without a token. Generate one with
#   python3 -c "import secrets; print(secrets.token_hex(32))"
# and export it as RUN_API_TOKEN (or put it in a gitignored .env).
RUN_API_TOKEN = os.environ['RUN_API_TOKEN']
if not RUN_API_TOKEN:
    raise RuntimeError('RUN_API_TOKEN must not be empty')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_PROMPT_CHARS = 8000

# One job at a time. The lock covers the check-then-start so two concurrent
# requests cannot both pass the "nothing running" test. This guard is
# per process; run a single worker (the default for `python3 app.py`).
_job_lock = threading.Lock()
_current_job = None


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


config = load_config()
OLLAMA_URL = os.environ.get('OLLAMA_URL', config.get('ollama_url', 'http://ollama:11434'))
MODEL_NAME = config.get('model', 'llama3.1:8b-instruct-q4_K_M')


def _authorized(req):
    """Constant-time check of the `Authorization: Bearer <token>` header."""
    header = req.headers.get('Authorization', '')
    scheme, _, supplied = header.partition(' ')
    if scheme.lower() != 'bearer' or not supplied:
        return False
    # Compare bytes: compare_digest raises TypeError on non-ASCII str.
    return secrets.compare_digest(supplied.strip().encode('utf-8'), RUN_API_TOKEN.encode('utf-8'))


def _json_object(req):
    data = req.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@app.route('/')
def index():
    return render_template('index.html', config=config, model=MODEL_NAME, ollama_url=OLLAMA_URL)


@app.route('/completion', methods=['POST'])
def completion():
    data = _json_object(request)
    prompt = data.get('prompt', '')
    if not isinstance(prompt, str) or not prompt.strip():
        return jsonify({'status': 'error', 'message': 'Prompt is required.'}), 400
    prompt = prompt.strip()
    if len(prompt) > MAX_PROMPT_CHARS:
        return jsonify({'status': 'error', 'message': 'Prompt is too long.'}), 400

    payload = {
        'model': MODEL_NAME,
        'prompt': prompt,
        'max_tokens': 200,
        'temperature': 0.7
    }

    try:
        response = requests.post(f'{OLLAMA_URL}/v1/completions', json=payload, timeout=30)
    except requests.RequestException:
        app.logger.exception('Ollama request failed')
        return jsonify({'status': 'error', 'message': 'The model backend is unavailable.'}), 502

    if response.status_code != 200:
        app.logger.error('Ollama returned HTTP %s: %s', response.status_code, response.text[:500])
        return jsonify({'status': 'error', 'message': 'The model backend returned an error.'}), 502

    try:
        result = response.json()
    except ValueError:
        app.logger.error('Ollama returned a non-JSON body')
        return jsonify({'status': 'error', 'message': 'The model backend returned an error.'}), 502
    completion_text = ''
    if isinstance(result.get('choices'), list) and result['choices']:
        completion_text = result['choices'][0].get('text', '')
    else:
        completion_text = result.get('text', '') or result.get('completion', '')

    return jsonify({
        'status': 'ok',
        'prompt': prompt,
        'completion': completion_text
    })


@app.route('/run', methods=['POST'])
def run_action():
    global _current_job
    if not _authorized(request):
        return jsonify({'status': 'error', 'message': 'Unauthorized.'}), 401, {'WWW-Authenticate': 'Bearer'}

    action = _json_object(request).get('action')
    commands = {
        'lora': [sys.executable, 'llm-setup.py', '--lora'],
        'nanogpt': [sys.executable, 'llm-setup.py', '--nanogpt']
    }
    if not isinstance(action, str) or action.lower() not in commands:
        return jsonify({'status': 'error', 'message': 'Unknown action.'}), 400
    action = action.lower()

    with _job_lock:
        if _current_job is not None and _current_job.poll() is None:
            return jsonify({'status': 'error', 'message': 'A job is already running.'}), 409
        # Output is not streamed to the browser.
        _current_job = subprocess.Popen(commands[action], cwd=BASE_DIR)
    return jsonify({'status': 'started', 'action': action, 'message': f'{action} task started.'})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'personal-lllm-build'})


if __name__ == '__main__':
    # The Werkzeug debugger runs arbitrary Python from the browser, so debug is
    # off unless FLASK_DEBUG=1 is set explicitly for a local session. Binding
    # to every interface is likewise an explicit choice (FLASK_HOST=0.0.0.0),
    # which the Dockerfile makes for the container.
    app.run(host=os.environ.get('FLASK_HOST', '127.0.0.1'), port=8000,
            debug=os.environ.get('FLASK_DEBUG') == '1')
