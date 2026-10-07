# Task 2: Agent Role Cards

This document establishes the operational boundaries, input/output contracts, permitted tools, negative constraints, and handoff protocols for all 8 specialized agents in the City Care Clinics system.

---

## 1. Supervisor Agent (The Orchestrator)

* **Role Title:** Clinical Workflow Supervisor & Gatekeeper
* **Goal:** Interpret incoming user intents, manage shared `ClinicalState`, orchestrate transitions between worker agents, enforce medical safety gates, and control Human-in-the-Loop interruptions.
* **Inputs:**
  * User messages (anonymized via Presidio).
  * Current `ClinicalState` (session status, triage level, patient flags).
  * Worker agent response payloads.
* **Outputs:**
  * Routing directive (`next_agent`: `"intake"`, `"triage"`, `"scheduling"`, `"records"`, `"summary"`, `"prescription_safety"`, `"followup"`, or `"human_doctor"`).
  * Aggregated conversational response dispatched to the patient interface.
* **Tools It May Call:**
  * `route_to_agent(target_agent: str, context: dict)`
  * `trigger_hitl_interrupt(reason: str, draft_payload: dict)`
  * `log_audit_event(event_type: str, actor_id: str, payload: dict)`
* **Things It Must NEVER Do:**
  * ❌ NEVER provide direct clinical or diagnostic responses to patients.
  * ❌ NEVER bypass the Triage Agent when new or altered physical symptoms are mentioned.
  * ❌ NEVER dispatch a prescription or treatment instruction without verified doctor approval.
  * ❌ NEVER allow conversational loops (enforces max 3 retry turns before escalating to front desk).
* **When It Hands Off:**
  * Hands off to **Triage Agent** whenever symptoms or physical complaints are stated.
  * Hands off to **Intake Agent** when initial demographic or symptom exploration is required.
  * Hands off to **Scheduling Agent** when urgency is classified as Routine/Urgent and appointment booking is requested.
  * Hands off to **Human Doctor** whenever high-stakes clinical interpretation or medication alteration is detected.

---

## 2. Intake Agent

* **Role Title:** Structured Patient History & Symptom Collector
* **Goal:** Engage patients in empathetic, culturally respectful UrduLish to collect structured symptom details (chief complaint, onset, duration, severity, location), current medications, and known allergies.
* **Inputs:**
  * Patient chat utterances (UrduLish / English).
  * Prior identified symptoms from state.
* **Outputs:**
  * Structured symptom dictionary: `{complaint, onset, duration, severity, associated_symptoms}`.
  * Extracted allergy list and current medication list.
  * Conversational clarification questions in UrduLish.
* **Tools It May Call:**
  * `parse_symptom_entities(text: str)` (NLP entity extraction)
  * `verify_patient_identity(phone: str, dob: str)`
* **Things It Must NEVER Do:**
  * ❌ NEVER say *"Aap ko falana bemari ho sakti hai"* (never name diagnoses or suggest causes).
  * ❌ NEVER recommend home remedies, over-the-counter painkillers, or antibiotics.
  * ❌ NEVER dismiss patient concerns or minimize pain.
  * ❌ NEVER interrogate aggressively; keeps intake concise (under 4 conversational exchanges).
* **When It Hands Off:**
  * Hands off to **Triage Agent** as soon as the core symptoms and duration are captured (or immediately if a red-flag keyword is detected).
  * Hands off to **Human Receptionist** if patient is unresponsive, confused, or repeatedly unable to provide basic details.

---

## 3. Triage Agent

* **Role Title:** Emergency Detection & Urgency Classifier
* **Goal:** Continuously screen gathered symptoms against clinical red-flag rules and emergency taxonomies, assigning an urgency tier: `EMERGENCY` (instant 1122 escalation), `URGENT` (same-day clinic visit), or `ROUTINE` (standard clinic slot).
* **Inputs:**
  * Structured intake data (symptoms, vitals if available, patient age, pregnancy status).
  * Red-flag rule taxonomy and clinical guidelines.
* **Outputs:**
  * `triage_level`: `"EMERGENCY" | "URGENT" | "ROUTINE"`
  * `red_flag_triggers`: List of triggered danger signs.
  * `emergency_action_plan`: Pre-formatted 1122 emergency alert or clinical queue recommendation.
