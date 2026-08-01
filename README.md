# MedGuard — Assignment 2 Iteration 1 Optimized

MedGuard is a local security proxy for clinical LLM workflows. This repository contains our first complete MVP for FIT5238 Assignment 2.

The primary user is a **Clinical AI Security Analyst**. The Dashboard helps this user see whether a clinical prompt was blocked, sanitized, isolated as untrusted data, or allowed to continue.

## Iteration 1 scope

The MVP contains:

- a working web Dashboard;
- prompt-injection detection for user and tool messages;
- block and sanitize responses;
- EHR/RAG content isolation;
- Canary-token checks for non-streaming model output;
- a local TF-IDF and logistic-regression prompt-injection risk scorer;
- an OpenAI-compatible `/v1/chat/completions` proxy;
- simulated clinical data and simulated AI output for an offline classroom demo;
- audit events and runtime defense switches;
- automated tests for the main user paths and error paths.

Batch evaluation, Dashboard live-model mode, streaming output and advanced response validation are reserved for Iteration 2. Streaming requests receive a controlled `400` response in this build.

## System flow

```text
OpenAI-compatible client
          |
          v
MedGuard proxy and three defense layers
          |
          v
Upstream LLM API
```

The Dashboard demonstration does not need an API key. The proxy endpoint can forward clean, non-streaming requests to a real OpenAI-compatible provider when a client supplies its provider key.

## Project structure

```text
medguard-iteration1/
  run.py
  requirements.txt
  README.md
  medguard_core/
  scripts/
  models/
  data/
  tests/
  docs/
```

## Install

Open PowerShell in this directory:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Test

```powershell
python -m pytest -q
```

Verified Iteration 1 result:

```text
24 passed
```

The bundled risk model was trained with the exact NumPy, scikit-learn and
joblib versions pinned in `requirements.txt`, so a clean Python 3.12 install
does not depend on local compiler tools.

## Local ML risk scorer

The optional scorer complements the rule detector and shows a risk score in
the Dashboard and API evidence. It was trained on 900 constructed examples
derived from 300 Alpaca prompt pairs. The split is grouped by `source_id`, so
the same original prompt pair cannot occur in both train and test sets.

The recorded synthetic split has zero source overlap and scores 1.0 for
accuracy, precision, recall and F1. These numbers only describe the constructed
wrapper-classification task. They are not clinical-safety or real-world
prompt-injection performance claims.

To reproduce the model with a separately obtained `alpaca_data.json` file:

```powershell
python -B scripts\train_risk_model.py --alpaca "<path-to-alpaca_data.json>" --sample-pairs 300
```

The raw Alpaca file is training input only and is excluded by `.gitignore`.

## Run the offline MVP demo

```powershell
python -B run.py --port 8081
```

Open:

```text
http://127.0.0.1:8081/dashboard
```

For a supervised classroom demonstration on the same trusted network:

```powershell
python -B run.py --host 0.0.0.0 --port 8081
```

Use the computer's LAN address from the assessor's device. Do not expose this Iteration 1 server directly to the public internet because the Dashboard does not include authentication or TLS.

Suggested demo:

1. Run the clean sample and show the simulated assistant output.
2. Run the Role override sample and show the blocked decision.
3. Run the Poisoned EHR sample and explain detection and isolation.
4. Change Block to Sanitize and repeat the attack.
5. Open an audit event and show that full clinical messages and credentials are not logged.

## Connect an OpenAI-compatible client

Start MedGuard with the provider base URL:

```powershell
python -B run.py --target "<provider-base-url>" --port 8081
```

Configure the client:

```text
Base URL: http://127.0.0.1:8081/v1
API Key : provider API key
Model   : provider model name
```

Do not commit API keys or `.env` files.

## Iteration 1 endpoints

```text
GET  /dashboard
GET  /health
GET  /api/status
POST /api/config
GET  /api/events
POST /api/demo/analyze
POST /v1/chat/completions
GET  /v1/models
```

Technical documentation is in [`docs/project_report.md`](docs/project_report.md). Test evidence is in [`docs/testing.md`](docs/testing.md).

