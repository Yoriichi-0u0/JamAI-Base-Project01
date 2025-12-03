"""Wrapper around the JamAI Base Python SDK for the AI Admin Copilot."""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from json import JSONDecodeError
from typing import Any, Iterable, List, Optional

from jamaibase import JamAI, types as t

from .config import Settings, get_settings
from .models import CopilotRequest, CopilotResponse, RecommendedSlot


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


def _extract_completion_content(text: str) -> Optional[str]:
    """
    Attempt to pull the assistant message content out of a ChatCompletion-style string.
    """

    match = re.search(r"content='(.*?)'", text, flags=re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'"content":\s*"([^"]+)"', text, flags=re.DOTALL)
    if match:
        return match.group(1)
    return None


def _normalize_text_field(value: Any) -> str:
    """
    Normalize a field that may come back as a complex object or verbose string.
    """

    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    extracted = _extract_completion_content(text)
    if extracted:
        return extracted.strip()

    # If the string looks like a ChatCompletion dump, trim before usage/metadata.
    if "ChatCompletion" in text or "chatcmpl" in text:
        parts = text.split("usage=", 1)
        text = parts[0].strip()
        text = text.replace("choices=[", "").replace("message=", "")
        # Remove repeated prefixes like "ChatCompletionChoice(index=0,"
        text = re.sub(r"ChatCompletion\w*\([^)]*\)", "", text).strip(" ,[]")
    return text


def _looks_like_completion_blob(text: str) -> bool:
    lowered = text.lower()
    return ("chatcompletion" in lowered or "chatcmpl" in lowered) and ("id=" in lowered or "object=" in lowered)


def _build_fallback_message(summary: str, slots: List[RecommendedSlot], chosen: Optional[RecommendedSlot]) -> str:
    """
    Construct a human-friendly WhatsApp draft if the backend returns a blob.
    """

    lines = ["Hi! Here is a quick summary and options based on your request:"]
    if summary:
        lines.append(f"- Summary: {summary}")
    if chosen:
        lines.append(f"- Suggested slot: {chosen.label}")
    elif slots:
        lines.append("- Recommended slots:")
        for idx, slot in enumerate(slots[:5], start=1):
            lines.append(f"  {idx}. {slot.label}")
    lines.append("Please reply with your preferred option (or share a new timing), and we will confirm with the teacher.")
    return "\n".join(lines)


def _simplify_warning_text(value: Any) -> str:
    """
    Produce a concise warning string, trimming oversized blobs.
    """

    text = _normalize_text_field(value)
    if not text:
        return ""
    max_len = 400
    if len(text) > max_len:
        return text[:max_len].rstrip() + "..."
    return text


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
    cleaned = _normalize_text_field(raw)
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
        return [_simplify_warning_text(item) for item in raw if _simplify_warning_text(item)]
    if isinstance(raw, str):
        cleaned = _simplify_warning_text(raw)
        if not cleaned:
            return []
        try:
            parsed = json.loads(cleaned)
        except JSONDecodeError:
            return [line.strip() for line in cleaned.splitlines() if line.strip()]
        if isinstance(parsed, list):
            return [_simplify_warning_text(item) for item in parsed if _simplify_warning_text(item)]
        return [cleaned]
    normalized = _simplify_warning_text(raw)
    return [normalized] if normalized else []


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


def call_action_table(req: CopilotRequest) -> CopilotResponse:
    """
    Send a CopilotRequest to the JamAI Action Table and parse the response.

    Args:
        req: Normalized request payload.

    Returns:
        Parsed CopilotResponse ready for the UI.

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
        intent = _normalize_text_field(columns.get("intent", ""))
        summary = _normalize_text_field(columns.get("summary", ""))
        slot_options_raw = _normalize_text_field(columns.get("slot_options", "") or "")
        chosen_slot_raw = _normalize_text_field(columns.get("chosen_slot", "") or "")
        whatsapp_message = _normalize_text_field(columns.get("whatsapp_message", ""))
        warnings_raw = columns.get("warnings", "")

        if not intent or not summary:
            raise JamAIResponseError("JamAI response is missing required fields.")

        recommended_slots = _parse_recommended_slots(slot_options_raw)
        if not recommended_slots and slot_options_raw:
            recommended_slots = [RecommendedSlot(label=slot_options_raw.strip())]

        chosen_slot = _parse_chosen_slot(chosen_slot_raw, recommended_slots)
        warnings = _parse_warnings(warnings_raw)

        if not whatsapp_message or _looks_like_completion_blob(whatsapp_message):
            whatsapp_message = _build_fallback_message(summary, recommended_slots, chosen_slot)

        return CopilotResponse(
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
    "call_action_table",
    "create_client",
    "get_client",
]