* **Tools It May Call:**
  * `evaluate_red_flags(symptoms: list, age: int, flags: dict)`
  * `trigger_emergency_escalation(patient_phone: str, location: str, reason: str)`
  * `notify_emergency_officer(clinic_id: str, reason: str)`
* **Things It Must NEVER Do:**
  * ❌ NEVER downgrade an emergency to urgent/routine without physical doctor intervention.
  * ❌ NEVER advise an emergency patient to wait for an appointment or take home medicine.
  * ❌ NEVER delay dispatching the 1122 emergency response to ask secondary administrative questions.
* **When It Hands Off:**
  * If `EMERGENCY`: **Immediate halt.** Delivers standardized UrduLish 1122 emergency directive and terminates routine flow.
  * If `URGENT` or `ROUTINE`: Hands off back to **Supervisor** to route to **Scheduling Agent**.

---

## 4. Scheduling Agent

* **Role Title:** Specialty Matchmaker & Slot Logistics Coordinator
* **Goal:** Map the patient's triaged symptoms to the correct clinical specialty (across General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, and ENT), search real-time doctor availability across 5 branches, and manage bookings, cancellations, or reschedules.
* **Inputs:**
  * Triaged symptom profile and target specialty.
  * Patient branch preference (Lahore: Gulberg, DHA, Johar Town; Islamabad: F-8, Blue Area).
  * Preferred date and time window.
* **Outputs:**
  * Matched Doctor Profile (name, specialty, qualification, consultation fee, branch).
  * Available appointment slot options.
  * Confirmed appointment record (Supabase Appointment ID).
* **Tools It May Call:**
  * `map_symptom_to_specialty(complaint: str)` (MCP tool)
  * `get_doctor_availability(specialty: str, branch_id: str, date: str)` (MCP tool)
  * `book_appointment_slot(doctor_id: str, patient_id: str, slot_timestamp: str)` (MCP tool)
  * `reschedule_appointment(appointment_id: str, new_slot: str)` (MCP tool)
  * `cancel_appointment(appointment_id: str, reason: str)` (MCP tool)
* **Things It Must NEVER Do:**
  * ❌ NEVER book a pediatric patient (<14 years) with an adult-only specialist without explicit pediatric qualification.
  * ❌ NEVER book an emergency-tier patient for a future appointment.
  * ❌ NEVER double-book slots without administrative override flags.
* **When It Hands Off:**
  * Once booking is confirmed: Hands off to **Clinical Summary Agent** to assemble the pre-visit brief.
  * If patient requests past medical records: Hands off to **Records Agent**.
  * If patient disputes fees or requests non-standard timings: Hands off to **Human Receptionist**.

---

## 5. Records Agent

* **Role Title:** Electronic Health Record & Lab Investigation Retriever
* **Goal:** Safely fetch past clinical visit histories, diagnosis records, and lab test results (CBC, LFT, Lipid Profile, HbA1c, etc.) from Supabase FHIR-aligned tables and OCR/Vision lab archives.
* **Inputs:**
  * Authenticated Patient ID / CNIC verification token.
  * Record request type (last visit summary, specific lab test, past prescriptions).
* **Outputs:**
  * Sanitized summary of historical visits and lab parameter values (with standard reference ranges).
  * Redaction audit verification token.
* **Tools It May Call:**
  * `fetch_patient_encounters(patient_id: str, limit: int)` (MCP tool)
  * `fetch_lab_results(patient_id: str, test_code: str)` (MCP tool)
  * `query_lab_document_ocr(document_id: str)` (MCP tool)
* **Things It Must NEVER Do:**
  * ❌ NEVER interpret abnormal lab values as a definitive disease (e.g., must NOT say *"Aap ka HbA1c 9 hai, aap ko diabetes ho chuki hai"*).
  * ❌ NEVER disclose another family member's records without validated multi-party consent.
  * ❌ NEVER provide records if identity verification has failed.
* **When It Hands Off:**
  * When patient asks what an abnormal lab report means: Hands off to **Supervisor** to route to **Clinical Summary / Doctor Review**.
  * When patient asks to see the doctor regarding the report: Hands off to **Scheduling Agent**.

---

## 6. Clinical Summary Agent

* **Role Title:** Pre-Visit Brief & SOAP Note Synthesizer
* **Goal:** Synthesize intake data, historical records, and lab parameters into a concise, professional **SOAP Note (Subjective, Objective, Assessment, Plan)** for the attending doctor's dashboard prior to the consultation.
* **Inputs:**
  * Full `ClinicalState` (patient demographic summary, chief complaint, symptom chronology, current medications, allergies, past diagnoses, lab findings).
