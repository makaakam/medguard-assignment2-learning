# Iteration 1 MVP definition

## User story

As a Clinical AI Security Analyst, I want to inspect a clinical LLM request before it reaches the model so that I can demonstrate prompt-injection detection, untrusted-data isolation and prompt-leak protection.

## Acceptance criteria

1. The application starts locally from documented commands.
2. The Dashboard names Clinical AI Security Analyst as its only primary user.
3. A clean simulated clinical request returns a labelled simulated AI output.
4. Each analysis includes an explainable local ML prompt-injection risk score.
5. A role-override request is blocked before upstream forwarding.
6. Tool/EHR/RAG text is scanned and can be isolated as untrusted data.
7. A Canary marker is injected and checked in non-streaming model output.
8. A clean non-streaming request can reach an OpenAI-compatible upstream provider.
9. Invalid input and unavailable upstream services return controlled errors.
10. Automated tests and manual demo steps are documented.
11. The Dashboard presents results as readable structured evidence without exposing raw JSON, hidden system instructions or security markers.

## Iteration 2 backlog

- Batch Security Evaluation;
- detection-rate, false-positive-rate and latency metrics;
- Dashboard live-model mode;
- streaming output protection;
- multimodal and nested output handling;
- event filtering/export;
- expanded validation and provider hardening.

