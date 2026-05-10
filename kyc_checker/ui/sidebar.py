"""Sidebar configuration panel."""
import streamlit as st


PRODUCTS = [
    "Personal Loan",
    "Home Loan",
    "Credit Card",
    "Savings Account",
    "Fixed Deposit",
    "Business Loan",
    "Insurance",
]


def render_sidebar() -> str:
    st.sidebar.title("⚙️ Configuration")

    st.sidebar.markdown("### 🏦 Product")
    product = st.sidebar.selectbox("Product Being Applied For", PRODUCTS)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📐 Agent Architecture")
    st.sidebar.markdown("""
1. 🔎 Document Extraction  
2. 🛡️ Authenticity Check  
3. 🤳 Face Match  
4. ✅ Eligibility Rules  
5. ⚠️ Fraud & Sanctions  
6. 🧠 Decision Engine  
7. 📝 Audit Logger  
""")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<span style="font-size:0.8rem; color:#888;">Powered by <strong>Groq</strong> LLM API</span>',
        unsafe_allow_html=True,
    )

    return product
