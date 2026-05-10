"""Analytics dashboard tab."""
import streamlit as st


def render_dashboard():
    st.subheader("📊 Session Analytics")

    history = st.session_state.get("history", [])

    if not history:
        st.info("No verifications run yet in this session. Run a verification to see analytics.")
        return

    total      = len(history)
    approved   = sum(1 for h in history if h["decision"] == "APPROVE")
    rejected   = sum(1 for h in history if h["decision"] == "REJECT")
    referred   = sum(1 for h in history if h["decision"] == "REFER")
    avg_conf   = sum(h["confidence"] for h in history) / total if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Checks",    total)
    c2.metric("✅ Approved",     approved)
    c3.metric("❌ Rejected",     rejected)
    c4.metric("⚠️ Referred",     referred)
    c5.metric("Avg Confidence",  f"{avg_conf:.1f}%")

    st.markdown("---")
    st.subheader("Recent Verifications")

    for h in history[:10]:
        icon = {"APPROVE": "✅", "REJECT": "❌", "REFER": "⚠️"}.get(h["decision"], "❓")
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        col1.write(h["customer"])
        col2.write(h["product"])
        col3.write(f"{icon} {h['decision']}")
        col4.write(f"{h['confidence']:.0f}%")
