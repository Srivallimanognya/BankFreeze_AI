git add README.md
# BankFreeze AI

BankFreeze AI is an Agentic AI-powered bank account freeze investigation, multi-source reconciliation, and resolution support system. It helps users investigate and understand why a bank account hold or freeze occurred, reconciles bank records with notice documents and authority information, generates factual inquiry representations, and tracks resolution progress.

---

## Project Overview

When a bank account is placed under restriction (due to cybercell complaints, disputed transactions, periodic KYC lapses, or statutory orders), account holders often lack clear, actionable details. BankFreeze AI provides an end-to-end investigation dashboard:

1. **Select / Ingest Case**: Select pre-configured synthetic demo cases or create new records.
2. **Multi-Source Reconciliation**: Cross-checks facts across customer statements, uploaded documents, mock bank core adapters, and law-enforcement registries.
3. **AI Investigation & Risk Assessment**: Analyzes knowns, unknowns, matching facts, and conflicts, producing procedural next steps.
4. **Action Plan & Communication**: Formulates tailored factual inquiry drafts and escalation paths with mandatory human review guardrails.
5. **n8n Agentic Orchestration**: Triggers backend investigation workflows and presents structured findings directly inside the dashboard.

---

## Main Features

- **Interactive Investigation Dashboard**: Real-time status cards, restriction badges, and operational summaries.
- **Dynamic Case Selection**: Switch between demo cases with zero state cross-contamination.
- **Multi-Source Reconciliation Engine**: Automated comparison across user intake, document extractions, bank notices, and authority registries to detect matches, partials, and critical mismatches.
- **n8n Workflow Integration**: Triggers automated agentic investigation workflows via webhook and receives structured JSON investigation results.
- **Local Fallback Synthesizer**: Fully functional in offline demo mode even when external webhook services are unreachable.
- **Document Analysis & OCR Extraction**: Analyzes uploaded notices to extract reference numbers, disputed amounts, and authority contacts.
- **Escalation & Resolution Matrix**: Tiered escalation guidance (Branch Manager ➔ Nodal Officer ➔ Principal Nodal / Banking Ombudsman).
- **Audit Logging & Compliance Guardrails**: Tracks every investigation action with immutable audit trails. Strict account masking and prohibited credential safeguards.

---

## Technology Stack

- **Python** (Core application logic & analysis engine)
- **Streamlit** (Frontend user interface & interactive dashboard)
- **SQLite** (Relational case storage & audit trails)
- **SQLAlchemy** (ORM models and database session management)
- **n8n** (Agentic workflow orchestration & webhook execution)
- **Pydantic** (Data validation schemas and extraction models)
- **HTTPX** (Asynchronous and synchronous HTTP client for webhook communication)
- **Pytest** (Automated unit and integration test suite)
- **bcrypt** (Password hashing and security)
- **Pillow** (Image processing for document previews)
- **pypdf** (PDF notice parsing and text extraction)
- **python-dotenv** (Environment variable loading)

---

## Project Structure

```
BankFreeze_AI_Deploy/
├── .env.example              # Configuration template with placeholders (no secrets)
├── .gitignore                # Git ignore rules for virtualenvs, caches, and secrets
├── .streamlit/
│   └── config.toml           # Streamlit server deployment configuration
├── README.md                 # Project documentation and deployment guide
├── app.py                    # Main Streamlit application entry point
├── bankfreeze.db             # Local SQLite database (seeded demo records)
├── requirements.txt          # Python package dependencies
│
├── config/
│   ├── __init__.py
│   └── settings.py           # Application settings and environment resolution
├── database/
│   ├── __init__.py
│   ├── connection.py         # SQLite engine and session factory
│   └── models.py             # SQLAlchemy ORM models (Cases, Documents, Logs)
├── demo/
│   ├── __init__.py
│   ├── seed_data.py          # Synthetic demo cases generator
│   └── sample_documents/     # Realistic mock notices and orders
├── modules/
│   ├── audit.py              # Audit logging helper
│   ├── authority_adapter.py  # Mock law-enforcement and authority adapter
│   ├── bank_adapter.py       # Mock bank core system adapter
│   ├── communication_generator.py # Factual inquiry draft generator
│   ├── document_analyzer.py  # Document fact extractor
│   ├── escalation.py         # Tiered grievance escalation engine
│   ├── freeze_analyzer.py    # Freeze category classifier
│   ├── llm_service.py        # LLM interface with deterministic fallback
│   ├── reconciliation.py     # Multi-source cross-referencing engine
│   ├── resolution_agent.py   # Agentic reasoning synthesizer
│   ├── security.py           # Masking, hashing, and credential sanitization
│   └── workflow_client.py    # n8n webhook dispatcher & fallback synthesizer
├── n8n/
│   └── BankFreeze_AI_Final_Workflow.json # Complete n8n workflow definition
├── schemas/
│   ├── case.py               # Case enums and validation schemas
│   ├── extraction.py         # Document extraction schemas
│   └── reconciliation.py     # Reconciliation status schemas
├── tests/
│   ├── test_agent_decisions.py
│   ├── test_case_lifecycle.py
│   ├── test_communication_generator.py
│   ├── test_database.py
│   ├── test_document_extraction.py
│   ├── test_freeze_classification.py
│   ├── test_reconciliation.py
│   ├── test_security.py
│   └── test_workflow_integration.py # End-to-end integration tests
└── ui/
    ├── components.py         # Reusable Streamlit widgets and banners
    └── views/                # Individual application view pages
        ├── ai_analysis.py
        ├── audit_log_view.py
        ├── authority_info.py
        ├── case_details.py
        ├── communications.py
        ├── create_case.py
        ├── dashboard.py
        ├── documents.py
        ├── escalation_view.py
        ├── reconciliation_view.py
        ├── resolution_plan.py
        ├── settings_view.py
        ├── transactions.py
        └── workflow_view.py  # Full n8n investigation dashboard
```

