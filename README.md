# Realfun AI Admin Copilot

Streamlit-based copilot for tuition center admins. Paste a parent's message, add student context, and let JamAI Base parse the intent, suggest new class slots, and draft a ready-to-send WhatsApp reply.

## Prerequisites

- Python 3.11+
- A JamAI Base project with access to an Action Table.

## Setup

```bash
python -m venv .venv
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
- `JAMAI_ACTION_TABLE_ID` (default suggested ID: `realfun_requests`)

## JamAI Base setup

1. Create a JamAI project.
2. Create an **Action Table** with ID `realfun_requests` (or your chosen ID referenced in `.env`).
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

- You are a scheduling assistant for a coding tuition center called **Realfun**.
- Understand intents: reschedule, new enrolment, cancel, generic query.
- Use Knowledge Table rows for actual slot availability and Zoom/venue details.
- Return `slot_options` and `warnings` as JSON lists; each slot item may include `label`, `internal_code`, `confidence`.
- Keep `whatsapp_message` concise, polite, and formatted in the center’s house style with clear bullet points.

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

