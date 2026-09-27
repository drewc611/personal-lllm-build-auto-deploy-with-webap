# Security audit — personal-lllm-build-auto-deploy-with-webap — 2026-09-27

Part of a 22-repository audit of this account. The cross-repository report (method, pain points, business impact, solution analysis, roadmap) is published at https://claude.ai/artifact/KgdrC9eNyCwdqjvSfwMNuB.

## Summary for this repository

| Severity | Count |
|---|---|
| Critical | 1 |
| High | 2 |
| Medium | 1 |
| Low | 3 |

**AI-generated placeholder / default credential findings (★):** PL-1 (fixed in this PR), PL-3 (fixed in this PR)

Automated passes run against this repository: gitleaks 8.24.2 (full history and tree), the placeholder-credential checker now shipped in `scripts/`, semgrep 1.178.0 (`p/security-audit`, `p/secrets`, `p/owasp-top-ten`, `p/github-actions`), bandit, pip-audit and npm audit where applicable, plus a manual review of auth, input handling, workflows and deployment files.

## Findings

| ID | Severity | Category | Location | Evidence | Impact | Fix | Status |
|---|---|---|---|---|---|---|---|
| PL-1 ★ | Critical | Debug server / remote code execution | `app.py:87; Dockerfile:16; docker-compose.yml:4-5` | `app.run(host='0.0.0.0', port=8000, debug=True)`; compose publishes 8000:8000 and bind-mounts the repo | The Werkzeug interactive debugger executes arbitrary Python from a browser on any unhandled exception. Published on all interfaces, running as root in the container with the checkout mounted read-write. | Debug and host come from `FLASK_DEBUG` / `FLASK_HOST`, default off and loopback; compose sets the host explicitly. Run behind gunicorn for anything beyond a laptop. | fixed in this PR |
| PL-2 | High | Missing authentication / resource exhaustion | `app.py:66-78; llm-setup.py:17-31; train.py:11` | `POST /run` calls `os.spawnlp(os.P_NOWAIT, 'python3', ...)` with no auth and no concurrency guard | Anyone reaching the port can start unbounded LoRA/nanoGPT training jobs and `git clone` fetches. CPU/GPU and disk exhaustion; network egress to attacker-timed fetches. | Require an auth token, allow one in-flight job, run jobs through a queue with limits. | open |
| PL-3 ★ | High | Hard-coded placeholder secret (CWE-798) | `app.py:8` | `app.config['SECRET_KEY'] = 'change-this-secret-key'` | Every deployment shares a public signing key. flask-login and flask-wtf are in requirements; the moment sessions or CSRF tokens are used they are forgeable by anyone who read this line. | Read `FLASK_SECRET_KEY` from the environment with no default; startup fails when unset. `.env.example` documents how to generate one. | fixed in this PR |
| PL-4 | Medium | Container and network hardening | `docker-compose.yml:12,16-17; Dockerfile (no USER)` | `volumes: - .:/app`; ollama `ports: - "11434:11434"`; image runs as root | Ollama's unauthenticated API is exposed on the host; root plus a bind mount means any code execution edits the host checkout. | Bind Ollama to 127.0.0.1, add a non-root `USER`, drop the bind mount outside local dev. | open |
| PL-5 | Low | CI hygiene | `.github/workflows/automate.yml:8-19,36` | No `permissions:` block; actions on mutable tags; `\|\| true` swallows failures | Default token may be read/write; a moved tag changes what runs. | Add `permissions: contents: read`; pin actions to SHAs (the new secret-scan workflow shows the pattern). | open |
| PL-6 | Low | Unpinned dependencies | `requirements.txt:1-7` | `flask`, `flask-wtf`, `flask-login`, `mlx-lm`, `requests` with no versions | Non-reproducible builds; `mlx-lm` is Apple-silicon only and breaks the Linux Docker/CI install. | Pin exact versions; make `mlx-lm` optional. | open |
| PL-7 | Low | Information disclosure | `app.py:46,49,62` | `'message': str(exc)`, `'message': response.text`, `'raw': result` | Internal Ollama URL, upstream error bodies and raw model payloads returned to clients. | Return generic errors; log detail server-side. | open |

## Guardrails added in this change

- `scripts/check-placeholder-secrets.sh` — fails the build on placeholder credentials, secret defaults, disabled-auth defaults, `debug=True`, literal secret assignments, private keys and committed `.env` files.
- `.gitleaks.toml` — gitleaks defaults plus custom placeholder rules and a fixture allowlist.
- `.github/workflows/secret-scan.yml` — runs both on every push and pull request and weekly over full history (SHA-pinned actions).
- `.pre-commit-config.yaml` — the same checks locally; run `pre-commit install` once.
- `docs/security/AI-CODING-GUARDRAILS.md` — the binding rules for any AI-assisted change, with references.
- A "Security rules for AI-assisted changes" section in `CLAUDE.md` (and `AGENTS.md` / Copilot instructions where present).
- `.gitignore` rules for `.env`, keys and Terraform state where they were missing.

See the cross-repository report for the fail-closed pattern by language and the prioritised fix list.
