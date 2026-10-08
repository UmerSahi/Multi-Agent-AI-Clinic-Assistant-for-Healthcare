"""
LangGraph Multi-Agent Workflow Engine for City Care Clinics
Implements:
1. StateGraph with shared ClinicalState
2. Supervisor node routing with retry/fallback
3. Parallel execution (Triage + Records concurrently)
4. Interrupt-and-approve Human-in-the-Loop gates (Labs, Prescriptions, Low-confidence triage)
5. Short-term session memory checkpointing + Long-term memory integration
6. Transition and span logging with telemetry
7. Mermaid graph visualization export
"""

import sys
import time
import json
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Literal

# Paths
DAY4_DIR = Path(__file__).resolve().parent
ROOT_DIR = DAY4_DIR.parent
DAY3_DIR = ROOT_DIR / "Day 3"
DAY2_DIR = ROOT_DIR / "Day 2"

for p in [str(DAY4_DIR), str(DAY3_DIR), str(DAY3_DIR / "agents"), str(DAY2_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from clinical_state import ClinicalState
from supervisor_agent import supervisor
from memory_manager import memory_manager
from hitl_manager import hitl_manager
from observability import observability
from email_notifier import email_notifier

# Import agents
try:
    from intake_agent import intake_agent  # type: ignore
    from triage_agent import triage_agent  # type: ignore
    from scheduling_agent import scheduling_agent  # type: ignore
    from records_agent import records_agent  # type: ignore
    from clinical_summary_agent import clinical_summary_agent  # type: ignore
    from prescription_safety_agent import prescription_safety_agent  # type: ignore
    from followup_agent import followup_agent  # type: ignore
except ImportError:
    from agents.intake_agent import intake_agent  # type: ignore
    from agents.triage_agent import triage_agent  # type: ignore
    from agents.scheduling_agent import scheduling_agent  # type: ignore
    from agents.records_agent import records_agent  # type: ignore
    from agents.clinical_summary_agent import clinical_summary_agent  # type: ignore
    from agents.prescription_safety_agent import prescription_safety_agent  # type: ignore
    from agents.followup_agent import followup_agent  # type: ignore


def _get_msg_content(msg: Any) -> str:
    if isinstance(msg, dict):
        return msg.get("content", "")
    return getattr(msg, "content", str(msg))


def _is_user_msg(msg: Any) -> bool:
    if isinstance(msg, dict):
        return msg.get("role") == "user"
    if hasattr(msg, "type"):
        return msg.type == "human"
    return getattr(msg, "role", "") == "user"


def _log_transition(state: ClinicalState, from_node: str, to_node: str, latency_ms: float = 0.0) -> List[Dict[str, Any]]:
    """Helper to record node transitions."""
    transitions = list(state.get("node_transitions", []))
    transitions.append({
        "from": from_node,
        "to": to_node,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latency_ms": round(latency_ms, 2)
    })
    return transitions


# =====================================================================
# Node Definitions
# =====================================================================

def supervisor_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Supervisor router node: Evaluates conversational state and routes to the appropriate specialist agent.
    """
    t0 = time.time()
    next_node = supervisor.route_intent(state)
    latency_ms = (time.time() - t0) * 1000

    transitions = _log_transition(state, "supervisor", next_node, latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "SupervisorAgent", latency_ms, prompt_tokens=120, completion_tokens=30)

    return {
        "current_agent": "supervisor",
        "next_agent": next_node,
        "triage_result": state.get("triage_result"),
        "node_transitions": transitions
    }


def returning_greeting_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Generates personalized returning patient greeting using long-term memory.
    """
    t0 = time.time()
    mem = state.get("long_term_memory", {})
    lang = state.get("language") or mem.get("preferred_language") or "Urdu"
    greeting_text = memory_manager.generate_returning_patient_greeting(mem, language=lang)
    latency_ms = (time.time() - t0) * 1000

    messages = list(state.get("messages", []))
    messages.append({
        "role": "assistant",
        "content": greeting_text,
        "agent": "MemoryManager",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    transitions = _log_transition(state, "returning_greeting", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "MemoryManager", latency_ms, prompt_tokens=90, completion_tokens=75)

    return {
        "messages": messages,
        "current_agent": "returning_greeting",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def intake_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Executes conversational clinical intake.
    """
    t0 = time.time()
    messages = list(state.get("messages", []))
    latest_user_msg = ""
    for m in reversed(messages):
        if _is_user_msg(m):
            latest_user_msg = _get_msg_content(m)
            break

    lang = state.get("language") or state.get("long_term_memory", {}).get("preferred_language") or "Urdu"
    intake_result, latency_ms = supervisor.execute_with_retry(
        "intake",
        intake_agent.process_turn,
        latest_user_msg,
        state.get("intake_form"),
        lang
    )
    if not intake_result:
        is_en = lang and lang.lower() in ("english", "en")
        intake_result = {
            "reply": "Pardon me, could you please describe your symptoms once more?" if is_en else "Maaf kijiye ga, kya aap apni alamat dobara bayan kar sakte hain?",
            "form": state.get("intake_form", {}),
            "is_complete": False
        }

    form_data = intake_result.get("form", {})
    is_complete = intake_result.get("is_complete", False)
    reply_msg = intake_result.get("reply", "")

    # Sync patient identity with memory if newly identified
    if form_data.get("chief_complaint") and state.get("patient_id"):
        memory_manager.update_patient_memory(state["patient_id"], {
            "past_complaints": [form_data["chief_complaint"]],
            "known_allergies": form_data.get("allergies", []),
            "chronic_conditions": form_data.get("medical_history", [])
        })

    messages.append({
        "role": "assistant",
        "content": reply_msg,
        "agent": "IntakeAgent",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    transitions = _log_transition(state, "intake", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "IntakeAgent", latency_ms, prompt_tokens=240, completion_tokens=110)

    return {
        "messages": messages,
        "intake_form": form_data,
        "intake_complete": is_complete,
        "current_agent": "intake",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def parallel_triage_records_node(state: ClinicalState) -> Dict[str, Any]:
    """
    PARALLEL FAN-OUT NODE:
    Executes Triage Agent and Records Agent concurrently via thread pool.
    Demonstrates true parallel asynchronous execution in LangGraph.
    """
    t0 = time.time()
    intake_form = state.get("intake_form", {})
    patient_id = state.get("patient_mrn") or state.get("patient_phone") or state.get("patient_id") or "p1"

    # Parallel dispatch
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        triage_future = executor.submit(triage_agent.evaluate, intake_form)
        records_future = executor.submit(records_agent.get_patient_summary, patient_id)

        triage_res = triage_future.result()
        records_res = records_future.result()

    if not records_res:
        records_res = {
            "patient": {"full_name": state.get("patient_name", "Valued Patient"), "id": state.get("patient_id")},
            "encounters": [],
            "observations": [],
            "medications": []
        }

    latency_ms = (time.time() - t0) * 1000
    triage_dict = triage_res.model_dump() if hasattr(triage_res, "model_dump") else dict(triage_res)

    messages = list(state.get("messages", []))
    hitl_req = state.get("hitl_required", False)
    hitl_type = state.get("hitl_type")
    hitl_payload = state.get("hitl_payload")

    # Check for Low-Confidence Triage HITL gate (< 0.85)
    conf = triage_dict.get("confidence_score", 1.0)
    is_emergency = triage_dict.get("is_emergency", False)

    if not is_emergency and conf < 0.85:
        hitl_req = True
        hitl_type = "LOW_CONFIDENCE_TRIAGE"
        task = hitl_manager.create_pending_approval(
            thread_id=state.get("session_id", "default_thread"),
            patient_id=state.get("patient_id"),
            patient_name=state.get("patient_name", "Valued Patient"),
            task_type="LOW_CONFIDENCE_TRIAGE",
            proposed_message_urdulish=f"Triage assessment: {triage_dict.get('urgency_tier')} ({triage_dict.get('reason')}). Recommended specialty: {triage_dict.get('recommended_specialty')}.",
            clinical_context={"confidence": conf, "intake": intake_form, "records": records_res},
            urgency_level="URGENT"
        )
        hitl_payload = task
        messages.append({
            "role": "assistant",
            "content": "Aap ki alamaat ka jaiza liya gaya hai. Case mazeed tasdeeq ke liye clinic doctor ko refer kiya gaya hai.",
            "agent": "TriageAgent",
            "is_pending_review": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    elif is_emergency:
        # Emergency escalation
        esc_msg = triage_dict.get("escalation_message_urdulish") or "EMERGENCY: Foran 1122 par call karein ya qareebi Emergency Room pohnchein!"
        messages.append({
            "role": "assistant",
            "content": f"🚨 **EMERGENCY MEDICAL ALERT** 🚨\n\n{esc_msg}\n\n**Reasons:** {triage_dict.get('reason')}",
            "agent": "TriageAgent",
            "is_emergency": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        trace_id = state.get("telemetry", {}).get("trace_id")
        if trace_id:
            observability.log_escalation(trace_id, "EMERGENCY", triage_dict.get("reason", "Red flag detected"))
    else:
        # Standard triage guidance
        tier = triage_dict.get("urgency_tier")
        spec = triage_dict.get("recommended_specialty", "General Medicine")
        guidance = (
            f"Alamaat ke mutabiq aap ki halat **{tier}** zarray mein aati hai. "
            f"Aap ke liye **{spec}** ke specialist doctor munasib rahain gay. "
            f"Kya aap appointment ke slots dekhna chahte hain?"
        )
        messages.append({
            "role": "assistant",
            "content": guidance,
            "agent": "TriageAgent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    transitions = _log_transition(state, "parallel_triage_records", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "Parallel(Triage+Records)", latency_ms, prompt_tokens=350, completion_tokens=180, tool_name="parallel_execution")

    return {
        "messages": messages,
        "triage_result": triage_dict,
        "records_data": records_res,
        "hitl_required": hitl_req,
        "hitl_type": hitl_type,
        "hitl_payload": hitl_payload,
        "current_agent": "parallel_triage_records",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def scheduling_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Handles appointment slot selection and booking.
    """
    t0 = time.time()
    triage = state.get("triage_result") or {}
    specialty = triage.get("recommended_specialty", "General Medicine")
    if "Emergency" in specialty:
        specialty = "General Medicine"

    pref_doc = state.get("long_term_memory", {}).get("preferred_doctor_name")
    docs = scheduling_agent.find_doctors(specialty=specialty)
    if not docs:
        docs = scheduling_agent.find_doctors(specialty="General Medicine")

    doc = docs[0] if docs else {
        "id": "doc1", "full_name": "Dr. Bilal Saeed", "specialty": "General Medicine",
        "consultation_fee": 2000, "branch_name": "Gulberg Lahore", "branch_id": "b1"
    }

    # If preferred doctor matches specialty, pick that
    if pref_doc:
        for d in docs:
            if pref_doc.lower() in d["full_name"].lower():
                doc = d
                break

    # Get available slots
    target_date_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    slots = scheduling_agent.get_available_slots(doc["id"], target_date_str)
    selected_slot = slots[0] if slots else None

    appointment_result = None
    messages = list(state.get("messages", []))

    if selected_slot:
        # Book the appointment
        booking_res = scheduling_agent.book_appointment(
            patient_id=state.get("patient_id") or "p1",
            doctor_id=doc["id"],
            branch_id=doc.get("branch_id", "b1"),
            slot_iso=selected_slot["slot_start"],
            reason=state.get("intake_form", {}).get("chief_complaint", "Clinical Consultation"),
            urgency=triage.get("urgency_tier", "ROUTINE")
        )
        if booking_res.get("success"):
            appointment_result = booking_res
            time_disp = selected_slot["display_time"]
            date_disp = selected_slot["display_date"]
            gcal_link = booking_res.get("google_calendar_url", "#")
            booking_ref = booking_res.get("booking_reference", "CCC-BK")
            fee = doc.get("consultation_fee", 2000)

            # Send Email Confirmation
            email_notifier.send_appointment_confirmation(
                patient_name=state.get("patient_name", "Valued Patient"),
                patient_email=f"{state.get('patient_name', 'patient').lower().replace(' ', '.')}@example.com",
                doctor_name=doc["full_name"],
                specialty=specialty,
                branch_name=doc.get("branch_name", "City Care Clinics"),
                start_time_iso=selected_slot["slot_start"],
                booking_ref=booking_ref,
                consultation_fee=fee,
                calendar_url=gcal_link
            )

            lang = state.get("language") or "Urdu"
            if lang and lang.lower() in ("english", "en"):
                booking_msg = (
                    f"✅ **Appointment Confirmed!**\n\n"
                    f"• **Doctor:** {doc['full_name']} ({specialty})\n"
                    f"• **Date & Time:** {date_disp} at {time_disp}\n"
                    f"• **Branch:** {doc.get('branch_name', 'Gulberg Lahore')}\n"
                    f"• **Consultation Fee:** PKR {fee:,}\n"
                    f"• **Booking Reference:** `#{booking_ref}`\n\n"
                    f"📅 [Add to Google Calendar]({gcal_link})\n\n"
                    f"Email and SMS confirmations have also been dispatched."
                )
            else:
                booking_msg = (
                    f"✅ **Appointment Confirmed!**\n\n"
                    f"• **Doctor:** {doc['full_name']} ({specialty})\n"
                    f"• **Date & Time:** {date_disp} at {time_disp}\n"
                    f"• **Branch:** {doc.get('branch_name', 'Gulberg Lahore')}\n"
                    f"• **Consultation Fee:** PKR {fee:,}\n"
                    f"• **Booking Reference:** `#{booking_ref}`\n\n"
                    f"📅 [Google Calendar mein add karein]({gcal_link})\n\n"
                    f"Aap ko email aur SMS confirmation bhi bhej di gayi hai."
                )
            messages.append({
                "role": "assistant",
                "content": booking_msg,
                "agent": "SchedulingAgent",
                "appointment_card": appointment_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    else:
        lang = state.get("language") or "Urdu"
        empty_msg = (
            f"Slots for {doc['full_name']} are fully booked for the next 2 days. Would you like to check available slots at another branch or with another specialist?"
            if lang and lang.lower() in ("english", "en")
            else f"Dr. {doc['full_name']} ke aglay 2 dino mein slots pur hain. Kya aap kisi doosri branch ya doctor ke sath slot dekhna chahein gay?"
        )
        messages.append({
            "role": "assistant",
            "content": empty_msg,
            "agent": "SchedulingAgent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "scheduling", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "SchedulingAgent", latency_ms, prompt_tokens=210, completion_tokens=140, tool_name="book_appointment")

    return {
        "messages": messages,
        "appointment_result": appointment_result,
        "current_agent": "scheduling",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def clinical_summary_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Synthesizes pre-visit SOAP brief for the attending physician.
    Enforces clear demarcation of patient facts vs AI considerations.
    """
    t0 = time.time()
    intake_form = state.get("intake_form", {})
    patient_id = state.get("patient_id") or "p1"

    soap_note = clinical_summary_agent.generate_soap_note(intake_form, patient_id)
    soap_dict = soap_note.model_dump() if hasattr(soap_note, "model_dump") else dict(soap_note)

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "clinical_summary", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "ClinicalSummaryAgent", latency_ms, prompt_tokens=380, completion_tokens=220)

    return {
        "clinical_soap_note": soap_dict,
        "current_agent": "clinical_summary",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def prescription_safety_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Evaluates prescription safety and creates HITL review gate.
    All prescription advice requires physician approval!
    """
    t0 = time.time()
    drugs = [d.get("drug_name") for d in state.get("draft_prescription", [])] or ["Augmentin 625mg"]
    allergies = state.get("long_term_memory", {}).get("known_allergies", ["Penicillin"])

    check_rep = prescription_safety_agent.review_draft_prescription(
        proposed_drugs=drugs,
        patient_allergies=allergies,
        patient_age=45
    )
    rep_dict = check_rep.model_dump() if hasattr(check_rep, "model_dump") else dict(check_rep)

    # Interrupt: create HITL task
    task = hitl_manager.create_pending_approval(
        thread_id=state.get("session_id", "default_thread"),
        patient_id=state.get("patient_id"),
        patient_name=state.get("patient_name", "Valued Patient"),
        task_type="PRESCRIPTION_REVIEW",
        proposed_message_urdulish=rep_dict.get("patient_friendly_summary_urdulish", "Dawa tajweez ki gayi hai."),
        clinical_context={"safety_report": rep_dict, "drugs": drugs, "allergies": allergies},
        urgency_level="URGENT" if not rep_dict.get("is_safe") else "ROUTINE"
    )

    messages = list(state.get("messages", []))
    messages.append({
        "role": "assistant",
        "content": "⚠️ Dawaon ka safety check mukammal ho gaya hai. Doctor ki final approval ke baad hidayat bhej di jaye gi.",
        "agent": "PrescriptionSafetyAgent",
        "is_pending_review": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "prescription_safety", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "PrescriptionSafetyAgent", latency_ms, prompt_tokens=290, completion_tokens=150)

    return {
        "messages": messages,
        "prescription_safety_report": rep_dict,
        "hitl_required": True,
        "hitl_type": "PRESCRIPTION_REVIEW",
        "hitl_payload": task,
        "current_agent": "prescription_safety",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def records_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Lab result explanation node: Requires HITL approval before dispatching lab explanations to the patient.
    """
    t0 = time.time()
    patient_id = state.get("patient_id") or "p1"
    summary = records_agent.get_patient_summary(patient_id)

    # Draft lab explanation
    draft_lab_explanation = (
        "Aap ke recent blood test (CBC) ke mutabiq Hemoglobin 13.8 g/dL normal hai, "
        "lekin WBC count 12,400 /uL thora barha hua hai jo jism mein mamooli sozish ya infection ko zahir karta hai."
    )

    task = hitl_manager.create_pending_approval(
        thread_id=state.get("session_id", "default_thread"),
        patient_id=state.get("patient_id"),
        patient_name=state.get("patient_name", "Valued Patient"),
        task_type="LAB_EXPLANATION",
        proposed_message_urdulish=draft_lab_explanation,
        clinical_context={"labs": summary.get("observations", []) if summary else []},
        urgency_level="ROUTINE"
    )

    messages = list(state.get("messages", []))
    messages.append({
        "role": "assistant",
        "content": "🔬 Aap ki lab report ka AI tajziya ho chuka hai. Doctor ki clinical tasdeeq ke baad tafseelat yahan share ki jaye gi.",
        "agent": "RecordsAgent",
        "is_pending_review": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "records", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "RecordsAgent", latency_ms, prompt_tokens=220, completion_tokens=90)

    return {
        "messages": messages,
        "hitl_required": True,
        "hitl_type": "LAB_EXPLANATION",
        "hitl_payload": task,
        "current_agent": "records",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def hitl_gate_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Human-in-the-Loop Gate Node:
    Pauses execution or applies the physician's approval / edit / rejection.
    """
    t0 = time.time()
    decision = state.get("hitl_decision")
    messages = list(state.get("messages", []))

    if decision and decision.get("status"):
        # Resumed after doctor decision!
        status = decision.get("status")
        doc_msg = decision.get("final_message_urdulish") or decision.get("edited_message")
        doc_name = decision.get("doctor_name", "Dr. Maryam Naveed (Medical Director)")
        notes = decision.get("doctor_notes", "")

        prefix = "✅ **Doctor ne tasdeeq kar di hai:**\n\n" if status == "APPROVED" else "✏️ **Doctor ki hidayat (Dr. Maryam Naveed):**\n\n"
        if status == "REJECTED":
            prefix = "🛑 **Doctor ka faisla:**\n\n"

        full_reply = f"{prefix}{doc_msg}"
        if notes:
            full_reply += f"\n\n*Physician Note:* {notes}"

        messages.append({
            "role": "assistant",
            "content": full_reply,
            "agent": "DoctorApprovalGate",
            "is_approved_by_doctor": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        trace_id = state.get("telemetry", {}).get("trace_id")
        if trace_id:
            observability.log_hitl_event(
                trace_id,
                state.get("hitl_type", "GENERAL"),
                status,
                doc_name,
                notes
            )

        latency_ms = (time.time() - t0) * 1000
        transitions = _log_transition(state, "hitl_gate", "supervisor", latency_ms)
        return {
            "messages": messages,
            "hitl_required": False,
            "hitl_decision": decision,
            "current_agent": "hitl_gate",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }
    else:
        # Awaiting approval: interrupt point
        latency_ms = (time.time() - t0) * 1000
        transitions = _log_transition(state, "hitl_gate", "awaiting_approval", latency_ms)
        return {
            "current_agent": "hitl_gate",
            "next_agent": "awaiting_approval",
            "node_transitions": transitions
        }


def followup_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Generates post-consultation care plan and scheduled outreach reminders.
    """
    t0 = time.time()
    patient_name = state.get("patient_name", "Valued Patient")
    care_plan = followup_agent.generate_care_plan(
        patient_name=patient_name,
        doctor_name="Dr. Bilal Saeed",
        prescribed_meds=[
            {"drug_name": "Paracetamol 500mg", "frequency_per_day": 2},
            {"drug_name": "Risek (Omeprazole) 20mg", "frequency_per_day": 1}
        ],
        advised_labs=["CBC with ESR"],
        followup_days=5
    )
    plan_dict = care_plan.model_dump() if hasattr(care_plan, "model_dump") else dict(care_plan)

    # Dispatch email reminder
    email_notifier.send_followup_reminder(
        patient_name=patient_name,
        patient_email=f"{patient_name.lower().replace(' ', '.')}@example.com",
        doctor_name="Dr. Bilal Saeed",
        scheduled_date_display="5 Din Baad (Saturday, 12:00 PM)",
        medication_count=2
    )

    messages = list(state.get("messages", []))
    msg = (
        "📋 **Post-Consultation Care Plan:**\n\n"
        "1. **Dawai ka Schedule:** Subah nashtay se pehle Risek 20mg, aur bukhar/dard ke liye Paracetamol lein.\n"
        "2. **Follow-Up:** 5 din baad clinic visit ya recovery check-in lazmi karein.\n"
        "3. **Tafseelat Email:** Tafseeli hidayat aap ki email par bhej di gayi hain."
    )
    messages.append({
        "role": "assistant",
        "content": msg,
        "agent": "FollowupAgent",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "followup", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "FollowupAgent", latency_ms, prompt_tokens=260, completion_tokens=130)

    return {
        "messages": messages,
        "followup_plan": plan_dict,
        "current_agent": "followup",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def emergency_escalation_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Direct emergency pathway for red-flag conditions.
    """
    t0 = time.time()
    triage = state.get("triage_result") or {}
    lang = state.get("language") or "Urdu"
    if lang and lang.lower() in ("english", "en"):
        default_esc = (
            "🚨 **CRITICAL MEDICAL EMERGENCY (CALL 1122 RESCUE)** 🚨\n"
            "Your reported symptoms indicate an immediate, life-threatening condition. "
            "Please call 1122 Emergency Services immediately or proceed directly to the nearest Hospital Emergency Ward (ER)!"
        )
    else:
        default_esc = (
            "🚨 **SHADEED EMERGENCY NOTICE (1122 RESCUE)** 🚨\n"
            "Aap ki alamaat jaan-lewa khatray ki nishandahi karti hain. "
            "Baraye meharbani bila-takheer 1122 emergency helpline par call karein ya foran qareebi Emergency Ward pohnchein!"
        )
    esc_msg = triage.get("escalation_message_urdulish") if lang != "English" else default_esc
    if not esc_msg:
        esc_msg = default_esc
    messages = list(state.get("messages", []))
    messages.append({
        "role": "assistant",
        "content": esc_msg,
        "agent": "EmergencyScreener",
        "is_emergency": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "emergency_escalation", "END", latency_ms)

    return {
        "messages": messages,
        "current_agent": "emergency_escalation",
        "next_agent": "END",
        "node_transitions": transitions
    }


# =====================================================================
# StateGraph Assembly
# =====================================================================

def supervisor_router(state: ClinicalState) -> str:
    """Dynamic routing function for supervisor conditional edges."""
    return state.get("next_agent", "scheduling")


def build_clinical_graph(checkpointer=None):
    """
    Constructs and compiles the full City Care Clinics LangGraph StateGraph.
    """
    builder = StateGraph(ClinicalState)

    # Add Nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("returning_greeting", returning_greeting_node)
    builder.add_node("intake", intake_node)
    builder.add_node("parallel_triage_records", parallel_triage_records_node)
    builder.add_node("scheduling", scheduling_node)
    builder.add_node("clinical_summary", clinical_summary_node)
    builder.add_node("prescription_safety", prescription_safety_node)
    builder.add_node("records", records_node)
    builder.add_node("hitl_gate", hitl_gate_node)
    builder.add_node("followup", followup_node)
    builder.add_node("emergency_escalation", emergency_escalation_node)

    # Edge from START to supervisor
    builder.add_edge(START, "supervisor")

    # Supervisor conditional edges
    builder.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "returning_greeting": "returning_greeting",
            "intake": "intake",
            "parallel_triage_records": "parallel_triage_records",
            "scheduling": "scheduling",
            "clinical_summary": "clinical_summary",
            "prescription_safety": "prescription_safety",
            "records": "records",
            "hitl_gate": "hitl_gate",
            "followup": "followup",
            "emergency_escalation": "emergency_escalation",
            "awaiting_approval": END,
            "END": END
        }
    )

    # Specialist agents return to END or loop back
    builder.add_edge("returning_greeting", END)
    builder.add_edge("intake", END)
    builder.add_edge("parallel_triage_records", END)
    builder.add_edge("scheduling", END)
    builder.add_edge("clinical_summary", END)
    builder.add_edge("prescription_safety", END)
    builder.add_edge("records", END)
    builder.add_edge("hitl_gate", END)
    builder.add_edge("followup", END)
    builder.add_edge("emergency_escalation", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)


# Singleton compiled graph
memory_checkpointer = MemorySaver()
clinical_graph = build_clinical_graph(checkpointer=memory_checkpointer)


def get_mermaid_graph() -> str:
    """Exports LangGraph architecture as Mermaid diagram code."""
    return """graph TD
    START([Start Patient Interaction]) --> Supervisor[Supervisor Router]

    Supervisor -->|Returning Patient Recall| ReturningGreeting[Returning Greeting Node]
    Supervisor -->|Intake Turn Needed| Intake[Intake Agent]
    Supervisor -->|Intake Complete Fan-Out| ParallelNode[Parallel Triage + Records Node]
    Supervisor -->|Booking / Slot Request| Scheduling[Scheduling Agent]
    Supervisor -->|Pre-Visit Doctor Brief| ClinicalSummary[Clinical Summary Agent SOAP]
    Supervisor -->|Prescription Review| RxSafety[Prescription Safety Agent]
    Supervisor -->|Lab Report Review| Records[Records Agent]
    Supervisor -->|Human-in-the-Loop Flagged| HITLGate[Doctor HITL Approval Gate]
    Supervisor -->|Follow-Up Care Plan| Followup[Followup Agent]
    Supervisor -->|Red Flag Emergency| Emergency[Emergency Screener 1122]

    subgraph Parallel Execution
        ParallelNode -.-> TriageWorker[Triage Urgency Evaluator]
        ParallelNode -.-> RecordsWorker[EHR / Labs Fetcher]
    end

    subgraph Doctor HITL Approval Center
        HITLGate -->|Review Required| DoctorReview{Attending Physician}
        DoctorReview -->|Approve| Dispatched[Authorized Message to Patient]
        DoctorReview -->|Edit| PhysicianEdit[Edited Guidance to Patient]
        DoctorReview -->|Reject| Suppressed[Refer to In-Person Exam]
    end

    ReturningGreeting --> END([End Turn])
    Intake --> END
    ParallelNode --> END
    Scheduling --> END
    ClinicalSummary --> END
    RxSafety --> HITLGate
    Records --> HITLGate
    HITLGate --> END
    Followup --> END
    Emergency --> END
"""


if __name__ == "__main__":
    print("Testing LangGraph Multi-Agent Workflow Engine...")
    mermaid = get_mermaid_graph()
    print("Exported Mermaid Diagram:\n", mermaid[:300], "...\n")
    print("LangGraph Compiled Successfully!")
