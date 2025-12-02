"""Streamlit entrypoint for the Realfun AI Admin Copilot."""

from __future__ import annotations

import logging

import streamlit as st

from .services import process_parent_request
from .ui import render_response

LOGGER = logging.getLogger(__name__)


def _init_session_state() -> None:
    st.session_state.setdefault("request_inflight", False)
    st.session_state.setdefault("last_response", None)
    st.session_state.setdefault("form_error", "")


def run() -> None:
    """Render the Streamlit application."""

    st.set_page_config(page_title="Realfun AI Admin Copilot", layout="wide")
    _init_session_state()

    st.title("Realfun AI Admin Copilot")
    st.write(
        "Draft fast, consistent WhatsApp replies for parent schedule requests using JamAI Base."
    )

    left, right = st.columns(2)

    with left:
        with st.form("realfun_request_form"):
            student_name = st.text_input("Student name", key="student_name")
            student_level = st.selectbox(
                "Student level",
                options=["Level 1", "Level 2", "Level 3", "Unknown"],
                key="student_level",
            )
            current_mode = st.radio(
                "Current mode",
                options=["online", "physical", "mixed", "unknown"],
                key="current_mode",
            )
            current_slot = st.text_input(
                "Current slot",
                help="Optional. Example: Sat 1-2.30 pm",
                key="current_slot",
            )
            raw_request = st.text_area(
                "Parent request",
                height=150,
                key="raw_request",
                help="Paste the parent's WhatsApp message or email content.",
            )
            notes = st.text_area(
                "Internal notes",
                height=100,
                key="internal_notes",
                help="Optional context for the AI such as history or constraints.",
            )

            submit = st.form_submit_button(
                "Generate recommendation",
                disabled=st.session_state["request_inflight"],
            )

        if submit:
            st.session_state["request_inflight"] = True
            try:
                with st.spinner("Contacting AI backend..."):
                    response = process_parent_request(
                        student_name=student_name,
                        student_level=student_level,
                        current_mode=current_mode,
                        current_slot=current_slot,
                        raw_request=raw_request,
                        notes=notes,
                    )
                st.session_state["last_response"] = response
                st.session_state["form_error"] = ""
            except Exception as exc:  # pragma: no cover - UI guardrail
                st.session_state["last_response"] = None
                st.session_state["form_error"] = str(exc)
                LOGGER.exception("Error while processing parent request")
                st.error(f"Failed to generate recommendation: {exc}")
            finally:
                st.session_state["request_inflight"] = False

    with right:
        if st.session_state.get("last_response"):
            render_response(st.session_state["last_response"])
        elif st.session_state.get("form_error"):
            st.error(st.session_state["form_error"])
            st.info("Update the form and try again.")
        else:
            st.info("Fill in the form and click “Generate recommendation” to begin.")


if __name__ == "__main__":
    run()

