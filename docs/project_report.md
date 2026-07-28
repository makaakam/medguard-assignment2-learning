# Iteration 1 technical report

## MVP and audience

Our Iteration 1 goal was a small system that could be installed locally, demonstrated without a paid API and connected to a real OpenAI-compatible model when credentials were available.

We defined one primary audience: **Clinical AI Security Analyst**. This user needs to inspect prompt-injection decisions rather than receive medical advice. The Dashboard therefore prioritises defense status, processed messages and audit evidence.

## System architecture and design

```text
Client -> MedGuard Proxy -> Upstream LLM API
                |
                +-> Dashboard and audit events
```

| Component | File | Iteration 1 responsibility |
|---|---|---|
| Entry point | `run.py` | Starts the local aiohttp server |
| Proxy | `medguard_core/proxy.py` | Validates requests and coordinates the defense pipeline |
| Injection Guard | `medguard_core/detectors.py` | Detects suspicious instructions in user and tool text |
| RAG Isolation | `medguard_core/isolation.py` | Marks clinical context as untrusted data |
| Canary | `medguard_core/canary.py` | Adds a secret marker and checks non-streaming model output |
| Audit | `medguard_core/audit.py` | Stores event metadata without API keys or full messages |
| Dashboard | `medguard_core/dashboard.py` | Runs the classroom demonstration |

Separating these components lets team members test and explain one module without reading the whole proxy at once.

## AI output and simulated data

The offline Dashboard uses simulated EHR/RAG text. For an accepted request it produces a clearly labelled simulated clinical-assistant output. This makes the security workflow demonstrable without network access or a shared API key.

The actual proxy path forwards clean, non-streaming `/v1/chat/completions` requests to an OpenAI-compatible provider. Automated tests use a mock LLM server to prove that clean traffic reaches the upstream service and blocked traffic does not.

The simulated output is not presented as medical advice or as evidence of model accuracy. This build does not validate medical facts.

## Defense choices

1. Injection Guard offers an immediate, explainable decision for common role override, prompt leak and unsafe medication patterns.
2. RAG Isolation separates instructions from retrieved EHR/tool text and treats the retrieved text as data.
3. Canary checks whether a protected system marker appears in non-streaming model output.

We chose block and sanitize modes because an analyst may need either a strict demonstration or a comparison of the transformed request.

## API

| Endpoint | Purpose |
|---|---|
| `GET /dashboard` | Iteration 1 user interface |
| `GET /health` | Server and defense-layer status |
| `GET /api/status` | Runtime configuration and basic counters |
| `POST /api/config` | Change defense switches and block/sanitize mode |
| `GET /api/events` | Read recent audit metadata |
| `POST /api/demo/analyze` | Run the offline MVP analysis |
| `POST /v1/chat/completions` | Protected non-streaming model request |
| `GET /v1/models` | Provider passthrough |

## Robustness boundary

Iteration 1 returns controlled errors for malformed JSON, invalid message arrays, unavailable upstream services and unsupported streaming requests. It binds to `127.0.0.1` by default.

The following work is intentionally deferred:

- Batch Security Evaluation and calculated detection metrics;
- Dashboard Live upstream AI mode;
- streaming Canary protection;
- multimodal input and nested output scanning;
- event filtering/export;
- broader attack datasets and advanced provider compatibility.

These items form a visible Iteration 2 backlog rather than hidden functionality in the MVP.