---

## Run Locally

### 1. Clone or Open the Repository
```bash
cd BankFreeze_AI_Deploy
```

### 2. Create and Activate a Virtual Environment
**On Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)
Copy the template to create a local `.env`:
```bash
copy .env.example .env   # Windows
# or: cp .env.example .env  # Linux/macOS
```
*(Leave `N8N_WEBHOOK_URL` empty to run in offline demo mode, or add your webhook URL).*

### 5. Start the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Environment Variables

The application can be configured via environment variables or a local `.env` file:

```ini
APP_NAME=BankFreeze AI
APP_ENV=development
SECRET_KEY=demo-secret-key-change-in-production-bankfreeze-2025
DATABASE_URL=sqlite:///bankfreeze.db
DEMO_MODE=True
MASK_ACCOUNT_NUMBERS=True
ENFORCE_STRICT_SAFEGUARDS=True

# n8n Webhook Integration (Optional for live execution)
N8N_WEBHOOK_URL=YOUR_N8N_WEBHOOK_URL
N8N_TIMEOUT_SECONDS=30
```

> **IMPORTANT**: Never commit the actual `.env` file containing secrets or URLs to GitHub. `.env` is listed in `.gitignore` and `.env.example` should be used as a template.

---

## GitHub Upload

To push this deployment-ready project to your GitHub repository:

```bash
git init
git add .
git commit -m "Initial BankFreeze AI project"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

---

## Streamlit Community Cloud Deployment

To deploy on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. **Create a GitHub Repository**: Push this project folder to your GitHub account.
2. **Log into Streamlit Community Cloud**: Connect your GitHub account.
3. **Create New App**:
   - **Repository**: Select `YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **Configure Secrets** (Optional for live n8n workflow):
   - In App Settings ➔ **Secrets**, add:
     ```toml
     N8N_WEBHOOK_URL = "YOUR_N8N_WEBHOOK_URL"
     ```
5. **Deploy**: Click **Deploy**. Streamlit Cloud will install dependencies from `requirements.txt` and launch the app.

---

## n8n Requirement

BankFreeze AI supports both local/offline execution and cloud workflow orchestration:

### Local Development Flow:
```
Streamlit App (Local) ──> Local n8n Webhook or Local Agentic Synthesizer ──> Structured Result
```

### Deployed Cloud Flow:
```
Streamlit Community Cloud ──[HTTPS]──> Public n8n Webhook / n8n Cloud ──> Existing n8n Workflow ──> Return Structured Result
```

> **Note on Deployed Webhooks**: A Streamlit application deployed on the public internet cannot access `localhost:5678` on your personal machine. When deployed on Streamlit Cloud, `N8N_WEBHOOK_URL` must point to a publicly reachable HTTPS endpoint (such as n8n Cloud or an n8n instance hosted with a public domain/tunnel).  
> If `N8N_WEBHOOK_URL` is blank or unreachable, BankFreeze AI automatically uses its built-in local agentic synthesizer so the entire dashboard remains fully functional.

---

## Safety / Demo Note

- **Prototype & Demonstration**: This system is a functional prototype built for educational and demonstration purposes using synthetic mock data.
- **No Real Banking Connections**: It does not connect to live core banking APIs, SWIFT, NEFT/RTGS settlement networks, or police/law-enforcement intranets.
- **Zero Credential Transmission**: The system strictly prohibits collecting, transmitting, or storing sensitive authentication credentials (PINs, passwords, OTPs, CVVs, or full account numbers).
- **NO AUTOMATIC UNFREEZE**: BankFreeze AI never claims an account has been or will be automatically unfrozen, and performs no automated fund/account unfreeze actions. All outputs are advisory factual representations requiring explicit human compliance review.
- **SQLite Persistence on Streamlit Cloud**: Streamlit Community Cloud operates with an ephemeral filesystem. Any changes made to the SQLite database during a session on Streamlit Cloud will reset when the app container restarts. For a production deployment, connect a persistent external SQL database via `DATABASE_URL`.