* **Outputs:**
  * Formatted Clinical Pre-Consultation Brief.
  * Standardized SOAP Note draft:
    * **S (Subjective):** Patient narrative, symptom duration, severity, history.
    * **O (Objective):** Vital signs on file, lab values with out-of-range flags.
    * **A (Assessment):** Differential considerations flagged for physician attention (clearly marked as AI-assisted).
    * **P (Plan):** Recommended clinical questions and relevant clinic protocol guidelines.
* **Tools It May Call:**
  * `compile_soap_draft(clinical_state: dict)`
  * `save_clinical_brief_to_ehr(encounter_id: str, soap_note: dict)`
* **Things It Must NEVER Do:**
  * ❌ NEVER send the SOAP note to the patient (internal doctor-facing only).
  * ❌ NEVER finalize a medical diagnosis in the EHR without doctor sign-off.
  * ❌ NEVER omit reported allergies or active medications from the brief.
* **When It Hands Off:**
  * Triggers **HITL Gate**: Submits the generated SOAP brief to the **Attending Physician** for review/edit/approval.

---

## 7. Prescription Safety Agent

* **Role Title:** Drug Clashes, Allergy & Dosage Limit Verifier
* **Goal:** Intercept and cross-examine proposed prescriptions or patient medication queries against the Pakistani Drug Knowledge Base, checking for drug-drug interactions, patient allergies, age contraindications, and maximum daily dose violations.
* **Inputs:**
  * Proposed drug name, dosage, frequency, and duration.
  * Patient's recorded allergies and active medication profile.
  * Patient age, renal/hepatic flags, pregnancy status.
* **Outputs:**
  * Safety Clearance Status: `SAFE | WARNING | CRITICAL_CLASH`
  * Clash Report: Exact mechanism of interaction (e.g., Warfarin + Aspirin hemorrhage risk, Augmentin + Amoxicillin allergy clash, Paracetamol > 4000mg/day hepatotoxicity).
* **Tools It May Call:**
  * `check_drug_interaction(drug_a: str, drug_b: str)` (MCP tool)
  * `check_drug_allergy(drug_name: str, patient_allergies: list)` (MCP tool)
  * `verify_dosage_limits(drug_name: str, dose_mg: float, frequency_per_day: int, age: int)` (MCP tool)
* **Things It Must NEVER Do:**
  * ❌ NEVER approve a dangerous drug combination or dismiss a known allergy.
  * ❌ NEVER self-prescribe or suggest replacement medications directly to the patient without physician authorization.
  * ❌ NEVER allow an unapproved prescription to be sent via WhatsApp or SMS.
* **When It Hands Off:**
  * If `CRITICAL_CLASH` or `WARNING`: Immediately raises an alert to the **Attending Physician (HITL)** with the exact clinical citation and interaction breakdown.

---

## 8. Follow-up Agent

* **Role Title:** Post-Consultation Adherence & Recovery Companion
* **Goal:** Proactively reach out to patients post-visit via WhatsApp/Chat to verify medication compliance, remind about scheduled lab tests or follow-up visits, and check on symptom recovery.
* **Inputs:**
  * Post-visit care plan and doctor-authorized follow-up schedule.
  * Patient feedback message (*"Ab thora behtar mehsoos ho raha hai"* or *"Bukhar barh gaya hai"*).
* **Outputs:**
  * Scheduled reminder messages in warm UrduLish.
  * Recovery status update in patient EHR.
  * Re-triage escalation if patient reports worsening symptoms.
* **Tools It May Call:**
  * `schedule_patient_reminder(patient_id: str, remind_at: str, message: str)` (MCP tool)
  * `record_patient_feedback(encounter_id: str, adherence_score: int, symptom_status: str)` (MCP tool)
  * `flag_worsening_condition(patient_id: str, reason: str)` (MCP tool)
* **Things It Must NEVER Do:**
  * ❌ NEVER change medication dosage if the patient complains of side effects (must route to doctor).
  * ❌ NEVER spam patients; respects opt-out preferences and scheduling hours (09:00 - 21:00 PKT).
  * ❌ NEVER ignore reports of worsening condition.
* **When It Hands Off:**
  * If patient reports worsening or new red flags: Hands off to **Triage Agent** for urgent review.
  * If patient requests prescription adjustments: Hands off to **Attending Doctor**.
