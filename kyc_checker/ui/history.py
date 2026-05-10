"""History tab — full session log."""
import streamlit as st
import json


def render_history():
    st.subheader("📁 Verification History")

    history = st.session_state.get("history", [])

    if not history:
        st.info("No history yet. Run verifications in the 'New Verification' tab.")
        return

    if st.button("🗑️ Clear History"):
        st.session_state["history"] = []
        st.rerun()

    for i, h in enumerate(history):
        icon = {"APPROVE": "✅", "REJECT": "❌", "REFER": "⚠️"}.get(h["decision"], "❓")
        with st.expander(f"{icon} {h['customer']} — {h['product']} | {h['timestamp']}"):
            st.json(h)
