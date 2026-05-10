"""Session state initialiser for Streamlit."""
import streamlit as st


def init_session_state():
    defaults = {
        "history":       [],
        "demo_loaded":   False,
        "run_triggered": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
