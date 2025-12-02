"""Pydantic models representing requests and responses for Realfun AI."""

from typing import List, Optional

from pydantic import BaseModel, Field


class RealfunRequest(BaseModel):
    """
    Normalized representation of a parent request for scheduling assistance.

    Attributes:
        student_name: Name of the student the request is about.
        student_level: Academic level label such as "Level 1".
        current_mode: Current attendance mode (online/physical/mixed/unknown).
        current_slot: Free text description of the student's current slot.
        raw_request: Original message text from the parent or guardian.
        notes: Optional internal notes to provide extra context.
    """

    student_name: str
    student_level: str
    current_mode: str
    current_slot: str
    raw_request: str
    notes: Optional[str] = None


class RecommendedSlot(BaseModel):
    """
    Slot recommendation parsed from JamAI output.

    Attributes:
        label: Human friendly slot description.
        internal_code: Optional internal code for the slot used by the center.
        confidence: Optional confidence score between 0 and 1.
    """

    label: str
    internal_code: Optional[str] = None
    confidence: Optional[float] = None


class RealfunResponse(BaseModel):
    """
    Structured AI response ready for the Streamlit UI.

    Attributes:
        intent: Parsed intent such as "reschedule" or "new_enrolment".
        summary: One sentence summary of the request.
        recommended_slots: List of possible slots returned by JamAI.
        chosen_slot: Slot selected by JamAI, if any.
        whatsapp_message: Final WhatsApp message for copy-paste.
        warnings: Any warnings or follow-up notes to highlight.
    """

    intent: str
    summary: str
    recommended_slots: List[RecommendedSlot]
    chosen_slot: Optional[RecommendedSlot]
    whatsapp_message: str
    warnings: List[str] = Field(default_factory=list)


__all__ = ["RealfunRequest", "RecommendedSlot", "RealfunResponse"]

