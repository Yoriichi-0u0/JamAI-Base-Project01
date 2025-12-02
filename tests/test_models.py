from app.models import RealfunResponse, RecommendedSlot


def test_realfun_response_instantiation():
    slot = RecommendedSlot(label="Saturday 3-4.30 pm Online", internal_code="SAT_1500_1630_ONLINE", confidence=0.92)
    response = RealfunResponse(
        intent="reschedule",
        summary="Move to a weekend online slot.",
        recommended_slots=[slot],
        chosen_slot=None,
        whatsapp_message="Hi parent, here is the proposed new slot...",
        warnings=["Confirm teacher availability", "Check with student on timing"],
    )

    assert response.intent == "reschedule"
    assert response.chosen_slot is None
    assert response.recommended_slots[0].label.startswith("Saturday")
    assert len(response.warnings) == 2

