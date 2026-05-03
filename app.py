import json
import os

import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


config = load_config()
OLLAMA_URL = os.environ.get('OLLAMA_URL', config.get('ollama_url', 'http://ollama:11434'))
MODEL_NAME = config.get('model', 'llama3.1:8b-instruct-q4_K_M')


@app.route('/')
def index():
    return render_template('index.html', config=config, model=MODEL_NAME, ollama_url=OLLAMA_URL)


@app.route('/completion', methods=['POST'])
def completion():
    data = request.json or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'status': 'error', 'message': 'Prompt is required.'}), 400

    payload = {
        'model': MODEL_NAME,
        'prompt': prompt,
        'max_tokens': 200,
        'temperature': 0.7
    }

    try:
        response = requests.post(f'{OLLAMA_URL}/v1/completions', json=payload, timeout=30)
    except requests.RequestException as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 500

    if response.status_code != 200:
        return jsonify({'status': 'error', 'message': response.text}), response.status_code

    result = response.json()
    completion_text = ''
    if isinstance(result.get('choices'), list) and result['choices']:
        completion_text = result['choices'][0].get('text', '')
    else:
        completion_text = result.get('text', '') or result.get('completion', '')

    return jsonify({
        'status': 'ok',
        'prompt': prompt,
        'completion': completion_text,
        'raw': result
    })


@app.route('/run', methods=['POST'])
def run_action():
    data = request.json or {}
    action = data.get('action', '').lower()
    commands = {
        'lora': ['python3', 'llm-setup.py', '--lora'],
        'nanogpt': ['python3', 'llm-setup.py', '--nanogpt']
    }
    if action not in commands:
        return jsonify({'status': 'error', 'message': 'Unknown action.'}), 400
    # Start the workflow asynchronously; output is not streamed to the browser.
    os.spawnlp(os.P_NOWAIT, 'python3', *commands[action])
    return jsonify({'status': 'started', 'action': action, 'message': f'{action} task started.'})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'personal-lllm-build'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
