# MedGuard — Assignment 2 Iteration 2 Final

MedGuard is a deployable local safety proxy and web dashboard for clinical AI
workflows. The primary user is a **Clinical AI Security Analyst** who needs to
check requests, understand safety evidence and decide whether a request should
continue before it reaches a connected AI model.

This branch is the final Iteration 2 build. It retains the complete optimized
Iteration 1 baseline and adds the planned I2 functionality.

## Implemented system

- responsive web dashboard with structured decision, AI-output, security-signal and protected-message views for one defined analyst audience;
- explainable prompt-injection rules for user, tool and retrieved content;
- local TF-IDF and logistic-regression risk scoring;
- block and sanitize responses;
- EHR/RAG content isolation;
- Canary-token protection for non-streaming and streaming responses;
- OpenAI-compatible `/v1/chat/completions` proxy;
- Dashboard choices labelled Check safety only, Use a sample AI response and
  Use a connected AI model;
- batch security evaluation with detection, false-positive and latency metrics;
- multimodal message validation and nested response/tool-call scanning;
- audit-event search and JSON export;
- controlled errors for malformed input, invalid upstream responses and
  unavailable providers;
- automated tests for I1, I2 and failure paths.

## Iteration structure

| Version | Branch | Tag |
|---|---|---|
| Original I1 baseline | `integration/iteration-1` | `iteration-1-complete` |
| Optimized I1 final | `integration/iteration-1-optimized` | `iteration-1-optimized-complete` |
| Final I2 | `integration/iteration-2` | `iteration-2-complete` |

The original I1 branch and tag are retained so the two demonstrated iterations
remain reproducible.

## Architecture

```text
Dashboard or OpenAI-compatible client
                |
                v
       validation and detection
                |
        isolation + ML score
                |
          Canary protection
                |
                v
       OpenAI-compatible upstream
```

The offline demonstration uses simulated clinical data and clearly labelled
simulated output, so it works without an API key. Live mode uses an optional
server-side credential and never sends that credential to the browser.

## Install

Python 3.12 is supported. In PowerShell:

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

Verified final result:

```text
69 passed
```

The suite covers the original I1 acceptance criteria, all I2 features and
normal, blocked, invalid and upstream-failure paths. See
[`docs/testing.md`](docs/testing.md) for the detailed evidence and
[`docs/iteration2_feedback.md`](docs/iteration2_feedback.md) for the trace from
Iteration 1 staff feedback to the final Iteration 2 changes.

## Run the offline demo

```powershell
python -B run.py --port 8081
```

Open `http://127.0.0.1:8081/dashboard`. The first visit opens a five-step
interactive guide. Use **Help** in the top navigation to restart it. Recent
redacted decisions are available on the separate
`http://127.0.0.1:8081/review-history` page.

The Dashboard guides a first-time user through three steps: enter the task and
optional demonstration context, choose how the request should run, and review
the recommended outcome. Technical evidence remains available in an expandable
section, while protected instructions and hidden security markers stay private.
Field-level introductions and examples explain what belongs in each input. The
interface uses plain-language outcomes and consistent semantic colours: green
for safe decisions, red for review warnings, deep red for stopped requests,
blue for information and grey for inactive or waiting states. Run controls stay
aligned on desktop, use a two-column tablet layout and stack on mobile.

Suggested demonstration:

1. Choose **Use a sample AI response**, check a clean request and show **Safe to continue**.
2. Open **Technical details** to explain the supporting risk and message-handling evidence.
3. Run Role override and Poisoned EHR examples and show **Request stopped** or **Review recommended**.
4. Compare **Stop unsafe requests** with **Remove unsafe instructions and continue**.
5. Select **Test sample requests** and review the summary.
6. Open **Review History**, filter the decision cards and download the redacted
   session report.

For a supervised classroom demo on the same trusted network:

```powershell
python -B run.py --host 0.0.0.0 --port 8081
```

Do not expose this classroom prototype directly to the public internet because
it does not include production authentication or TLS termination.

## Optional live upstream mode

Set the credential only in the process environment; never commit it:

```powershell
$env:MEDGUARD_UPSTREAM_API_KEY="<provider-api-key>"
$env:MEDGUARD_UPSTREAM_MODEL="<provider-model>"
python -B run.py --target "<provider-base-url>" --port 8081
```

The proxy also accepts an authorization header from an OpenAI-compatible client.
The Dashboard uses the server-side environment value when **Use a connected AI
model** is selected.

## Local ML risk scorer

The scorer complements the rule detector and returns a probability plus a
pass/warn/block action. The bundled model was trained on 900 constructed
examples derived from 300 Alpaca prompt pairs. Training and test groups are
split by `source_id`, with zero source overlap.

The recorded synthetic accuracy, precision, recall and F1 are 1.0. These values
only measure the constructed wrapper-classification task; they are not clinical
safety or real-world prompt-injection performance claims.

To reproduce the model with a separately obtained raw dataset:

```powershell
python -B scripts\train_risk_model.py --alpaca "<path-to-alpaca_data.json>" --sample-pairs 300
```

The raw `alpaca_data.json` is not included and is ignored by Git.

## API

| Method and route | Purpose |
|---|---|
| `GET /dashboard` | Analyst web interface |
| `GET /review-history` | Searchable redacted decision-history interface |
| `GET /health` | Service and defense-layer health |
| `GET /api/status` | Safe configuration and metrics |
| `POST /api/config` | Change runtime defense switches |
| `GET /api/events` | Read recent redacted audit metadata |
| `POST /api/demo/analyze` | Analyze one offline or live scenario |
| `POST /api/demo/batch` | Evaluate the bundled security samples |
| `POST /v1/chat/completions` | Protected OpenAI-compatible request |
| `GET /v1/models` | Provider passthrough |

System design, AI integration and robustness details are in
[`docs/project_report.md`](docs/project_report.md). The retained I1 scope and
acceptance criteria are in [`docs/iteration1_mvp.md`](docs/iteration1_mvp.md).

