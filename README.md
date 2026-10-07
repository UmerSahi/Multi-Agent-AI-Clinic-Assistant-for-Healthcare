# 🏥 City Care Clinics — Multi-Agent AI Clinic Assistant

> **A production-ready, safety-critical Multi-Agent clinical assistant built with LangGraph, Model Context Protocol (MCP), and Supabase.**
> Designed for Pakistani outpatient clinics handling high patient volumes across 5 branches in Lahore and Islamabad with 30 doctors across 6 specialties. The system automates patient intake in natural UrduLish, screens for emergency red flags (Rescue 1122), routes to specialists, drafts clinical SOAP notes, and cross-checks prescriptions for drug interactions—keeping a licensed doctor in full control at every critical juncture.

---

## 📌 Project Overview & Scenario

* **Client:** City Care Clinics (5 outpatient clinics in Lahore & Islamabad)
* **Specialties:** General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, ENT (30 Doctors)
* **Key Challenges Solved:**
  * Front-desk communication overload across WhatsApp and phone calls.
  * Patient misrouting to incorrect medical specialties.
  * Lengthy pre-consultation history taking by physicians.
  * Dangerous prescription clashes (drug-drug interactions, patient allergies, dose limits).
  * Missed follow-ups and unmonitored recovery.

---

## 🏗️ Technical Architecture & Stack

| Area | Technologies & Frameworks |
| :--- | :--- |
| **Multi-Agent Orchestration** | **LangGraph** (Supervisor StateGraph pattern, Shared `ClinicalState`, HITL interrupts) |
| **Database & Persistence** | **Supabase (PostgreSQL)** (FHIR-aligned schema, Row-Level Security, audit trails) |
| **Tool Protocol** | **Model Context Protocol (MCP)** (Decoupled servers for EHR, Scheduling, Drug DB, Lab Vision) |
| **Language Understanding** | **Bilingual UrduLish** (Natural Roman Urdu + English conversational code-switching) |
| **Privacy & Compliance** | **Microsoft Presidio** (Custom regex & NLP recognizers for Pakistani CNIC & phone numbers) |
| **Safety & Medical Guardrails** | Deterministic 1122 emergency escalation, zero autonomous prescribing/diagnosing |
| **Knowledge & RAG** | Vector knowledge base (pgvector / ChromaDB) for clinic FAQs & 100+ Pakistani drug formulations |
| **Application Interface** | FastAPI backend + Chat interface |

---

## 🧭 Multi-Agent Team

```
                               ┌────────────────────────────────┐
                               │   Patient / Doctor (Chat UI)   │
                               │   (UrduLish & English Support) │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │       Supervisor Agent         │
                               │  (Intent Routing & Gatekeeper) │
                               └───────┬───────────────┬────────┘
                                       │               │
        ┌──────────────────────────────┼───────────────┼──────────────────────────────┐
        ▼                              ▼               ▼                              ▼
┌───────────────┐              ┌───────────────┐ ┌───────────────┐            ┌───────────────┐
│ 1. Intake     │              │ 2. Triage     │ │ 3. Scheduling │            │ 4. Records    │
│ • Structured  │              │ • Red Flags   │ │ • 6 Specs     │            │ • Past visits │
│   UrduLish    │              │ • 1122 Alert  │ │ • 5 Branches  │            │ • Lab reports │
└───────┬───────┘              └───────┬───────┘ └───────┬───────┘            └───────┬───────┘
        │                              │               │                              │
        └──────────────────────────────┼───────────────┼──────────────────────────────┘
                                       │               │
        ┌──────────────────────────────┴───────────────┴──────────────────────────────┐
        ▼                                                                             ▼
┌───────────────────────────────┐                                     ┌───────────────────────────────┐
│   5. Clinical Summary Agent   │                                     │ 6. Prescription Safety Agent  │
│  • Automated SOAP Notes       │                                     │  • Pakistani Drug Clashes     │
│  • Pre-visit Doctor Briefing  │                                     │  • Allergies & Dose Limits    │
└───────────────┬───────────────┘                                     └───────────────┬───────────────┘
                │                                                                     │
                └──────────────────────────────┬──────────────────────────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │  Human-In-The-Loop (HITL Gate) │
                               │   (Doctor Review & Approval)   │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │       7. Follow-up Agent       │
                               │  • Medicine / Lab Reminders    │
                               │  • Recovery Check-ins          │
                               └────────────────────────────────┘
```

