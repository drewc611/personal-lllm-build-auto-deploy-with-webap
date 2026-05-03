# personal-lllm-build-auto-deploy-with-webap

A deployable LLM toolkit for local Ollama, LoRA fine-tuning, nanoGPT learning, Flask UI, Docker Compose, and GitHub Actions automation.

## What’s included

- `Dockerfile` for the Flask web app
- `docker-compose.yml` for an app + Ollama stack
- `app.py` + `templates/index.html` for a web UI with live Ollama completions
- `llm-setup.py` CLI wrapper for GPT / LoRA / nanoGPT tasks
- `auto-update.py` for repo refresh and workflow execution
- `prepare_nanogpt.py` to clone the nanoGPT repository automatically
- `mbox_to_txt.py` for Gmail `.mbox` export conversion
- `fine_tune_lora.py` template for LoRA training
- `train.py` starter script for nanoGPT training
- `.github/workflows/automate.yml` GitHub Actions automation
- `config.json` multi-user settings
- `requirements.txt` dependency manifest
- `data/` sample data files

## Quick start

1. Install Python 3.10+ and Docker.
2. Clone the repo.
3. Install Python requirements:

```bash
pip install -r requirements.txt
```

4. Start the Flask web app locally:

```bash
python3 app.py
```

5. Open: `http://localhost:8000`

6. Start the Docker Compose stack:

```bash
docker compose up --build
```

7. If you want to prepare nanoGPT:

```bash
python3 prepare_nanogpt.py
```

8. To run nanoGPT training after cloning:

```bash
python3 train.py --prepare --epochs 5
```

## Phase 3: LoRA fine-tuning

### Install MLX-LM

```bash
pip install mlx-lm
```

### Prepare your data

Create `data/data.jsonl` with prompt/completion pairs:

```json
{"prompt": "Write a funny joke about dogs.", "completion": "Why did the dog bring a ladder to the party? Because it heard the punchline was on the second floor!"}
```

Or generate JSONL from a folder of writing samples:

```bash
python3 fine_tune_lora.py --prepare-dir writing_samples --data data/data.jsonl
```

### Run LoRA fine-tuning

```bash
python3 fine_tune_lora.py --data data/data.jsonl --output llama3.1-lora --train --epochs 10
```

### Run your adapter

```bash
ollama run llama3.1-lora
```

## Notes

- Ollama is required for local Llama 3.1 use.
- The web UI now sends prompts to the local Ollama completion endpoint.
- `config.json` stores the model name and `ollama_url` for the app.
- `prepare_nanogpt.py` clones `https://github.com/karpathy/nanoGPT.git` into `./nanoGPT`.
- Use `data/example_text.txt` for a quick nanoGPT demo dataset.
- GitHub Actions validates the code and clones nanoGPT during CI.
