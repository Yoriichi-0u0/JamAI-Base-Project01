"""Wrapper around the JamAI Base Python SDK."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from json import JSONDecodeError
from typing import Any, Iterable, List, Optional

from jamaibase import JamAI, types as t

from .config import get_settings, Settings
from .models import RealfunRequest, RealfunResponse, RecommendedSlot


LOGGER = logging.getLogger(__name__)


class JamAIResponseError(RuntimeError):
    """Raised when the JamAI response cannot be parsed into expected fields."""


def create_client(settings: Optional[Settings] = None) -> JamAI:
    """
    Instantiate a JamAI client using provided settings or environment defaults.

    Args:
        settings: Optional settings override, mainly used for testing.

    Returns:
        Configured JamAI client.
    """

    resolved_settings = settings or get_settings()
    return JamAI(project_id=resolved_settings.jamai_project_id, token=resolved_settings.jamai_pat)


@lru_cache(maxsize=1)
def get_client() -> JamAI:
    """
    Return a cached JamAI client for reuse across Streamlit reruns.
    """

    return create_client()


def _coerce_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_recommended_slots(raw: str) -> List[RecommendedSlot]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except JSONDecodeError:
        cleaned = raw.strip()
        return [RecommendedSlot(label=cleaned)] if cleaned else []

    slots: List[RecommendedSlot] = []
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, str):
                slots.append(RecommendedSlot(label=item))
            elif isinstance(item, dict):
                label = item.get("label") or item.get("name")
                if not label:
                    label = json.dumps(item, ensure_ascii=False)
                slots.append(
                    RecommendedSlot(
                        label=label,
                        internal_code=item.get("internal_code") or item.get("code"),
                        confidence=_coerce_float(item.get("confidence")),
                    )
                )
    elif isinstance(parsed, dict):
        label = parsed.get("label") or parsed.get("name") or raw.strip()
        slots.append(
            RecommendedSlot(
                label=label,
                internal_code=parsed.get("internal_code") or parsed.get("code"),
                confidence=_coerce_float(parsed.get("confidence")),
            )
        )
    if slots:
        return slots
    cleaned = raw.strip()
    return [RecommendedSlot(label=cleaned)] if cleaned else []


def _parse_chosen_slot(raw: str, options: Iterable[RecommendedSlot]) -> Optional[RecommendedSlot]:
    if not raw:
        return None
    cleaned = raw.strip()
    try:
        parsed = json.loads(cleaned)
    except JSONDecodeError:
        parsed = cleaned

    if isinstance(parsed, dict):
        return RecommendedSlot(
            label=parsed.get("label") or parsed.get("name") or cleaned,
            internal_code=parsed.get("internal_code") or parsed.get("code"),
            confidence=_coerce_float(parsed.get("confidence")),
        )
    if isinstance(parsed, str):
        for option in options:
            if parsed == option.label or parsed == option.internal_code:
                return option
        return RecommendedSlot(label=parsed)
    return None


def _parse_warnings(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    if isinstance(raw, str):
        cleaned = raw.strip()
        if not cleaned:
            return []
        try:
            parsed = json.loads(cleaned)
        except JSONDecodeError:
            return [line.strip() for line in cleaned.splitlines() if line.strip()]
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [cleaned]
    return [str(raw)]


def _extract_columns(completion: Any) -> dict[str, Any]:
    rows = getattr(completion, "rows", None)
    if rows is None and isinstance(completion, dict):
        rows = completion.get("rows")
    if not rows:
        raise JamAIResponseError("JamAI response contains no rows.")

    first_row = rows[0]
    columns = getattr(first_row, "columns", None)
    if columns is None and isinstance(first_row, dict):
        columns = first_row.get("columns")
    if not isinstance(columns, dict):
        raise JamAIResponseError("JamAI row missing 'columns' mapping.")
    return columns


def call_realfun_action_table(req: RealfunRequest) -> RealfunResponse:
    """
    Send a RealfunRequest to the JamAI Action Table and parse the response.

    Args:
        req: Normalized request payload.

    Returns:
        Parsed RealfunResponse ready for the UI.

    Raises:
        JamAIResponseError: When parsing fails or response is incomplete.
    """

    settings = get_settings()
    client = get_client()
    try:
        completion = client.table.add_table_rows(
            "action",
            t.MultiRowAddRequest(
                table_id=settings.jamai_action_table_id,
                data=[
                    {
                        "raw_request": req.raw_request,
                        "student_name": req.student_name,
                        "student_level": req.student_level,
                        "current_mode": req.current_mode,
                        "current_slot": req.current_slot,
                        "notes": req.notes or "",
                    }
                ],
                stream=False,
            ),
        )
        columns = _extract_columns(completion)
        intent = str(columns.get("intent", "")).strip()
        summary = str(columns.get("summary", "")).strip()
        slot_options_raw = str(columns.get("slot_options", "") or "")
        chosen_slot_raw = str(columns.get("chosen_slot", "") or "")
        whatsapp_message = str(columns.get("whatsapp_message", "")).strip()
        warnings_raw = columns.get("warnings", "")

        if not intent or not summary or not whatsapp_message:
            raise JamAIResponseError("JamAI response is missing required fields.")

        recommended_slots = _parse_recommended_slots(slot_options_raw)
        if not recommended_slots and slot_options_raw:
            recommended_slots = [RecommendedSlot(label=slot_options_raw.strip())]

        chosen_slot = _parse_chosen_slot(chosen_slot_raw, recommended_slots)
        warnings = _parse_warnings(warnings_raw)

        return RealfunResponse(
            intent=intent,
            summary=summary,
            recommended_slots=recommended_slots,
            chosen_slot=chosen_slot,
            whatsapp_message=whatsapp_message,
            warnings=warnings,
        )
    except JamAIResponseError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Failed to call JamAI Action Table")
        raise JamAIResponseError(f"Unexpected error while calling JamAI: {exc}") from exc


__all__ = [
    "JamAIResponseError",
    "call_realfun_action_table",
    "create_client",
    "get_client",
]