---

## 📅 Project Roadmap & Daily Modules

### [Day 1: Architecture, Safety Design & Agent Roles](file:///c:/Users/PMYLS/Downloads/AI%20Clinic%20Assistant%20for%20Healthcare/Day%201) ✅
* **[01_multi_agent_architecture.md](file:///c:/Users/PMYLS/Downloads/AI%20Clinic%20Assistant%20for%20Healthcare/Day%201/01_multi_agent_architecture.md):** Architectural patterns (Supervisor vs. Swarm vs. Hierarchical), Shared State vs. Message Passing, MCP design, HITL review/edit/approve flows, and full system diagram.
* **[02_agent_role_cards.md](file:///c:/Users/PMYLS/Downloads/AI%20Clinic%20Assistant%20for%20Healthcare/Day%201/02_agent_role_cards.md):** Formal role cards for all 8 agents (Goals, Inputs/Outputs, Permitted Tools, Negative Constraints, Handoff rules).
* **[03_patient_conversation_flows.md](file:///c:/Users/PMYLS/Downloads/AI%20Clinic%20Assistant%20for%20Healthcare/Day%201/03_patient_conversation_flows.md):** 7 end-to-end conversation flows with Mermaid sequence diagrams and authentic UrduLish scripts (Routine Fever/Cough, Chest Pain 1122 Escalation, Pediatrics, Lab Review, Rescheduling, Medication Clashes, Post-Visit Follow-Up).
* **[04_safety_and_triage_policy.md](file:///c:/Users/PMYLS/Downloads/AI%20Clinic%20Assistant%20for%20Healthcare/Day%201/04_safety_and_triage_policy.md):** 8-domain red-flag taxonomy, Emergency/Urgent/Routine SLA matrix, exact UrduLish escalation messages, AI vs. Doctor boundary matrix, and statutory disclaimers.
* **[05_privacy_compliance_and_prompts.md](file:///c:/Users/PMYLS/Downloads/AI%20Clinic%20Assistant%20for%20Healthcare/Day%201/05_privacy_compliance_and_prompts.md):** PII/PHI definitions, Microsoft Presidio anonymization pipeline for Pakistani CNIC & phone numbers, Supabase RBAC matrix, immutable audit log schemas, patient consent banner, and complete UrduLish system prompts.

### Day 2: Database Schema, Synthetic Data & Knowledge Layer ⏳
* Supabase PostgreSQL FHIR-aligned schema setup (Patients, Doctors, Clinics, Encounters, Observations, Prescriptions, Audit Logs).
* 500+ synthetic Pakistani patient records, 30 doctors, 5 clinic branches, and 100+ Pakistani drug formulations.
* Vector knowledge base indexing (ChromaDB / pgvector).

### Day 3: LangGraph Core Engine & Worker Agents ⏳
* Supervisor router graph implementation.
* Intake, Triage, Scheduling, and Records agents with tool integration.
* Dynamic UrduLish conversational memory and state management.

### Day 4: Clinical Summary, Prescription Safety & HITL Gates ⏳
* Automated SOAP note generation for attending doctors.
* Drug-drug interaction and allergy screening engine.
* Doctor review, edit, and approve interface with LangGraph interrupts.

### Day 5: Evaluation, Guardrails, Docker & Deployment ⏳
* Safety red-teaming, DeepEval / Ragas evaluation pipelines.
* End-to-end conversational chat testing.
* Containerization (Docker) and deployment readiness.

---

## 🔒 Safety & Ethical Mandate

> ⚠️ **Strict Safety Rule:** The AI must **never diagnose a disease or prescribe medication on its own**. It gathers structured information, screens for danger signs, drafts clinical summaries, and flags potential medication clashes. Every emergency symptom immediately triggers an escalation to **Rescue 1122 / Nearest Emergency Ward**. All clinical guidance requires licensed physician authorization. All data used is **100% synthetic**.
