import json
from types import SimpleNamespace

import pytest

from app.jamai_client import JamAIResponseError, call_action_table
from app.models import CopilotRequest


def _make_completion(columns: dict) -> SimpleNamespace:
    return SimpleNamespace(rows=[SimpleNamespace(columns=columns)])


def test_call_action_table_builds_request_and_parses(monkeypatch):
    captured = {}
    fake_completion = _make_completion(
        {
            "intent": "reschedule",
            "summary": "Move to a weekend slot.",
            "slot_options": json.dumps(
                [
                    {
                        "label": "Saturday 3-4.30 pm Online",
                        "internal_code": "SAT_1500_1630_ONLINE",
                        "confidence": 0.9,
                    }
                ]
            ),
            "chosen_slot": json.dumps(
                {"label": "Saturday 3-4.30 pm Online", "internal_code": "SAT_1500_1630_ONLINE"}
            ),
            "whatsapp_message": "Hi parent, recommended new slot attached.",
            "warnings": json.dumps(["Confirm teacher availability"]),
        }
    )

    class FakeTable:
        def add_table_rows(self, table_type, payload):
            captured["table_type"] = table_type
            captured["payload"] = payload
            return fake_completion

    fake_client = SimpleNamespace(table=FakeTable())
    fake_settings = SimpleNamespace(jamai_action_table_id="admin_requests")

    monkeypatch.setattr("app.jamai_client.get_client", lambda: fake_client)
    monkeypatch.setattr("app.jamai_client.get_settings", lambda: fake_settings)

    request = CopilotRequest(
        student_name="Ada Lovelace",
        student_level="Level 1",
        current_mode="online",
        current_slot="Sat 1-2pm",
        raw_request="Can we move to an online slot on Saturday afternoon?",
    )

    response = call_action_table(request)

    assert captured["table_type"] == "action"
    assert captured["payload"].table_id == fake_settings.jamai_action_table_id
    assert captured["payload"].data[0]["student_name"] == "Ada Lovelace"
    assert response.intent == "reschedule"
    assert response.recommended_slots[0].internal_code == "SAT_1500_1630_ONLINE"
    assert response.chosen_slot is not None
    assert response.chosen_slot.label.startswith("Saturday")
    assert response.warnings == ["Confirm teacher availability"]


def test_call_action_table_handles_malformed_slots(monkeypatch):
    raw_slots = "• Sat 2pm online\n• Sun 4pm physical"
    fake_completion = _make_completion(
        {
            "intent": "reschedule",
            "summary": "No structured slots provided.",
            "slot_options": raw_slots,
            "chosen_slot": "",
            "whatsapp_message": "Fallback message.",
            "warnings": "Double check teacher roster",
        }
    )

    class FakeTable:
        def add_table_rows(self, table_type, payload):
            return fake_completion

    fake_client = SimpleNamespace(table=FakeTable())
    fake_settings = SimpleNamespace(jamai_action_table_id="admin_requests")

    monkeypatch.setattr("app.jamai_client.get_client", lambda: fake_client)
    monkeypatch.setattr("app.jamai_client.get_settings", lambda: fake_settings)

    request = CopilotRequest(
        student_name="Alan Turing",
        student_level="Level 2",
        current_mode="physical",
        current_slot="Fri 5-6pm",
        raw_request="Need to move the class this week.",
    )

    response = call_action_table(request)

    assert response.recommended_slots[0].label.startswith("• Sat")
    assert response.chosen_slot is None
    assert response.warnings == ["Double check teacher roster"]
