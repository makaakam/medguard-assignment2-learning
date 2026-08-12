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
69 passed
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
| Dashboard guidance | The task and optional-context fields have introductions, examples, accessible descriptions and a demonstration-data warning |
| Plain-language decisions | Safe, review and stopped outcomes are shown while technical evidence remains available separately |
| Dashboard UX | First-visit five-step guide, field-level help, three run choices and sample testing use structured safe views with no raw JSON display |
| Review history | Separate page supports outcome filters, readable evidence cards, search, retry guidance and redacted report download |
| Responsive control alignment | Run mode, optional model input and action buttons use equal-height desktop controls, a two-column tablet layout and a single-column mobile layout |
| Semantic status colours | Safe outcomes use green, review/error states use red, stopped requests use deep red, information uses blue and inactive states use grey |
| Default first-run experience | The initial demonstration record is anonymous and safe, and completed checks move focus to the readable outcome |
| Safety-only guidance | A safety-only result does not tell the user to review an AI answer that was never produced |

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
http://127.0.0.1:8081/review-history
```

Expected clean sample: the Dashboard shows **Safe to continue**, the API returns
`decision = passed` and `ml_risk.available = true`, and the sample response is
clearly labelled. Expected Role override sample: the Dashboard shows **Request
stopped**, while the API returns `decision = blocked` and
`category = role_override`.

Select **Test sample requests** and confirm that the summary explains unsafe
examples found, safe examples incorrectly flagged and average check time. Open
**Review History**, filter the cards and download the report to confirm the
analyst evidence workflow.

Responsive visual validation was also performed at 1440, 1024, 768 and 390
pixel browser widths. No horizontal overflow was observed. On the desktop
layout, the run-mode selector, optional connected-model field and both action
buttons remain aligned. Browser console review of both application pages
reported no application warnings or errors.
