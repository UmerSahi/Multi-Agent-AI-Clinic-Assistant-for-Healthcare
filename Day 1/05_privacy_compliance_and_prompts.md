# Task 5: Privacy, Compliance & Prompt Design

This document details the data privacy safeguards, Microsoft Presidio redaction pipelines, Role-Based Access Control (RBAC), immutable audit logging schemas, patient consent policies, and production system prompts for City Care Clinics.

---

## 1. Sensitive Data Classification (PII / PHI)

In compliance with international healthcare standards (HIPAA/GDPR) and Pakistani legal protections (PECA 2016 / Personal Data Protection regulations), patient data is categorized into three strict security tiers:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DATA CLASSIFICATION MATRIX                                      │
├───────────────────┬───────────────────────────────────┬────────────────────────────────┤
│ Category          │ Data Attributes                   │ Storage & Processing Rules     │
├───────────────────┼───────────────────────────────────┼────────────────────────────────┤
│ 1. Direct PII     │ • Full Name (e.g., Muhammad Tariq)│ Must be REDACTED via Presidio  │
│    (Personally    │ • Pakistani CNIC (XXXXX-XXXXXXX-X)│ before reaching LLM API. Stored│
│     Identifiable) │ • Mobile Phone (+92-3XX-XXXXXXX)  │ encrypted at rest (AES-256) in │
│                   │ • Home Address, Email             │ Supabase Vault.                │
├───────────────────┼───────────────────────────────────┼────────────────────────────────┤
│ 2. Protected PHI  │ • Chief Complaints & Symptoms     │ LLM sees anonymized pseudonyms │
│    (Health        │ • Diagnoses, Past Surgeries       │ (`<PATIENT_492>`). Encrypted in│
│     Information)  │ • Lab Reports & Biomarkers        │ FHIR Observation/Condition     │
│                   │ • Active Medication & Allergies   │ tables with RLS.               │
├───────────────────┼───────────────────────────────────┼────────────────────────────────┤
│ 3. Operational    │ • Clinic Branch, Doctor ID        │ Public / unmasked operational  │
│    Metadata       │ • Appointment Slots, Timestamps   │ data. Standard indexing.       │
└───────────────────┴───────────────────────────────────┴────────────────────────────────┘
```

---

## 2. Microsoft Presidio PII Redaction Pipeline

Before any raw patient chat or document text is passed to LLM context windows (OpenAI, Claude, or Gemini), it passes through an inline **Presidio Anonymization Layer** equipped with custom Pakistani entity recognizers.

```
[Raw User Input] 
       │
       ▼
[Presidio Analyzer Engine]
   ├── Custom Pattern: Pakistani CNIC Regex `\b\d{5}-\d{7}-\d{1}\b`
   ├── Custom Pattern: Pakistani Phone Regex `\b(?:\+92|0092|0)?3\d{2}[- ]?\d{7}\b`
   ├── Spacy NLP: PERSON, LOCATION, DATE_TIME
       │
       ▼
[Presidio Anonymizer Engine] ──► Replaces with Tokens: `<CNIC_1>`, `<PHONE_1>`, `<PERSON_1>`
       │
       ▼
[Anonymized Payload sent to LLM]
       │
       ▼
[Response received from LLM]
       │
       ▼
[De-anonymizer Engine] ──► Re-injects real values in client UI session ONLY
```

### Python Implementation Blueprint (Presidio Custom Recognizer)
```python
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# 1. Custom Pakistani CNIC Pattern (e.g. 35202-1234567-1)
cnic_pattern = Pattern(
    name="pk_cnic_pattern",
    regex=r"\b\d{5}-\d{7}-\d{1}\b",
    score=0.95
)
cnic_recognizer = PatternRecognizer(
    supported_entity="PK_CNIC",
    patterns=[cnic_pattern]
)

# 2. Custom Pakistani Mobile Number Pattern (e.g. +92 300 1234567, 0321-7654321)
phone_pattern = Pattern(
    name="pk_phone_pattern",
    regex=r"\b(?:\+92|0092|0)?3\d{2}[- ]?\d{7}\b",
    score=0.90
)
phone_recognizer = PatternRecognizer(
    supported_entity="PK_PHONE",
    patterns=[phone_pattern]
)

analyzer = AnalyzerEngine()
analyzer.registry.add_recognizer(cnic_recognizer)
analyzer.registry.add_recognizer(phone_recognizer)
anonymizer = AnonymizerEngine()

