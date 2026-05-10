# 🔍 AI Eligibility & KYC Checker

An **enterprise-grade, agentic KYC verification system** powered by **Groq LLM API** with a Streamlit UI.

This application includes:
- **Microsoft Agentic Framework compatibility** via a runtime adapter aligned to Semantic Kernel patterns.
- **Autonomous tool-driven actions** (format validation, action logging, and automatic manual-review ticket creation on critical mismatches).

## Architecture

```
Customer Submission
       │
       ▼
┌─────────────────────┐
│  KYC Orchestrator   │  ← coordinates all agents with enterprise runtime controls
└─────────────────────┘
       │
       ├── Agent 1: Document Extraction Agent
       │       Extracts & validates ID fields
       │
       ├── Agent 2: Authenticity Verification Agent
       │       Checks document genuineness & format
       │
       ├── Agent 3: Face Match Agent
       │       Biometric selfie vs ID photo comparison
       │
       ├── Agent 4: Eligibility Rules Agent
       │       Age, income, credit score, geography checks
       │
       ├── Agent 5: Fraud & Sanctions Agent
       │       Watchlist screening, PEP, adverse media
       │
       ├── Agent 6: Decision Agent
       │       Synthesises all results → APPROVE / REJECT / REFER
       │
              └── Agent 7: Audit Logger Agent
                     Compliance audit trail (RBI/SEBI standards)

       Microsoft Runtime Layer
              │
              ├── Correlation ID propagation
              ├── Retry policy for agent invocation
              ├── Framework metadata (Semantic Kernel/local fallback)
              └── Enterprise execution envelope
```

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get a free Groq API key
Visit [console.groq.com](https://console.groq.com) → sign up → create an API key.

### 3. Run the app
```bash
streamlit run app.py
```

### 4. Enter your API key in the sidebar and start verifying!

## Features

- **7 specialist AI agents** running in sequence
- **Microsoft Agentic Framework runtime adapter** for enterprise integration
- **Autonomous agent actions** using dedicated tools
- **Enterprise controls**: correlation IDs, retries, structured audit trail
- **Real-time agent progress** with live status updates
- **Full audit trail** with compliance-grade logging
- **Session analytics dashboard**
- **Demo mode** — try instantly without filling the form
- **Multiple Groq models** supported (LLaMA 3, Mixtral, Gemma)
- **Products supported**: Personal Loan, Home Loan, Credit Card, Savings Account, Fixed Deposit, Business Loan, Insurance

## Project Structure

```
kyc_checker/
├── app.py                      # Streamlit entry point
├── requirements.txt
├── agents/
│   ├── orchestrator.py         # Pipeline coordinator
│   ├── base_agent.py           # Abstract base class
│   ├── document_agent.py       # Agent 1
│   ├── authenticity_agent.py   # Agent 2
│   ├── face_match_agent.py     # Agent 3
│   ├── eligibility_agent.py    # Agent 4
│   ├── fraud_agent.py          # Agent 5
│   ├── decision_agent.py       # Agent 6
│   └── audit_agent.py          # Agent 7
├── utils/
│   ├── groq_client.py          # Groq API wrapper
│   ├── microsoft_agentic_runtime.py  # Microsoft framework runtime adapter
│   ├── agent_tools.py          # Autonomous tool actions
│   └── session_manager.py      # Streamlit session helpers
└── ui/
    ├── sidebar.py              # Config sidebar
    ├── dashboard.py            # Analytics tab
    └── history.py              # History tab
```

## Supported Documents (India)
- Aadhaar Card
- PAN Card
- Passport
- Driving License
- Voter ID

## Decision Outcomes
| Decision | Meaning |
|----------|---------|
| ✅ APPROVE | All checks passed — auto-approved |
| ❌ REJECT | Critical failure — document fake, sanctions hit, or clearly ineligible |
| ⚠️ REFER | Uncertain or minor mismatch — refer to human reviewer |
