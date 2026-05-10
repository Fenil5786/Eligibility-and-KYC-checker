import streamlit as st
import json
import time
import os
import tempfile
from datetime import datetime
from pathlib import Path

GROQ_API_KEY = "your api key here"
GROQ_MODEL = "openai/gpt-oss-120b"

st.set_page_config(
    page_title="AI Eligibility & KYC Checker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .agent-card {
        background: #f8f9fa;
        border-left: 4px solid #0f3460;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .status-approve { color: #28a745; font-weight: bold; font-size: 1.2rem; }
    .status-reject  { color: #dc3545; font-weight: bold; font-size: 1.2rem; }
    .status-refer   { color: #ffc107; font-weight: bold; font-size: 1.2rem; }
    .step-complete  { color: #28a745; }
    .step-running   { color: #007bff; }
    .step-pending   { color: #6c757d; }
    .audit-box {
        background: #1e1e1e;
        color: #00ff00;
        font-family: monospace;
        padding: 1rem;
        border-radius: 8px;
        font-size: 0.85rem;
        max-height: 300px;
        overflow-y: auto;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .groq-badge {
        background: #f72585;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #dee2e6;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

from agents.orchestrator import KYCOrchestrator
from utils.session_manager import init_session_state
from ui.sidebar import render_sidebar
from ui.dashboard import render_dashboard
from ui.history import render_history

def main():
    init_session_state()

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 AI Eligibility & KYC Checker</h1>
        <p style="opacity:0.85; margin:0;">Powered by <strong>Groq LLM</strong> | Multi-Agent Agentic System</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar config
    product_type = render_sidebar()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 New Verification", "📊 Dashboard", "📁 History"])

    with tab1:
        render_verification_form(product_type)

    with tab2:
        render_dashboard()

    with tab3:
        render_history()


def render_verification_form(product_type):
    st.subheader("Customer KYC & Eligibility Verification")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 👤 Personal Information")
        full_name    = st.text_input("Full Name *", placeholder="e.g. Rahul Sharma")
        dob          = st.date_input("Date of Birth *", min_value=datetime(1920, 1, 1).date())
        gender       = st.selectbox("Gender", ["Male", "Female", "Other"])
        nationality  = st.text_input("Nationality", value="Indian")
        address      = st.text_area("Address *", placeholder="Full residential address", height=80)

        st.markdown("#### 💰 Financial Information")
        annual_income = st.number_input("Annual Income (₹)", min_value=0, step=10000, value=500000)
        employment    = st.selectbox("Employment Type", ["Salaried", "Self-Employed", "Business Owner", "Student", "Retired", "Unemployed"])
        credit_score  = st.slider("Credit Score (CIBIL)", 300, 900, 700)

    with col2:
        st.markdown("#### 📄 Document Information")
        doc_type   = st.selectbox("Primary ID Document *", ["Aadhaar Card", "PAN Card", "Passport", "Driving License", "Voter ID"])
        doc_number = st.text_input("Document Number *", placeholder="e.g. ABCDE1234F")
        doc_expiry = st.date_input("Document Expiry (if applicable)", value=None)

        st.markdown("#### 🌍 Additional Details")
        state    = st.selectbox("State", [
            "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
            "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka",
            "Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram",
            "Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana",
            "Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Delhi","Other"
        ])
        pep_status    = st.checkbox("Politically Exposed Person (PEP)?")
        existing_cust = st.checkbox("Existing Customer?")

        st.markdown("#### 📎 Document Upload (Simulation)")
        uploaded_id   = st.file_uploader("Upload ID Document (PDF/Image)", type=["pdf","png","jpg","jpeg"])
        uploaded_self = st.file_uploader("Upload Selfie Photo", type=["png","jpg","jpeg"])

    st.markdown("---")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        run_btn = st.button("🚀 Run KYC Verification", type="primary", use_container_width=True)
    with col_btn2:
        demo_btn = st.button("🎭 Load Demo Data", use_container_width=True)

    if demo_btn:
        st.session_state["demo_loaded"] = True
        st.rerun()

    if st.session_state.get("demo_loaded"):
        st.info("✅ Demo data loaded — click **Run KYC Verification** to proceed.")

    # Resolve customer data
    customer_data = None
    if run_btn or st.session_state.get("run_triggered"):
        if st.session_state.get("demo_loaded"):
            customer_data = get_demo_data(product_type)
        elif full_name and address and doc_number:
            # Save uploaded files temporarily
            doc_file_path = None
            selfie_file_path = None
            
            if uploaded_id:
                safe_doc_type = doc_type.lower().replace(" ", "_")
                doc_file_path = save_uploaded_file(uploaded_id, safe_doc_type)
            
            if uploaded_self:
                selfie_file_path = save_uploaded_file(uploaded_self, "selfie")
            
            customer_data = {
                "full_name":    full_name,
                "dob":          str(dob),
                "gender":       gender,
                "nationality":  nationality,
                "address":      address,
                "state":        state,
                "annual_income": annual_income,
                "employment":   employment,
                "credit_score": credit_score,
                "doc_type":     doc_type,
                "doc_number":   doc_number,
                "doc_expiry":   str(doc_expiry) if doc_expiry else "N/A",
                "pep_status":   pep_status,
                "existing_customer": existing_cust,
                "product_type": product_type,
                "has_id_doc":   uploaded_id is not None,
                "has_selfie":   uploaded_self is not None,
                "doc_file_path": doc_file_path,
                "aadhar_file_path": doc_file_path,
                "selfie_file_path": selfie_file_path,
            }
        else:
            st.error("⚠️ Please fill in all required fields (marked with *).")

    if customer_data:
        st.session_state["run_triggered"] = False
        st.session_state["demo_loaded"]   = False

        api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)

        if not api_key or api_key == "gsk_your_api_key_here":
            st.error("🔑 Groq API key is missing in backend config (app.py).")
            return

        st.markdown("---")
        st.subheader("🤖 Agent Pipeline Execution")
        run_agentic_pipeline(customer_data, api_key, GROQ_MODEL)


def run_agentic_pipeline(customer_data: dict, api_key: str, model: str):
    orchestrator = KYCOrchestrator(api_key=api_key, model=model)

    steps = [
        ("🔎 Document Extraction Agent",     "Extracting & validating document data..."),
        ("🛡️ Authenticity Verification Agent","Checking document authenticity & tampering..."),
        ("🤳 Face Match Agent",              "Performing biometric face match..."),
        ("✅ Eligibility Check Agent",        "Evaluating eligibility rules..."),
        ("⚠️ Fraud & Sanctions Agent",        "Screening fraud & sanctions databases..."),
        ("🧠 Decision Agent",                 "Generating final decision & reasoning..."),
        ("📝 Audit Logger Agent",             "Saving audit trail & compliance record..."),
    ]

    placeholders = []
    for label, _ in steps:
        ph = st.empty()
        ph.markdown(f"⏳ `{label}` — waiting...")
        placeholders.append(ph)

    result = orchestrator.run(customer_data, steps, placeholders)

    # ─── Results ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Verification Results")

    decision = result.get("final_decision", "REFER")
    col1, col2, col3 = st.columns(3)

    with col1:
        css_class = {"APPROVE": "status-approve", "REJECT": "status-reject"}.get(decision, "status-refer")
        icon      = {"APPROVE": "✅", "REJECT": "❌"}.get(decision, "⚠️")
        st.markdown(f"**Final Decision**")
        st.markdown(f'<span class="{css_class}">{icon} {decision}</span>', unsafe_allow_html=True)

    with col2:
        score = result.get("confidence_score", 0)
        st.metric("Confidence Score", f"{score:.1f}%")

    with col3:
        st.metric("Processing Time", result.get("processing_time", "N/A"))

    # Agent Results
    with st.expander("🤖 Agent-by-Agent Results", expanded=True):
        for agent_name, agent_result in result.get("agent_results", {}).items():
            st.markdown(f"**{agent_name}**")
            if isinstance(agent_result, dict):
                for k, v in agent_result.items():
                    st.markdown(f"- **{k}**: {v}")
            else:
                st.markdown(str(agent_result))
            st.markdown("---")

    # Reasoning
    with st.expander("🧠 AI Reasoning & Explanation"):
        st.markdown(result.get("reasoning", "No reasoning available."))

    # Risk Factors
    risk_factors = result.get("risk_factors", [])
    if risk_factors:
        with st.expander("⚠️ Risk Factors Identified"):
            for rf in risk_factors:
                st.warning(rf)

    # Audit Log
    with st.expander("📋 Audit Log (Compliance Record)"):
        audit = result.get("audit_log", {})
        st.markdown(f'<div class="audit-box">{json.dumps(audit, indent=2)}</div>', unsafe_allow_html=True)

    # Save to history
    if "history" not in st.session_state:
        st.session_state["history"] = []
    st.session_state["history"].insert(0, {
        "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer":   customer_data.get("full_name", "Unknown"),
        "product":    customer_data.get("product_type", "N/A"),
        "decision":   decision,
        "confidence": result.get("confidence_score", 0),
    })


def save_uploaded_file(uploaded_file, file_type: str) -> str:
    """
    Save uploaded file to temporary directory and return the path.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        file_type: Type of file ("aadhar" or "selfie")
    
    Returns:
        Path to the saved file
    """
    try:
        # Create temp directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        kyc_temp_dir = os.path.join(temp_dir, "kyc_uploads")
        os.makedirs(kyc_temp_dir, exist_ok=True)
        
        # Generate filename with timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"{file_type}_{timestamp}{file_ext}"
        file_path = os.path.join(kyc_temp_dir, filename)
        
        # Save the file
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path
    except Exception as e:
        st.error(f"Error saving uploaded file: {str(e)}")
        return None


def get_demo_data(product_type: str) -> dict:
    return {
        "full_name":    "Priya Mehta",
        "dob":          "1992-07-14",
        "gender":       "Female",
        "nationality":  "Indian",
        "address":      "42, Koramangala 4th Block, Bengaluru, Karnataka - 560034",
        "state":        "Karnataka",
        "annual_income": 850000,
        "employment":   "Salaried",
        "credit_score": 748,
        "doc_type":     "Aadhaar Card",
        "doc_number":   "2345 6789 0123",
        "doc_expiry":   "N/A",
        "pep_status":   False,
        "existing_customer": False,
        "product_type": product_type,
        "has_id_doc":   True,
        "has_selfie":   True,
    }


if __name__ == "__main__":
    main()
