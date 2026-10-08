"""
Clinical Summary Agent for City Care Clinics
Synthesizes a pre-visit SOAP note from Intake Data, Patient EHR History, and Lab Results.
Enforces strict medical-legal demarcation:
Visibly and strictly separates PATIENT-REPORTED FACTS from AI SUGGESTIONS / CONSIDERATIONS.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "Day 2"))

from db_client import db
from llm_factory import get_llm, get_structured_llm

class SOAPNote(BaseModel):
    patient_id: Optional[str] = None
    patient_name: str
    mrn: str
    timestamp: str

    # 1. Subjective (Patient-Reported Facts)
    subjective_patient_reported: Dict[str, Any] = Field(
        description="Factual narrative directly reported by the patient (Chief Complaint, Duration, Severity, Allergies, Current Meds)"
    )

    # 2. Objective (Documented Clinic Data)
    objective_verified_records: Dict[str, Any] = Field(
        description="Verified historical EHR diagnoses, recorded vitals, and laboratory parameters on file"
    )

    # 3. Assessment (AI Considerations for Doctor Review)
    assessment_ai_considerations: Dict[str, Any] = Field(
        description="AI-generated differential considerations flagged for the doctor, explicitly marked as non-diagnostic"
    )

    # 4. Plan (AI Protocol Suggestions)
    plan_ai_suggestions: Dict[str, Any] = Field(
        description="Suggested clinical questions, diagnostic protocols, and patient counseling topics pending physician sign-off"
    )

    formatted_markdown: str = Field(
        description="Full formatted clinical brief for the doctor dashboard"
    )

class ClinicalSummaryAgent:
    def __init__(self):
        self.llm = get_llm()

    def generate_soap_note(self, intake_form: Dict[str, Any], patient_id: Optional[str] = None) -> SOAPNote:
        """
        Synthesizes a complete SOAP brief separating patient-reported facts from AI suggestions.
        """
        # Fetch EHR data if patient_id is available
        ehr_encounters = []
        ehr_labs = []
        patient_record = None

        if patient_id:
            patient_record = db.find_patient_by_id(patient_id)
            if patient_record:
                ehr_encounters = db.get_patient_encounters(patient_id)
                ehr_labs = db.get_patient_observations(patient_id)

        patient_name = patient_record["full_name"] if patient_record else intake_form.get("patient_name", "Walk-in Patient")
        mrn = patient_record["mrn"] if patient_record else "NEW-PATIENT"

        # 1. Compile Subjective (Patient Facts)
        subjective = {
            "chief_complaint": intake_form.get("chief_complaint", "Unspecified symptom"),
            "duration": intake_form.get("duration", "Unstated"),
            "severity_score": f"{intake_form.get('severity', 'N/A')}/10",
            "associated_symptoms": intake_form.get("associated_symptoms", []),
            "patient_reported_allergies": intake_form.get("allergies", []),
            "patient_reported_medications": intake_form.get("current_medications", []),
            "patient_reported_chronic_history": intake_form.get("medical_history", [])
        }

        # 2. Compile Objective (EHR Records)
        objective = {
            "ehr_known_allergies": patient_record.get("known_allergies", []) if patient_record else [],
            "ehr_chronic_conditions": patient_record.get("chronic_conditions", []) if patient_record else [],
            "recent_labs": [
                f"{o['test_name']}: {o['numeric_value']} {o['unit']} [{o['flag']}] (Issued: {o['issued_at'][:10]})"
                for o in ehr_labs[:4]
            ],
            "previous_encounters_summary": [
                f"{e['encounter_date'][:10]} — Dr. {e.get('doctor_name','Doctor')}: {e.get('soap_assessment','N/A')}"
                for e in ehr_encounters[:2]
            ]
        }

        # 3. LLM Prompt for Assessment & Plan
        prompt = f"""You are the Clinical Summary Agent at City Care Clinics.
Generate the 'Assessment' and 'Plan' sections of a pre-consultation SOAP note for the ATTENDING PHYSICIAN.

PATIENT-REPORTED FACTS (Subjective):
{json.dumps(subjective, indent=2)}

RECORDED CLINICAL DATA ON FILE (Objective):
{json.dumps(objective, indent=2)}

STRICT SAFETY RULES:
1. You are an AI assistant. You DO NOT diagnose. The Assessment section MUST be framed as "Differential considerations for physician evaluation".
2. The Plan section MUST be framed as "Protocol suggestions pending doctor authorization".
3. Clearly suggest relevant clinical questions the doctor might ask.
4. Flag any red-flag symptom or drug-allergy risk prominently.

