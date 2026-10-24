# Event Planner (GenAI-assisted)

Plan a **wedding, birthday or community event** in one click. Enter the date, guest count and budget and get:

- a **budget** split by category that always adds up to your exact total
- a dated **timeline** with tick-off tasks (progress is remembered in your browser)
- a **vendor checklist** with booking deadlines and the questions to ask each vendor
- **personalised ideas** (themes, activities, menu, tips) from an LLM on Groq, or from built-in suggestions when no API key is set

**Live demo:** https://event-planner-zkkr.onrender.com/
**Demo video:** https://drive.google.com/file/d/1W2nOjRc-aqn2sa2qV68C5qmjE0aDuF8j/view

## Run it in VS Code

1. Install **Python 3.10+** and the VS Code _Python_ extension.
2. Open this folder in VS Code (**File > Open Folder**), then open a terminal (**Terminal > New Terminal**).
3. Create a virtual environment and install packages.

   **Windows (PowerShell)**

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

   **macOS / Linux**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

   If VS Code asks, choose `.venv` as the interpreter (**Ctrl+Shift+P > Python: Select Interpreter**).

4. _(Optional, for AI ideas)_ copy `.env.example` to `.env` and paste your Groq key (free at https://console.groq.com/keys) after `GROQ_API_KEY=`.
5. Start the app: press **F5** (the "Event Planner (FastAPI)" launch profile is included) or run
   ```bash
   uvicorn app.main:app --reload
   ```
6. Open <http://127.0.0.1:8000>.

### Run the tests

```bash
pytest
```

or use the VS Code **Testing** panel (the flask icon); pytest is pre-configured.

### Lint

```bash
ruff check app tests
```

## API

`POST /api/plan` with JSON:

```json
{
  "event_type": "birthday",
  "title": "Mira's 8th birthday",
  "event_date": "2027-03-14",
  "guest_count": 40,
  "total_budget": 20000,
  "currency": "INR",
  "location": "Berhampore",
  "preferences": "kids, eggless cake"
}
```

`GET /api/health` reports status and whether AI is active.
Errors: `422` invalid input (with field-level details), `413` body too large, `429` too many requests.

## How the code is organised

| File                                | Responsibility                                                    |
| ----------------------------------- | ----------------------------------------------------------------- |
| `app/models.py`                     | Validated request and response models                             |
| `app/catalog.py`                    | Planning knowledge as data (splits, milestones, vendor questions) |
| `app/budget.py`                     | Exact money allocation                                            |
| `app/timeline.py`, `app/vendors.py` | Date scheduling and vendor checklist                              |
| `app/ideas.py`                      | Offline + Groq LLM idea generators and the safe fallback wrapper  |
| `app/planner.py`                    | Combines everything; a pure function with injected dependencies   |
| `app/security.py`                   | Rate limiter and security headers                                 |
| `app/main.py`                       | FastAPI app factory and routes                                    |
| `app/static/`                       | Accessible, responsive web UI (no build step)                     |
| `tests/`                            | Unit and API tests                                                |

## Design decisions (mapped to the evaluation criteria)

**1. Clean, readable, well-structured code**
Small single-purpose modules, type hints throughout, docstrings that explain _why_, and planning data separated from logic.

**2. Safe practices**

- Every input is bounded (length, range, pattern, enum); unknown fields are rejected; NaN/infinity budgets are rejected.
- The API key comes only from the environment, is hidden from `repr`, and `.env` is git-ignored.
- LLM safety: user text is escaped and wrapped in tags the model is told to treat as data; the reply must be strict JSON that passes schema validation (length and count limits) or it is discarded. The event title is never sent to the model.
- The UI inserts all text with `textContent` (no HTML injection / XSS), and a strict Content-Security-Policy plus other security headers are sent.
- Rate limiting, request-size limit, API docs disabled, and error logs record only the error type, never user content.

**3. Time and memory**

- Plan building is O(number of template items), far under a millisecond.
- AI results are cached in a bounded LRU keyed on what actually affects the ideas, so repeat requests cost nothing.
- The LLM call has a timeout and one retry, and runs in a worker thread so it never blocks other users.
- The rate limiter evicts idle clients so memory stays bounded.

**4. Testability and maintainability**

- `create_app` and `build_plan` accept injected fakes (idea generator, clock), so tests need no network and no real time.
- 100+ tests cover money rounding, date scheduling, validation, prompt-injection handling, AI failure fallback, security headers and rate limiting.
- Changing advice means editing `catalog.py`, not logic.

**5. Usability for diverse users and environments**

- Works with no API key, no database and no build tools; runs on Windows, macOS and Linux.
- Responsive layout, keyboard-friendly, labelled fields, screen-reader live region, visible focus, dark mode, reduced-motion support.
- Currency selector with locale-aware formatting from the browser; plain-language errors; works on slow connections (no frameworks, no external requests).
- Print / save as PDF and JSON download.

**6. Targeting the real problem**
Event organisers struggle with _what to do, in what order, with how much money_. The app answers exactly that. When there is little time left it compresses the schedule proportionally, warns the user, and still puts high-priority vendors first.

## Known limits and next steps

- The rate limiter is per process. Behind a proxy or several workers, also limit at the gateway and pass the real client IP.
- Budget splits and timelines are general guidance, not local price quotes. Adding per-city price data would be the next improvement.
- Plans are not stored on a server; ticked tasks live in the browser only. Add accounts and a database if sharing between organisers is needed.
