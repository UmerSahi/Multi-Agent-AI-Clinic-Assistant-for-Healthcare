"""
Clinical State Definition for City Care Clinics LangGraph Architecture
Defines the unified state schema passed between all specialist agents,
supervisor, and human-in-the-loop review nodes.
"""

from typing import Dict, List, Any, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ClinicalState(TypedDict):
    """
    Unified LangGraph State for City Care Clinics.
    Maintains clinical facts, conversational memory, routing signals,
    and doctor review gates.
    """
    # 1. Short-Term Conversational Memory
    messages: Annotated[List[Dict[str, Any]], add_messages]
    session_id: str
    user_id: Optional[str]

    # 2. Patient Identity & Long-Term Memory
    patient_id: Optional[str]
    patient_name: Optional[str]
    patient_phone: Optional[str]
    patient_mrn: Optional[str]
    is_returning_patient: bool
    long_term_memory: Dict[str, Any]  # Preferences, past diagnoses, preferred doctor, language

    # 3. Clinical Intake Data
    intake_form: Dict[str, Any]  # Form extracted by IntakeAgent
    intake_complete: bool

    # 4. Triage Stratification
    triage_result: Optional[Dict[str, Any]]  # Urgency tier, confidence, red flags, 1122 alert

    # 5. Electronic Health Record (EHR) & Labs
    records_data: Optional[Dict[str, Any]]  # Encounters, observations, medications

    # 6. Scheduling & Appointments
    scheduling_request: Optional[Dict[str, Any]]  # Specialty, branch, doctor preference
    appointment_result: Optional[Dict[str, Any]]  # Confirmed appointment, gcal link, booking ref

    # 7. Clinical Summary (SOAP Note for Doctor)
    clinical_soap_note: Optional[Dict[str, Any]]  # Pre-visit SOAP note with fact/AI segregation

    # 8. Prescription Safety
    draft_prescription: Optional[List[Dict[str, Any]]]
    prescription_safety_report: Optional[Dict[str, Any]]  # Clashes, DDI, allergies, alerts

    # 9. Follow-Up Plan
    followup_plan: Optional[Dict[str, Any]]  # Med schedule, lab prep alerts, outreach msgs

    # 10. Human-in-the-Loop (HITL) Doctor Review
    hitl_required: bool
    hitl_type: Optional[str]  # "LAB_EXPLANATION", "PRESCRIPTION_REVIEW", "LOW_CONFIDENCE_TRIAGE"
    hitl_payload: Optional[Dict[str, Any]]  # Draft content waiting for doctor review
    hitl_decision: Optional[Dict[str, Any]]  # status: "approved" | "edited" | "rejected", doctor_notes, edited_text

    # 11. Workflow Orchestration & Telemetry
    current_agent: str
    next_agent: Optional[str]
    error_state: Optional[Dict[str, Any]]
    node_transitions: List[Dict[str, Any]]  # History of transitions [timestamp, node, latency_ms]
    telemetry: Dict[str, Any]  # Token counts, estimated cost, latency tracking
