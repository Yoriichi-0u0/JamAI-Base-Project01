"""Service layer that orchestrates validation and JamAI calls."""

from __future__ import annotations

import logging

from .jamai_client import call_action_table
from .models import CopilotRequest, CopilotResponse

LOGGER = logging.getLogger(__name__)


def process_parent_request(
    student_name: str,
    student_level: str,
    current_mode: str,
    current_slot: str,
    raw_request: str,
    notes: str = "",
) -> CopilotResponse:
    """
    Build a CopilotRequest and call JamAI Base.

    Args:
        student_name: Name of the student.
        student_level: Level label provided by the admin.
        current_mode: Attendance mode.
        current_slot: Free text slot description.
        raw_request: Full text from the parent.
        notes: Optional internal notes.

    Returns:
        Parsed CopilotResponse from JamAI Base.

    Raises:
        ValueError: If mandatory fields are missing.
    """

    normalized_student = student_name.strip()
    normalized_level = student_level.strip()
    normalized_request = raw_request.strip()

    if not normalized_student:
        raise ValueError("Student name is required.")
    if not normalized_level:
        raise ValueError("Student level is required.")
    if not normalized_request:
        raise ValueError("Parent request cannot be empty.")

    request_payload = CopilotRequest(
        student_name=normalized_student,
        student_level=normalized_level,
        current_mode=current_mode.strip(),
        current_slot=current_slot.strip(),
        raw_request=normalized_request,
        notes=notes.strip() or None,
    )

    LOGGER.debug("Sending CopilotRequest to JamAI: %s", request_payload.dict())
    return call_action_table(request_payload)


__all__ = ["process_parent_request"]
