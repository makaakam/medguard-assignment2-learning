# MedGuard final technical report

## Objective and audience

MedGuard is a deployable prototype that integrates model-oriented security
analysis with simulated and optional live data. Its primary user is a
**Clinical AI Security Analyst**. The system supports that user in evaluating
prompt-injection attempts, inspecting evidence and demonstrating protections;
it is not a diagnostic or medical-advice system.

The design keeps an offline classroom path so assessors can reproduce the demo
without a paid service, while also providing an OpenAI-compatible live path.

## System architecture

```text
Browser Dashboard                     OpenAI-compatible client
        |                                       |
        +-------------------+-------------------+
                            v
                 aiohttp API and validation
                            |
          +-----------------+------------------+
          |                 |                  |
   Injection Guard     RAG Isolation      ML Risk Scorer
          +-----------------+------------------+
                            |
                     Canary protection
                            |
                 simulated or live output
                            |
                  redacted audit evidence
```

| Component | File | Responsibility |
|---|---|---|
| Entry point | `run.py` | Loads safe environment settings and starts aiohttp |
| API/proxy | `medguard_core/proxy.py` | Validates input, coordinates defenses and forwards requests |
| Rule detector | `medguard_core/detectors.py` | Produces explainable injection categories |
| Isolation | `medguard_core/isolation.py` | Treats EHR/RAG/tool content as untrusted data |
| Canary | `medguard_core/canary.py` | Detects prompt leakage in normal, nested and streamed output |
| ML scorer | `medguard_core/risk_model.py` | Produces a local risk probability and action |
| Audit | `medguard_core/audit.py` | Stores bounded event metadata without keys or full clinical text |
| Dashboard | `medguard_core/dashboard.py` | Presents readable decisions, AI output, signals, protected message flow and batch evidence |

The modules separate responsibilities so each defense can be tested and
explained independently while the proxy remains the integration point.

## AI model and data integration

The offline Dashboard combines simulated EHR/RAG content with clearly labelled
simulated assistant output. This satisfies a reproducible real-time interaction
flow without claiming that fabricated output is medical advice.

The local ML component is a scikit-learn TF-IDF and logistic-regression
pipeline. It was trained on 900 constructed examples derived from 300 Alpaca
prompt pairs. Grouped splitting by `source_id` prevents the same original pair
from appearing in both train and test sets. The stored metadata records zero
group overlap and synthetic accuracy, precision, recall and F1 of 1.0.

Those metrics describe only the constructed wrapper patterns. They do not
establish external, clinical or production prompt-injection performance. The
explainable rules remain visible, and if the model cannot load the other
defense layers continue operating with an `available = false` model status.

For live integration, accepted requests can be sent to an OpenAI-compatible
provider. The Dashboard obtains the optional provider key from the server
environment, while an API client may provide its own authorization header.
Automated tests use a local mock provider so no secret or paid API is required.

## UX and technical design choices

- One named audience avoids mixing security analysis with clinical diagnosis.
- A three-step request check gives first-time users a clear starting point: enter the task, choose how it runs and review the outcome.
- Primary outcomes use `Safe to continue`, `Review recommended` and `Request stopped`; technical categories remain in an expandable evidence section.
- Input guidance explains what belongs in each field and warns users to enter demonstration data rather than real patient information.
- Clean, attack and poisoned-EHR samples provide a repeatable demonstration.
- `Stop unsafe requests` and `Remove unsafe instructions and continue` expose the operational trade-off without relying on the term sanitize.
- `Check safety only`, `Use a sample AI response` and `Use a connected AI model` make response provenance clear.
- Rule category, ML score, processed messages and audit events give explainable evidence.
- Batch metrics help the analyst compare attacks and benign samples.
- Search and JSON export support review after the live demonstration.
- API and model data are rendered through safe DOM text operations; raw JSON is not displayed, protected system instructions and security markers are hidden, and JSON is available only through explicit event export.
- The server binds to `127.0.0.1` by default and never returns its configured API key.

## From Iteration 1 to Iteration 2

The optimized I1 baseline delivered the Dashboard, rule detection, isolation,
non-streaming Canary checks, local ML risk score, simulated output, protected
non-streaming proxy and controlled input/provider errors.

Iteration 2 adds:

1. batch evaluation with detection, false-positive and latency metrics;
2. live-upstream Dashboard mode using an optional server-side credential;
3. streaming Canary protection, including split token fragments;
4. multimodal message validation and nested/tool-call response scanning;
5. stricter request, mode, batch and upstream-response validation;
6. audit-event filtering/export and expanded status metrics;
7. full regression and abnormal-path tests covering both iterations.

The original I1 branch/tag and the optimized I1 branch/tag are retained, while
the final I2 branch is built directly on the optimized I1 commit.

## API

| Endpoint | Purpose and main behavior |
|---|---|
| `GET /dashboard` | Analyst-facing web system |
| `GET /health` | Reports service and enabled defense layers |
| `GET /api/status` | Returns safe config and calculated counters |
| `POST /api/config` | Updates allow-listed runtime switches |
| `GET /api/events` | Returns recent redacted audit evidence |
| `POST /api/demo/analyze` | Runs defense-only, simulated or live analysis |
| `POST /api/demo/batch` | Evaluates the bounded sample set and metrics |
| `POST /v1/chat/completions` | Protected OpenAI-compatible completion path |
| `GET /v1/models` | Controlled provider passthrough |

## Robustness and error handling

The API rejects non-object JSON, invalid message arrays, unsupported content
shapes, wrong field types, unknown analysis modes and oversized batches with
controlled client errors. Provider timeouts or connection failures return a
controlled `502` response. Malformed upstream objects are rejected instead of
being trusted. Streaming output is buffered until the Canary check completes,
preventing a leaked fragment from being forwarded first.

Upstream failures have their own audit category and are not counted as passed
security decisions. Audit records redact credentials and avoid storing full
clinical messages. These controls improve demonstration safety, but production
deployment would still require authentication, TLS termination, authorization,
persistent secured audit storage, rate limiting and an externally validated
security dataset.

## Deployment and demonstration

Install from `requirements.txt`, run `python -B run.py --port 8081`, and open
`http://127.0.0.1:8081/dashboard`. The system is usable offline. Optional live
mode is enabled through `MEDGUARD_UPSTREAM_API_KEY`,
`MEDGUARD_UPSTREAM_MODEL` and the `--target` provider base URL.

The recommended demonstration shows a clean request, a blocked role override,
an isolated poisoned EHR sample, sanitize mode, batch metrics and filtered audit
evidence. This sequence makes the UX, AI integration and technical defenses
visible within one reproducible run.