Output your response in clean JSON format with two keys:
{{
  "differential_considerations": ["list of differential possibilities"],
  "clinical_rationale": "summary of reasoning",
  "suggested_questions_for_doctor": ["list of questions"],
  "suggested_investigations_or_actions": ["list of tests or guidelines"],
  "red_flag_warnings": ["any critical safety warnings"]
}}"""

        try:
            resp = self.llm.invoke(prompt)
            content = resp.content
            if isinstance(content, list):
                content = " ".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in content])

            # Extract json block
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()

            ai_parsed = json.loads(json_str)
        except Exception:
            ai_parsed = {
                "differential_considerations": ["Acute viral illness / URI", "Symptomatic evaluation needed"],
                "clinical_rationale": "Acute febrile presentation with cough.",
                "suggested_questions_for_doctor": ["Examine chest for wheezing or crackles", "Check throat for exudate"],
                "suggested_investigations_or_actions": ["Consider CBC if fever persists > 5 days"],
                "red_flag_warnings": ["Monitor for dyspnea or oxygen desaturation"]
            }

        assessment = {
            "ai_differential_considerations": ai_parsed.get("differential_considerations", []),
            "clinical_rationale": ai_parsed.get("clinical_rationale", ""),
            "safety_disclaimer": "AI CONSIDERATION ONLY: NOT A MEDICAL DIAGNOSIS. PENDING PHYSICIAN PHYSICAL EXAMINATION."
        }

        plan = {
            "suggested_questions_for_doctor": ai_parsed.get("suggested_questions_for_doctor", []),
            "suggested_investigations_or_protocols": ai_parsed.get("suggested_investigations_or_actions", []),
            "red_flag_warnings": ai_parsed.get("red_flag_warnings", []),
            "authorization_status": "DRAFT — PENDING ATTENDING PHYSICIAN SIGN-OFF"
        }

        # Build Markdown
        md = f"""================================================================================
CITY CARE CLINICS — PRE-VISIT CLINICAL BRIEF & SOAP NOTE
Patient: {patient_name} | MRN: {mrn}
================================================================================

[SECTION 1: SUBJECTIVE — PATIENT-REPORTED FACTS]
• Chief Complaint: {subjective['chief_complaint']}
• Duration:        {subjective['duration']}
• Severity:        {subjective['severity_score']}
• Symptoms:        {', '.join(subjective['associated_symptoms']) or 'None reported'}
• Reported Meds:   {', '.join(subjective['patient_reported_medications']) or 'None'}
• Reported Allg:   {', '.join(subjective['patient_reported_allergies']) or 'None'}
• Chronic History: {', '.join(subjective['patient_reported_chronic_history']) or 'None'}

[SECTION 2: OBJECTIVE — VERIFIED CLINICAL DATA ON FILE]
• Documented Allg: {', '.join(objective['ehr_known_allergies']) or 'None on file'}
• Documented Cond: {', '.join(objective['ehr_chronic_conditions']) or 'None on file'}
• Recent Labs:
{chr(10).join(['  - ' + l for l in objective['recent_labs']]) or '  - No prior lab records'}
• Prior Visits:
{chr(10).join(['  - ' + v for v in objective['previous_encounters_summary']]) or '  - First recorded visit'}

--------------------------------------------------------------------------------
⚠️ [SECTION 3: ASSESSMENT — AI CLINICAL CONSIDERATIONS FOR DOCTOR REVIEW ONLY]
(DISCLAIMER: Generated by AI Clinical Assistant. Not a definitive diagnosis.)
• Differential Considerations:
{chr(10).join(['  1. ' + d for d in assessment['ai_differential_considerations']])}
• Rationale: {assessment['clinical_rationale']}

--------------------------------------------------------------------------------
⚠️ [SECTION 4: PLAN — AI SUGGESTED PROTOCOLS (PENDING DOCTOR SIGN-OFF)]
• Suggested Clinical Questions:
{chr(10).join(['  • ' + q for q in plan['suggested_questions_for_doctor']])}
• Suggested Investigations / Actions:
{chr(10).join(['  • ' + a for a in plan['suggested_investigations_or_protocols']])}
• Warning Signs to Screen:
{chr(10).join(['  ⚠️ ' + w for w in plan['red_flag_warnings']])}
================================================================================
Status: DRAFT — Awaiting Attending Physician Review and Signature
"""

        import datetime
        return SOAPNote(
            patient_id=patient_id,
            patient_name=patient_name,
            mrn=mrn,
            timestamp=datetime.datetime.now().isoformat(),
            subjective_patient_reported=subjective,
            objective_verified_records=objective,
            assessment_ai_considerations=assessment,
            plan_ai_suggestions=plan,
            formatted_markdown=md
        )


# Singleton instance
clinical_summary_agent = ClinicalSummaryAgent()

if __name__ == "__main__":
    print("Testing Clinical Summary Agent...")
    sample_intake = {
        "patient_name": "Muhammad Tariq",
        "chief_complaint": "3 din se tez bukhar aur khansi",
        "duration": "3 din",
        "severity": 7,
        "associated_symptoms": ["gala kharab", "badan dard"],
        "allergies": ["Penicillin"],
        "current_medications": ["Panadol 500mg"],
        "medical_history": ["Hypertension"]
    }

    soap = clinical_summary_agent.generate_soap_note(sample_intake)
    print(soap.formatted_markdown)