def scrub_pii(text: str) -> tuple[str, dict]:
    results = analyzer.analyze(text=text, entities=["PK_CNIC", "PK_PHONE", "PERSON"], language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text, results
```

---

## 3. Role-Based Access Control (RBAC) Matrix

To ensure principle of least privilege, database roles in Supabase are segregated:

| Resource / Capability | Patient | Receptionist | Attending Doctor | Clinic Admin |
| :--- | :---: | :---: | :---: | :---: |
| View Own Profile & Appointments | ✅ | ❌ | ❌ | ❌ |
| View Clinic Doctors & Available Slots | ✅ | ✅ | ✅ | ✅ |
| Book / Reschedule / Cancel Slots | ✅ | ✅ | ❌ | ✅ |
| View Patient Demographics & Phone | Self only | ✅ (Front Desk) | ✅ | ✅ |
| **View Clinical Symptoms & SOAP Notes** | ❌ (Private) | ❌ **FORBIDDEN** | ✅ Full Access | ❌ **FORBIDDEN** |
| **Write / Edit Diagnoses & Prescriptions** | ❌ **FORBIDDEN** | ❌ **FORBIDDEN** | ✅ Full Authority| ❌ **FORBIDDEN** |
| View Raw Audit Logs & Security Metrics | ❌ | ❌ | ❌ | ✅ Full Access |

---

## 4. Immutable Audit Log Specification

Every query, tool execution, and clinical access generates an append-only log in the Supabase `audit_logs` table.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_id TEXT NOT NULL,
    actor_role TEXT NOT NULL CHECK (actor_role IN ('PATIENT', 'RECEPTIONIST', 'DOCTOR', 'SYSTEM_AGENT')),
    patient_id TEXT,
    action_type TEXT NOT NULL, -- 'VIEW_LAB_REPORT', 'DISPATCH_HITL_SOAP', 'CALL_MCP_TOOL'
    resource_accessed TEXT NOT NULL,
    tool_name TEXT,
    ip_address INET,
    change_payload JSONB,
    emergency_flag BOOLEAN DEFAULT FALSE
);
```

---

## 5. Patient Consent & Data Retention Policy

### Data Retention Standard
* Active patient records are retained for **7 years** in accordance with medical-legal best practices.
* Ephemeral chat session transcripts without associated appointments are scrubbed after **30 days**.
* Patients retain the right to request full export or deletion of uncommitted chat inquiries.

### Initial Consent Banner (Displayed in UrduLish upon Session Start)
```
📋 KHUSUSI MALOOMAT AUR RAZDARI (PRIVACY NOTICE):

City Care Clinics mein aap ki sehat aur razdari hamari pehli tarjeeh hai.

1. Razdari (Privacy): Aap ka data mehfooz (encrypted) hai aur kisi teesri party ko nahi becha jata.
2. AI Sahulat: Yeh chat assistant doctor ki madad aur appointment ke liye hai; yeh khud ilaaj ya dawai tajweez nahi karta.
3. Doctor Review: Aap ki batai hui alamaat sirf aap ke muallij doctor ko consultation ke waqt dikhayi jati hain.

Is chat ko aage barha kar aap hamari Privacy Policy aur Terms of Care se ittifaq karte hain.
```

---

## 6. Patient-Facing Agent Persona & System Prompt

### Persona Definition
* **Name:** *Ayesha* — City Care Clinics Care Coordinator
* **Tone:** Warm, empathetic, polite (*adab aur ehtiram*), culturally authentic Pakistani UrduLish (*"Aap"*, *"Janab"*, *"InshaAllah"*, *"Allah sehat de"*).
* **Clinical Demeanor:** Serious, calm, and reassuring. Never dismissive or casual about pain; never alarmist or panic-inducing.
* **Language Strategy:** Fluent UrduLish (Roman Urdu with standard English clinical terms like *appointment*, *fever*, *prescription*, *specialist*, *branch*).

### Complete Production System Prompt
```markdown
You are Ayesha, the virtual Care Coordinator for City Care Clinics in Lahore and Islamabad.
Your mission is to welcome patients, understand their health concerns with utmost respect and empathy, collect structured symptom details, and guide them to the right care.

### CORE OPERATIONAL BOUNDARIES (NON-NEGOTIABLE):
1. NEVER DIAGNOSE: You are strictly forbidden from diagnosing diseases or speculating on conditions. Never say "Aap ko typhoid/dengue lagta hai".
2. NEVER PRESCRIBE: You must never recommend any medicine, dosage, or home remedies (no antibiotics, painkillers, or herbal concoctions).
3. RED-FLAG SENSITIVITY: If the patient mentions chest pain, severe breathlessness, stroke signs (mouth drooping, slurred speech), heavy bleeding, or a sick infant under 3 months, you must IMMEDIATELY trigger the 1122 emergency escalation message.
4. LANGUAGE: Communicate in natural, warm, grammatically correct UrduLish (Roman Urdu blended with common English medical terms). Always address the patient respectfully using "Aap".
5. CONCISE & FOCUSED: Keep responses under 3-4 sentences. Ask only one or two focused questions at a time to avoid overwhelming the patient.

### CONVERSATIONAL STYLE EXAMPLES:
- Greeting: "Assalam o Alaikum! City Care Clinics mein khushamdeed. Main Ayesha hoon. Aaj hum aap ki kis tarah madad kar sakte hain?"
- Empathy: "Yeh sun kar afsos hua ke aap ki tabiyat theek nahi hai. InshaAllah hum behtar rehnumai karenge."
- Clarification: "Yeh batayein ke bukhar kitne din se hai, aur kya saans lene mein koi dushwari toh nahi ho rahi?"
- Closing: "Aap ki appointment Dr. Usman ke sath confirm ho chuki hai. Allah aap ko kamil sehat ata farmaye!"
```
