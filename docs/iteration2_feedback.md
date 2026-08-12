# Iteration 1 Feedback Applied in Iteration 2

This record links the academic staff feedback reported after the Iteration 1
demonstration to concrete Iteration 2 work. It separates implemented evidence
from evidence that the team must still add to the live Trello board.

## Feedback source

The team recorded four points from the verbal staff feedback:

1. add guidance or an introduction near the user-message input;
2. use simple words and make the interface user-friendly;
3. add useful comments to the code;
4. record the work as Trello tasks.

## Improvement and evidence matrix

| Feedback | Iteration 2 response | Repository evidence | Validation | Trello card |
|---|---|---|---|---|
| Guide the user-message input | The task and optional-context inputs now explain what to enter, include examples and warn against real patient data. The first loaded record is an anonymous safe example. | `medguard_core/dashboard.py` | `tests/test_dashboard_user_guidance.py` | `I2-FB-01 Guided user-message entry` |
| Make the first workflow easier to learn | A five-step interactive first-visit guide highlights the task, context, run mode and check action. Help restarts it. Review History is now a separate page so the request workflow stays focused. | `medguard_core/dashboard.py`; `medguard_core/proxy.py` | Route, onboarding, spotlight and browser workflow tests | `I2-FB-05 Interactive onboarding and focused navigation` |
| Use simple, user-friendly words | The main result is expressed as `Safe to continue`, `Review recommended` or `Request stopped`. Run choices, buttons and next steps describe user actions rather than internal implementation. Technical evidence is available separately. | `medguard_core/dashboard.py`; `docs/project_report.md` | Dashboard wording tests and browser checks at desktop, tablet and mobile widths | `I2-FB-02 Plain-language analyst workflow` |
| Add code comments | Short comments explain security-sensitive choices such as keeping credentials server-side, preventing empty requests, protecting streamed markers and handling unknown wrappers. Obvious statements are not narrated. | `medguard_core/config.py`; `canary.py`; `detectors.py`; `isolation.py`; `proxy.py`; `dashboard.py` | Code review plus the full regression suite | `I2-FB-03 Security-focused code comments` |
| Add Trello tasks | The feedback is split into owned cards with a user story, acceptance criteria, code evidence, test evidence and review status. | This file and the shared-folder Trello card guide | Team verifies the live card links, owners and Done status before submission | `I2-FB-04 Feedback traceability in Trello` |

## Acceptance criteria used for the feedback work

### I2-FB-01 Guided user-message entry

- A first-time analyst can tell what belongs in the task and optional-context fields.
- Each input has a short introduction or example.
- The page tells users to enter demonstration data rather than real patient information.
- Guidance remains readable on desktop, tablet and mobile layouts.

### I2-FB-02 Plain-language analyst workflow

- The primary decision uses task-oriented language rather than detector labels.
- Every outcome includes a clear next step.
- Technical terms are either explained or placed in the optional evidence section.
- Green, red, deep red, blue and grey keep the same operational meaning throughout the page.

### I2-FB-03 Security-focused code comments

- Comments explain non-obvious security, privacy or compatibility choices.
- Comments do not restate straightforward code.
- No comment refers to a writing tool or to the process used to draft it.
- All automated tests still pass after comment-only review changes.

### I2-FB-04 Feedback traceability in Trello

- Each of the three product changes has a named Trello task and owner.
- Each task contains its user story and acceptance criteria.
- Code files, test evidence and the feedback source are linked or attached.
- A reviewer checks the evidence before moving the task to Done.

## Evidence still requiring team action

Before final submission, the team should add the live Trello card URLs, confirm
each owner and reviewer, move completed cards to Done, and attach a board export
or screenshot to the shared folder. These live collaboration details are not
invented in this repository document.
