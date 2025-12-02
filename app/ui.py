"""UI helpers for the Streamlit app."""

from __future__ import annotations

import json
import textwrap
from typing import Iterable

import streamlit as st

from .models import RealfunResponse, RecommendedSlot


INTENT_COLORS = {
    "reschedule": "#1f77b4",
    "new_enrolment": "#2ca02c",
    "cancel": "#d62728",
    "generic_query": "#9467bd",
}


def _format_confidence(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.0%}"


def render_intent_badge(intent: str) -> None:
    """Render a colored badge for the detected intent."""

    color = INTENT_COLORS.get(intent.lower(), "#444")
    badge = textwrap.dedent(
        f"""
        <div style="
            display:inline-block;
            padding:4px 10px;
            background:{color};
            color:white;
            border-radius:8px;
            font-weight:600;">
            Intent: {intent.title()}
        </div>
        """
    )
    st.markdown(badge, unsafe_allow_html=True)


def render_recommended_slots(slots: Iterable[RecommendedSlot]) -> None:
    """Render recommended slots in a table-friendly format."""

    rows = []
    for slot in slots:
        rows.append(
            {
                "Label": slot.label,
                "Internal code": slot.internal_code or "",
                "Confidence": _format_confidence(slot.confidence),
            }
        )
    if rows:
        st.table(rows)
    else:
        st.info("No slot recommendations returned.")


def render_warnings(warnings: list[str]) -> None:
    """Show warnings as a single Streamlit warning box."""

    if not warnings:
        return
    formatted = "\n".join(f"- {warning}" for warning in warnings)
    st.warning(formatted)


def render_whatsapp_message(message: str) -> None:
    """Render WhatsApp message and provide a copy-to-clipboard helper."""

    st.text_area("WhatsApp message", value=message, height=220, key="whatsapp_message_box")
    payload = json.dumps(message)
    copy_button = f"""
    <button onclick='navigator.clipboard.writeText({payload})'
            style="margin-top:8px;padding:8px 12px;border-radius:6px;border:1px solid #ccc;cursor:pointer;">
        Copy to clipboard
    </button>
    """
    st.markdown(copy_button, unsafe_allow_html=True)


def render_response(response: RealfunResponse) -> None:
    """Render the full response panel."""

    render_intent_badge(response.intent)
    st.subheader("Summary")
    st.write(response.summary)

    st.subheader("Recommended slots")
    render_recommended_slots(response.recommended_slots)

    st.subheader("Chosen slot")
    if response.chosen_slot:
        st.success(response.chosen_slot.label)
    else:
        st.info("No slot automatically chosen. Please decide manually.")

    st.subheader("WhatsApp message")
    render_whatsapp_message(response.whatsapp_message)

    render_warnings(response.warnings)


__all__ = [
    "render_intent_badge",
    "render_recommended_slots",
    "render_response",
    "render_warnings",
    "render_whatsapp_message",
]

