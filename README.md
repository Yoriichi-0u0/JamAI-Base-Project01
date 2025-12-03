# AI Admin Copilot

Streamlit-based copilot for tuition center admins. Paste a parent's message, add student context, and let JamAI Base parse the intent, suggest new class slots, and draft a ready-to-send WhatsApp reply.

## Prerequisites

- Python 3.11+ (3.11/3.12 recommended to pick up prebuilt wheels for Streamlit/pyarrow)
- A JamAI Base project with access to an Action Table.

## Setup

```bash
py -3.11 -m venv .venv
.\.venv\Scripts\activate   # on Windows
source .venv/bin/activate  # on macOS/Linux
pip install -r requirements.txt
```

Create your `.env` file from the template:

```bash
cp .env.example .env
```

Fill in:

- `JAMAI_PROJECT_ID`
- `JAMAI_PAT`
- `JAMAI_ACTION_TABLE_ID` (default suggested ID: `admin_requests`)

## JamAI Base setup

1. Create a JamAI project.
2. Create an **Action Table** with ID `admin_requests` (or your chosen ID referenced in `.env`).
3. Input columns expected by this app:
   - `raw_request` (str)
   - `student_name` (str)
   - `student_level` (str)
   - `current_mode` (str)
   - `current_slot` (str)
   - `notes` (str)
4. Output columns your LLM prompt must produce:
   - `intent` (str)
   - `summary` (str)
   - `slot_options` (str, ideally JSON list of slot objects or labels)
   - `chosen_slot` (str, one slot label or code)
   - `whatsapp_message` (str)
   - `warnings` (str, ideally JSON list of warning strings)
5. (Recommended) Create a Knowledge Table describing available schedules/Zoom links so the LLM can reference real data.

### Suggested Action Table prompt outline

- You are a scheduling assistant for a coding tuition center supporting admins handling parent requests.
- Understand intents: reschedule, new enrolment, cancel, generic query.
- Use Knowledge Table rows for actual slot availability and Zoom/venue details.
- Return `slot_options` and `warnings` as JSON lists; each slot item may include `label`, `internal_code`, `confidence`.
- Keep `whatsapp_message` concise, polite, and formatted in the center’s house style with clear bullet points.

## Using the app

1. Activate your virtual environment and run:
   ```bash
   streamlit run app/main_app.py
   ```
2. Fill in the form on the left:
   - **Student name** and **Student level** are required.
   - **Current mode/slot** help the AI propose similar slots.
   - **Parent request** is the original message (paste WhatsApp/email).
   - **Internal notes** add constraints (teacher availability, exams, etc.).
3. Click **Generate recommendation**. The right column will show:
   - **Intent badge** and a one-line **Summary**.
   - **Recommended slots** table (label, internal code, confidence).
   - **Chosen slot** (if the AI picked one) or a reminder to choose manually.
   - **WhatsApp message** ready to copy; use the **Copy to clipboard** button.
   - **Warnings** if the AI surfaced conflicts or follow-ups.
4. If outputs look verbose or raw, refine your JamAI Action Table prompt to return clean strings/JSON for `intent`, `summary`, `slot_options`, and `whatsapp_message`. The app already trims chat-completion boilerplate, but concise outputs improve readability.

### Trying real timetable data

The Python app does not manage schedules directly. Load your timetable (e.g., from `NewTimetable.xlsx`) into JamAI as a Knowledge Table or reference data so the Action Table prompt can recommend real slots and codes. Then set `JAMAI_ACTION_TABLE_ID` and rerun the app to test with live data.

## Running the app

```bash
streamlit run -m app.main_app
# or
streamlit run app/main_app.py
```

The UI has a two-column layout: inputs on the left, AI interpretation and WhatsApp-ready output on the right.

## Testing

```bash
pytest
```

## Limitations and future work

- Better validation of time slots and conflict detection against a live timetable.
- Integration with a real student database/CRM for identity and enrollment checks.
- Authentication/role-based access and audit logging for admin actions.
