# Iteration 2 testing evidence

## Reproducible command

From a clean Python 3.12 virtual environment:

```powershell
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q
```

Verified final result:

```text
No broken requirements found.
42 passed
```

The dependency versions used to serialize the bundled model are pinned in
`requirements.txt`, avoiding an incompatible or unreproducible model artifact.

## I1 regression coverage

| Area | Evidence |
|---|---|
| Injection rules | Role override, prompt leak and medication manipulation paths |
| Sanitize mode | Suspicious instructions can be removed instead of blocking |
| Tool/RAG inspection | Tool and retrieved EHR content are scanned and isolated |
| Non-streaming Canary | Injected marker is detected in upstream output |
| ML risk scoring | Loading, fallback, extraction and risk ordering |
| Dataset split | Metadata records zero overlapping `source_id` groups |
| Offline demonstration | Clean simulated data returns labelled simulated output |
| Proxy integration | Clean requests reach a mock provider; blocked requests do not |
| Input and provider failures | Controlled 400 and 502 responses |
| Dashboard audience | Clinical AI Security Analyst is explicitly named |

## I2 feature and failure-path coverage

| Area | Evidence |
|---|---|
| Batch evaluation | Security metrics and per-sample ML evidence are returned |
| Analysis modes | Defense-only, simulated-AI and live-upstream paths |
| Server-side credential | Live Dashboard mode uses the environment credential without exposing it in status |
| Streaming protection | Complete and split Canary leaks are blocked before partial forwarding |
| Streaming resilience | Malformed stream chunks do not crash the proxy |
| Multimodal validation | Text/image structures and invalid nested content are handled |
| Nested output scanning | Canary search covers tool calls and nested response fields |
| Upstream validation | Malformed JSON shapes return `invalid_upstream_response` |
| Request limits | Unknown modes, wrong field types and oversized batches are rejected |
| Metrics integrity | Upstream failures are not counted as passed requests |
| Dashboard UX | Batch, three modes, ML score, search and export controls are present; result, batch and event data use structured safe views with no raw JSON display |

All live-provider tests use a local mock aiohttp server. They prove integration
and error handling without requiring a real API key or external network call.

## Manual demo check

```powershell
python -B run.py --port 8081
```

Open:

```text
http://127.0.0.1:8081/health
http://127.0.0.1:8081/dashboard
```

Expected clean sample: `decision = passed`, `ml_risk.available = true`, and a
clearly labelled simulated output. Expected Role override sample:
`decision = blocked` and `category = role_override`.

Run batch evaluation and confirm that the summary contains detection rate,
false-positive rate and average latency. Filter the audit list and export the
visible results to confirm the analyst evidence workflow.
