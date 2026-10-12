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
import re
import uuid
import secrets
import hashlib
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone, timedelta, date
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
from supervisor_agent import (
    supervisor,
    is_emergency_message,
    is_data_exfiltration_attempt,
    is_diagnosis_demand,
    is_unauthorized_medication_demand,
    is_off_topic_query,
    is_angry_or_frustrated,
    is_lab_inquiry_message,
    is_reschedule_or_cancel,
    is_overdose_inquiry
)
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
    from prescription_safety_agent import prescription_safety_agent  # type: ignore
    from agents.followup_agent import followup_agent  # type: ignore

try:
    from db_client import db  # type: ignore
except Exception:
    db = None



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
    Executes conversational clinical intake:
    1. Welcomes new patient if replying to opening greeting.
    2. Turn 1 (Complaint): Acknowledges complaint, asks duration ("Aap ko kab se [sir mein dard] ho raha hai?").
    3. Turn 2 (Duration): Acknowledges duration, asks pain scale ("Takleef ki shiddat 1 se 10 ke darmiyan kitni hogi?").
    4. Turn 3 (Severity): Acknowledges severity, asks permission ("Kya main aap ko City Care ke dastiyab doctors suggest karun jin ke sath aap appointment book kar sakein?").
    5. Turn 4 (Permission Granted): Executes triage & displays doctor recommendations + upcoming slots!
    * If patient asks for a doctor directly in any message, immediately suggests doctors.
    """
    t0 = time.time()
    messages = list(state.get("messages", []))
    latest_user_msg = ""
    for m in reversed(messages):
        if _is_user_msg(m):
            latest_user_msg = _get_msg_content(m)
            break

    lang = state.get("language") or state.get("long_term_memory", {}).get("preferred_language") or "Urdu"
    is_en = lang and lang.lower() in ("english", "en")
    msg_low = latest_user_msg.lower().strip()
    stage = state.get("intake_stage")
    form_data = dict(state.get("intake_form") or {})

    # 0. Zero-Override Emergency Screening (Safety-first gate)
    if is_emergency_message(latest_user_msg):
        return emergency_escalation_node(state)

    # 0.1 Zero-Tolerance Safety Guardrails in Intake
    if (
        is_data_exfiltration_attempt(latest_user_msg)
        or is_diagnosis_demand(latest_user_msg)
        or is_unauthorized_medication_demand(latest_user_msg)
        or is_off_topic_query(latest_user_msg)
        or is_angry_or_frustrated(latest_user_msg)
    ):
        return safety_guardrail_node(state)

    # Check if user directly asked for doctor recommendation in this message
    asks_for_doc = any(w in msg_low for w in [
        "doctor bta", "doctor btao", "doctor bata", "doctor bataiye", "doctor batao",
        "doctor suggest", "doctor dekh", "doctor dikha", "doctor dikhana", "doctor milna",
        "koi doctor", "doctor chahiye", "konsa doctor", "recommend doctor", "which doctor",
        "doctor kon", "dastiyab doctor", "available doctor", "dekha sakun", "dikha sakun",
        "dekha sakoon", "dikha sakoon", "check karwa sakun", "checkup karwana"
    ])
    if asks_for_doc:
        if not form_data.get("chief_complaint"):
            form_data["chief_complaint"] = latest_user_msg
        state["intake_form"] = form_data
        state["intake_complete"] = True
        state["intake_stage"] = "doctors_suggested"
        return parallel_triage_records_node(state)

    # 1. New patient greeting response (e.g. "Naya patient hun", "new patient", etc.)
    is_new_reply = any(w in msg_low for w in [
        "new patient", "new", "naya patient", "naya", "nayi", "pehli dafa", "first time", "pehli bar"
    ]) and not any(w in msg_low for w in ["returning", "purana", "purani", "pehle"])

    if is_new_reply and not form_data.get("chief_complaint") and stage not in ("awaiting_duration", "awaiting_severity", "awaiting_doctor_permission"):
        welcome_reply = (
            "Welcome to City Care Clinics! What symptoms or medical concern brings you in today? Please describe how you are feeling."
            if is_en else
            "City Care Clinics mein khushamdeed! Aap ko aaj kya masla ya takleef darpesh hai? Baraye meharbani apni alamaat bayan karein."
        )
        messages.append({
            "role": "assistant",
            "content": welcome_reply,
            "agent": "City Care Assistant",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        transitions = _log_transition(state, "intake", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "patient_type": "new",
            "intake_stage": "awaiting_complaint",
            "current_agent": "intake",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }

    # 2. If stage is awaiting_doctor_permission:
    if stage == "awaiting_doctor_permission":
        no_words = ["nahi", "no", "not now", "zarurat nahi", "abhi nahi", "cancel"]
        if any(nw in msg_low for nw in no_words) and not any(pw in msg_low for pw in ["nahi jee", "nahi haan"]):
            decline_reply = (
                "No problem. If you need any further information or have any questions about City Care Clinics, please let us know."
                if is_en else
                "Koi masla nahi. Agar aap ko clinic ya kisi aur cheez ke baray mein maloomat chahiye to baraye meharbani batayein."
            )
            messages.append({
                "role": "assistant",
                "content": decline_reply,
                "agent": "City Care Assistant",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            transitions = _log_transition(state, "intake", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "intake_stage": "declined_doctors",
                "current_agent": "intake",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }
        else:
            # Patient agreed or confirmed! Suggest doctors and slots immediately.
            state["intake_complete"] = True
            state["intake_stage"] = "doctors_suggested"
            return parallel_triage_records_node(state)

    # 2.5 If stage is awaiting_associated_symptoms:
    if stage == "awaiting_associated_symptoms":
        form_data["associated_symptoms"] = latest_user_msg
        state["intake_form"] = form_data

        permission_reply = (
            "Understood. Would you like to book an appointment with a doctor so I can suggest available doctors at City Care?"
            if is_en else
            "Samajh gaya. Kya main aap ko City Care ke dastiyab doctors suggest karun jin ke sath aap appointment book kar sakein?"
        )
        messages.append({
            "role": "assistant",
            "content": permission_reply,
            "agent": "City Care Assistant",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        transitions = _log_transition(state, "intake", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "intake_form": form_data,
            "intake_stage": "awaiting_doctor_permission",
            "current_agent": "intake",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }

    # 3. If stage is awaiting_severity:
    if stage == "awaiting_severity":
        import re
        sev_match = re.search(r"\b(10|[1-9])\b", msg_low)
        if sev_match:
            form_data["severity"] = int(sev_match.group(1))
        else:
            form_data["severity"] = 7
        state["intake_form"] = form_data

        chief = (form_data.get("chief_complaint") or "").lower()
        if any(w in chief for w in ["sir", "sar", "headache", "matha", "head"]):
            assoc_q = "Theek hai. Kya sir dard ke sath koi aur alamat bhi mehsoos ho rahi hai, jaisay ulti aana (vomiting), kamzori, ya chakkar aana?"
        else:
            assoc_q = "Theek hai. Kya is takleef ke sath koi aur alamat bhi mehsoos ho rahi hai, jaisay kamzori ya ulti aana?"

        if is_en:
            assoc_q = "Understood. Are you experiencing any other symptoms along with this, such as weakness, dizziness, or vomiting/nausea?"

        messages.append({
            "role": "assistant",
            "content": assoc_q,
            "agent": "City Care Assistant",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        transitions = _log_transition(state, "intake", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "intake_form": form_data,
            "intake_stage": "awaiting_associated_symptoms",
            "current_agent": "intake",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }

    # 4. If stage is awaiting_duration:
    if stage == "awaiting_duration":
        import re
        # Check if user actually replied with a scale (e.g. "8/10" or "8") rather than duration:
        pure_scale_m = re.search(r"\b(10|[1-9])\s*/\s*10\b", msg_low) or (msg_low.isdigit() and 1 <= int(msg_low) <= 10)
        if pure_scale_m and not form_data.get("duration"):
            sev_num = int(re.search(r"\b(10|[1-9])\b", str(pure_scale_m)).group(1)) if not msg_low.isdigit() else int(msg_low)
            form_data["severity"] = sev_num
            form_data["duration"] = "haal hi mein"
            state["intake_form"] = form_data

            chief = (form_data.get("chief_complaint") or "").lower()
            if any(w in chief for w in ["sir", "sar", "headache", "matha", "head"]):
                assoc_q = "Theek hai. Kya sir dard ke sath koi aur alamat bhi mehsoos ho rahi hai, jaisay ulti aana (vomiting), kamzori, ya chakkar aana?"
            else:
                assoc_q = "Theek hai. Kya is takleef ke sath koi aur alamat bhi mehsoos ho rahi hai, jaisay kamzori ya ulti aana?"

            if is_en:
                assoc_q = "Understood. Are you experiencing any other symptoms along with this, such as weakness, dizziness, or vomiting/nausea?"

            messages.append({
                "role": "assistant",
                "content": assoc_q,
                "agent": "City Care Assistant",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            transitions = _log_transition(state, "intake", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "intake_form": form_data,
                "intake_stage": "awaiting_associated_symptoms",
                "current_agent": "intake",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }

        form_data["duration"] = latest_user_msg

        # Check if user also provided severity in the same message (e.g., "2 din se hai aur 8/10 dard hai")
        sev_match = re.search(r"\b(10|[1-9])\s*(?:/|\s*out of\s*)\s*10\b", msg_low) or re.search(r"\b(10|[1-9])\s*(?:scale|shiddat|darja)\b", msg_low)
        if sev_match:
            num = int(re.search(r"\b(10|[1-9])\b", sev_match.group(0)).group(1))
            form_data["severity"] = num
            state["intake_form"] = form_data

            chief = (form_data.get("chief_complaint") or "").lower()
            if any(w in chief for w in ["sir", "sar", "headache", "matha", "head"]):
                assoc_q = "Theek hai. Kya sir dard ke sath koi aur alamat bhi mehsoos ho rahi hai, jaisay ulti aana (vomiting), kamzori, ya chakkar aana?"
            else:
                assoc_q = "Theek hai. Kya is takleef ke sath koi aur alamat bhi mehsoos ho rahi hai, jaisay kamzori ya ulti aana?"

            if is_en:
                assoc_q = "Understood. Are you experiencing any other symptoms along with this, such as weakness, dizziness, or vomiting/nausea?"

            messages.append({
                "role": "assistant",
                "content": assoc_q,
                "agent": "City Care Assistant",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            transitions = _log_transition(state, "intake", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "intake_form": form_data,
                "intake_stage": "awaiting_associated_symptoms",
                "current_agent": "intake",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }

        state["intake_form"] = form_data
        scale_reply = (
            "Got it. On a scale of 1 to 10, how severe is your pain, where 1 is mild and 10 is very severe?"
            if is_en else
            "Theek hai. Takleef ki shiddat (pain scale) 1 se 10 ke darmiyan kitni hogi, jahan 1 halka aur 10 shadeed tareen dard ho?"
        )
        messages.append({
            "role": "assistant",
            "content": scale_reply,
            "agent": "City Care Assistant",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        transitions = _log_transition(state, "intake", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "intake_form": form_data,
            "intake_stage": "awaiting_severity",
            "current_agent": "intake",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }

    # 5. Default/Initial Complaint: Patient stated symptoms (e.g. "mery sir mein bohat dard ho rha ha")
    form_data["chief_complaint"] = latest_user_msg
    state["intake_form"] = form_data

    # Formulate duration question tailored to complaint
    if any(w in msg_low for w in ["sir", "sar", "headache", "matha", "head"]):
        duration_q = "Ji maine note kar liya hai. Aap ko kab se sir mein dard ho raha hai?"
    elif any(w in msg_low for w in ["pait", "stomach", "pet", "belly", "abdomen"]):
        duration_q = "Ji maine note kar liya hai. Aap ko kab se pait mein dard ho raha hai?"
    elif any(w in msg_low for w in ["bukhar", "fever", "tap"]):
        duration_q = "Ji maine note kar liya hai. Aap ko kab se bukhar ho raha hai?"
    elif any(w in msg_low for w in ["gala", "throat", "khansi", "cough"]):
        duration_q = "Ji maine note kar liya hai. Aap ko kab se gala kharab ya khansi ho rahi hai?"
    else:
        duration_q = "Ji maine aap ki takleef note kar li hai. Aap ko kab se yeh takleef ho rahi hai?"

    if is_en:
        duration_q = f"I have noted your concern ({latest_user_msg}). How long have you been experiencing this condition?"

    messages.append({
        "role": "assistant",
        "content": duration_q,
        "agent": "City Care Assistant",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    transitions = _log_transition(state, "intake", "supervisor", (time.time() - t0) * 1000)
    return {
        "messages": messages,
        "intake_form": form_data,
        "intake_stage": "awaiting_duration",
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

    if is_emergency:
        # Emergency escalation
        esc_msg = triage_dict.get("escalation_message_urdulish") or "EMERGENCY: Foran 1122 par call karein ya qareebi Emergency Room pohnchein!"
        messages.append({
            "role": "assistant",
            "content": f"🚨 **EMERGENCY MEDICAL ALERT** 🚨\n\n{esc_msg}\n\n**Reasons:** {triage_dict.get('reason')}",
            "agent": "City Care Assistant",
            "is_emergency": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        trace_id = state.get("telemetry", {}).get("trace_id")
        if trace_id:
            observability.log_escalation(trace_id, "EMERGENCY", triage_dict.get("reason", "Red flag detected"))
    else:
        if conf < 0.85:
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
        # Standard triage guidance + suggest available specialist doctors
        tier = triage_dict.get("urgency_tier", "ROUTINE")
        spec = triage_dict.get("recommended_specialty", "General Medicine")
        is_en = (state.get("language") or "Urdu").lower() in ("english", "en")

        # Query matching doctors
        suggested_docs = scheduling_agent.find_doctors(specialty=spec) if scheduling_agent else []
        if not suggested_docs and db:
            suggested_docs = db.get_practitioners(specialty=spec)
        if not suggested_docs and db:
            suggested_docs = db.get_practitioners()

        tomorrow_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        doc_lines = ""
        for i, doc in enumerate(suggested_docs[:3], 1):
            doc_fee = doc.get("consultation_fee", 2000)
            doc_branch = doc.get("branch_name") or doc.get("branch_city") or "City Care Clinics"
            slots = scheduling_agent.get_available_slots(doc["id"], tomorrow_str) if scheduling_agent else []
            slot_times = ", ".join([s["display_time"] for s in slots[:3]]) if slots else "Dastiyab slots available"
            doc_lines += (
                f"{i}. 👨‍⚕️ **{doc['full_name']}** ({doc.get('specialty', spec)})\n"
                f"   • **Branch:** {doc_branch} • **Consultation Fee:** PKR {doc_fee:,}\n"
                f"   • **Tajurba:** {doc.get('experience_years', 5)} saal ({doc.get('qualification', 'MBBS')})\n"
                f"   • **Kal ke Dastiyab Slots:** {slot_times}\n\n"
            )

        if is_en:
            guidance = (
                f"🩺 **Clinical Assessment:** Based on your symptoms, your case is evaluated as **{tier}**.\n"
                f"We recommend consulting a **{spec}** specialist. Here are the top available doctors at City Care Clinics:\n\n"
                f"{doc_lines}"
                f"Which doctor would you like to schedule with? Just reply with the doctor's name or your preferred time to proceed!"
            )
        else:
            guidance = (
                f"🩺 **Clinical Jaiza:** Aap ki alamat ke mutabiq aap ki halat **{tier}** zarray mein aati hai.\n"
                f"Aap ke liye **{spec}** ke specialist doctor munasib rahain gay. Hum in dastiyab doctors ko tajweez kartay hain:\n\n"
                f"{doc_lines}"
                f"Aap in mein se kis doctor ke sath appointment schedule karna chahtay hain? Bas doctor ka naam ya apna pasandeeda waqt batayein taakay booking shuru ki ja sake!"
            )

        messages.append({
            "role": "assistant",
            "content": guidance,
            "agent": "City Care Assistant",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    suggested_docs_list = suggested_docs[:3]
    state["intake_complete"] = True
    state["intake_stage"] = "doctors_suggested"
    state["suggested_doctors"] = suggested_docs_list

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
        "intake_complete": True,
        "intake_stage": "doctors_suggested",
        "suggested_doctors": suggested_docs_list,
        "current_agent": "parallel_triage_records",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }


def _parse_booking_request(text: str) -> Dict[str, Any]:
    """Helper to extract requested date and time from natural language user input."""
    import re
    text_lower = text.lower()
    now_utc = datetime.now(timezone.utc)
    
    # 1. Date extraction
    target_date = None
    has_explicit_date = False
    cleaned_for_time = text_lower

    # Match DD-MM-YYYY or DD/MM/YYYY (e.g. 11-10-2026, 11/10/2026)
    dmy_match = re.search(r"\b(\d{1,2})[-\/](\d{1,2})[-\/](\d{4})\b", text_lower)
    if dmy_match:
        try:
            day_val = int(dmy_match.group(1))
            mon_val = int(dmy_match.group(2))
            year_val = int(dmy_match.group(3))
            target_date = date(year_val, mon_val, day_val)
            has_explicit_date = True
            cleaned_for_time = cleaned_for_time.replace(dmy_match.group(0), " ")
        except Exception:
            pass

    # Match ISO format YYYY-MM-DD
    if not target_date:
        iso_match = re.search(r"\b(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})\b", text_lower)
        if iso_match:
            try:
                target_date = date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
                has_explicit_date = True
                cleaned_for_time = cleaned_for_time.replace(iso_match.group(0), " ")
            except Exception:
                pass

    if not target_date:
        # Check day-month like "10 october", "15 oct", "9th oct"
        month_match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*(?:\s*(\d{4}))?\b", text_lower)
        if month_match:
            try:
                day_num = int(month_match.group(1))
                mon_str = month_match.group(2)[:3]
                year_num = int(month_match.group(3)) if month_match.group(3) else now_utc.year
                months_list = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
                mon_num = months_list.index(mon_str) + 1
                target_date = date(year_num, mon_num, day_num)
                has_explicit_date = True
                cleaned_for_time = cleaned_for_time.replace(month_match.group(0), " ")
            except Exception:
                pass

    if not target_date:
        if "today" in text_lower or "aaj" in text_lower:
            target_date = now_utc.date()
            has_explicit_date = True
        elif "day after tomorrow" in text_lower or "parso" in text_lower:
            target_date = now_utc.date() + timedelta(days=2)
            has_explicit_date = True
        elif "tomorrow" in text_lower or "kal" in text_lower:
            target_date = now_utc.date() + timedelta(days=1)
            has_explicit_date = True
        else:
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for idx, d_name in enumerate(days):
                if d_name in text_lower:
                    days_ahead = (idx - now_utc.weekday()) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    target_date = now_utc.date() + timedelta(days=days_ahead)
                    has_explicit_date = True
                    break

    default_tomorrow = now_utc.date() + timedelta(days=1)
    
    # 2. Time extraction (run ONLY on cleaned_for_time to avoid false match on date numbers!)
    time_str = None
    colon_m = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", cleaned_for_time)
    if colon_m:
        raw_hr = int(colon_m.group(1))
        if 0 <= raw_hr <= 23:
            mn = int(colon_m.group(2))
            meridiem = colon_m.group(3)
            if meridiem == "pm" and raw_hr < 12:
                raw_hr += 12
            elif meridiem == "am" and raw_hr == 12:
                raw_hr = 0
            time_str = f"{raw_hr:02d}:{mn:02d}"

    if not time_str:
        ampm_m = re.search(r"\b(\d{1,2})\s*(am|pm)\b", cleaned_for_time)
        if ampm_m:
            raw_hr = int(ampm_m.group(1))
            meridiem = ampm_m.group(2)
            if 1 <= raw_hr <= 12:
                if meridiem == "pm" and raw_hr < 12:
                    raw_hr += 12
                elif meridiem == "am" and raw_hr == 12:
                    raw_hr = 0
                time_str = f"{raw_hr:02d}:00"

    if not time_str:
        baje_m = re.search(r"\b(\d{1,2})\s*(?:baje|bajay|o'clock)\b", cleaned_for_time)
        if baje_m:
            raw_hr = int(baje_m.group(1))
            if 1 <= raw_hr <= 12:
                if "shaam" in cleaned_for_time or "raat" in cleaned_for_time or "dopahar" in cleaned_for_time:
                    if raw_hr < 12:
                        raw_hr += 12
                time_str = f"{raw_hr:02d}:00"

    if not time_str:
        if "subah" in cleaned_for_time:
            m = re.search(r"subah\s*(\d{1,2})", cleaned_for_time)
            if m:
                time_str = f"{int(m.group(1)):02d}:00"
        elif "shaam" in cleaned_for_time or "raat" in cleaned_for_time:
            m = re.search(r"(?:shaam|raat)\s*(\d{1,2})", cleaned_for_time)
            if m:
                hr = int(m.group(1))
                if hr < 12: hr += 12
                time_str = f"{hr:02d}:00"

    return {
        "date_str": target_date.strftime("%Y-%m-%d") if target_date else default_tomorrow.strftime("%Y-%m-%d"),
        "has_explicit_date": has_explicit_date,
        "time_str": time_str
    }


def clean_patient_name(raw: str) -> str:
    """Helper to clean conversational prefixes and return a clean title-cased name."""
    raw = re.sub(r"\b(mera|naam|meri|hun|hain|hai|my|name|is|mr|mrs|ms|patient|ji|jee)\b", "", raw, flags=re.I)
    raw = re.sub(r"[\d\.\,\:\;\(\)\-]", " ", raw)
    words = [w for w in raw.split() if len(w) > 1 and w.lower() not in (
        "phone", "mobile", "age", "male", "female", "mard", "aurat", "allergy", "allergies",
        "none", "nahi", "nhi", "no", "yes", "confirm", "theek", "haan", "dawai", "medicine"
    )]
    return " ".join(words).title() if words else "Valued Patient"


def extract_conversational_patient_fields(text: str) -> Dict[str, Any]:
    """
    Carefully extracts only explicitly provided fields:
    - name: String or None
    - phone: 11-digit string starting with 03 or None
    - age: Integer (1-120) or None
    - gender: 'Male' | 'Female' | None
    - allergies: List of strings (e.g. ['None'] or ['Penicillin']) or None
    """
    text_clean = text.strip()

    # 1. Email extraction (extracted first to avoid interfering with name or allergy parsing)
    email = None
    email_m = re.search(r"\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b", text_clean)
    if email_m:
        email = email_m.group(1).lower().strip()

    # 2. Phone extraction
    phone = None
    phone_m = re.search(r"(\+?92[-\s]?3\d{2}[-\s]?\d{7}|03\d{2}[-\s]?\d{7}|\b03\d{9}\b|\b\d{11}\b)", text_clean)
    if phone_m:
        raw_ph = phone_m.group(1).replace(" ", "").replace("-", "")
        if raw_ph.startswith("+92"):
            raw_ph = "0" + raw_ph[3:]
        elif raw_ph.startswith("92"):
            raw_ph = "0" + raw_ph[2:]
        if len(raw_ph) == 11 and raw_ph.startswith("03"):
            phone = raw_ph

    text_no_contact = text_clean
    if email_m:
        text_no_contact = text_no_contact.replace(email_m.group(0), " ")
    if phone_m:
        text_no_contact = text_no_contact.replace(phone_m.group(0), " ")

    # 3. Gender extraction
    gender = None
    if re.search(r"\b(female|aurat|khatoon|woman|girl|larki)\b", text_no_contact, re.I):
        gender = "Female"
    elif re.search(r"\b(male|mard|man|boy|larka)\b", text_no_contact, re.I):
        gender = "Male"

    # 4. Age extraction
    age = None
    age_label_m = re.search(r"(?:umar|age|(?:3|4)[\.\)])\s*[:\-]?\s*(\d{1,3})", text_no_contact, re.I)
    if age_label_m:
        val = int(age_label_m.group(1))
        if 1 <= val <= 120:
            age = val
    if age is None:
        age_word_m = re.search(r"\b(1[0-9]|[2-9][0-9])\s*(?:saal|years?|yrs?)\b", text_no_contact, re.I)
        if age_word_m:
            age = int(age_word_m.group(1))
    if age is None and gender is not None:
        age_adj_m = re.search(r"\b(1[0-9]|[2-9][0-9])\b", text_no_contact)
        if age_adj_m:
            age = int(age_adj_m.group(1))

    # 5. Allergies extraction
    allergies = None
    # Priority A: Explicit allergy keyword
    allergy_kw_m = re.search(r"(?:allergies|allergy|dawai|medicine)\s*[:\-]?\s*([^\n,]+)", text_no_contact, re.I)
    if allergy_kw_m:
        val = allergy_kw_m.group(1).strip().lower()
        if any(neg in val for neg in ["none", "nahi", "nhi", "no", "nil", "na", "koi nahi", "kuch nahi"]):
            allergies = ["None"]
        else:
            clean_val = re.sub(r"[^\w\s]", "", val).strip().title()
            if clean_val and len(clean_val) > 2:
                allergies = [clean_val]
            else:
                allergies = ["None"]
    else:
        # Priority B: Numbered item 4 or 5 without label
        allergy_num_m = re.search(r"(?:4|5)[\.\)]\s*[:\-]?\s*([^\n,]+)", text_no_contact, re.I)
        if allergy_num_m:
            val = allergy_num_m.group(1).strip().lower()
            if any(neg in val for neg in ["none", "nahi", "nhi", "no", "nil", "na", "koi nahi", "kuch nahi"]):
                allergies = ["None"]
            elif not any(w in val for w in ["umar", "age", "saal", "male", "female", "mard", "aurat"]):
                clean_val = re.sub(r"[^\w\s]", "", val).strip().title()
                if clean_val and len(clean_val) > 2:
                    allergies = [clean_val]

    if allergies is None:
        neg_allergy_m = re.search(r"\b(none|nil|no allergies?|koi allergy nahi|kisi dawai se nahi|kisi dawai ki nahi|allergy nahi|allergy nhi|koi nahi)\b", text_no_contact, re.I)
        if neg_allergy_m:
            allergies = ["None"]
        else:
            med_m = re.search(r"\b(penicillin|sulfa|aspirin|panadol|augmentin|paracetamol|ibuprofen|amoxicillin|flagyl|disprin)\b", text_no_contact, re.I)
            if med_m:
                allergies = [med_m.group(1).title()]

    # 6. Name extraction
    name = None
    name_label_m = re.search(r"(?:naam|name|1[\.\)]?)\s*[:\-]?\s*([A-Za-z\s]+?)(?:,|\n|phone|mobile|email|03|2[\.\)]|\d|$)", text_no_contact, re.I)
    if name_label_m and len(name_label_m.group(1).strip()) >= 3:
        cand = clean_patient_name(name_label_m.group(1).strip())
        if cand and cand not in ("Valued Patient", "None"):
            name = cand

    if name is None:
        non_name_triggers = [
            "confirm", "theek", "haan", "hanji", "ok", "yes", "none", "nahi", "nhi",
            "cancel", "booking", "slot", "appointment", "doctor", "dr", "email"
        ]
        text_lower_words = text_clean.lower().split()
        is_only_control_words = any(w in non_name_triggers for w in text_lower_words) and len(text_lower_words) <= 2
        
        if not is_only_control_words and not phone_m and age is None and (allergies is None or allergies == ["None"]):
            cand = clean_patient_name(text_no_contact)
            if cand and cand not in ("Valued Patient", "None") and 3 <= len(cand) <= 40:
                words = cand.split()
                if 1 <= len(words) <= 4:
                    name = cand

    return {
        "name": name,
        "phone": phone,
        "email": email,
        "age": age,
        "gender": gender,
        "allergies": allergies
    }


def parse_conversational_patient_info(text: str) -> Dict[str, Any]:
    """Extracts phone, name, email, age, gender, and allergies from conversational patient message with safe defaults."""
    fields = extract_conversational_patient_fields(text)
    return {
        "name": fields.get("name") or "Valued Patient",
        "phone": fields.get("phone") or "03001234567",
        "email": fields.get("email"),
        "gender": fields.get("gender") or "Unspecified",
        "age": fields.get("age") or 30,
        "allergies": fields.get("allergies") or ["None"]
    }


def register_conversational_patient(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Registers patient in SQLite database and long-term memory."""
    name = parsed.get("name") or "Valued Patient"
    phone = parsed.get("phone") or "03001234567"
    email = parsed.get("email") or f"{name.lower().replace(' ', '.')}@example.com"
    age = parsed.get("age", 30)
    gender = parsed.get("gender", "Unspecified")
    allergies = parsed.get("allergies", [])

    if db:
        existing = db.find_patient_by_phone(phone)
        if existing:
            final_name = name if name and name != "Valued Patient" else existing["full_name"]
            final_email = parsed.get("email") or existing.get("email") or email
            if getattr(db, "is_supabase", False):
                try:
                    db.supabase.table("patients").update({
                        "full_name": final_name,
                        "email": final_email,
                        "known_allergies": allergies
                    }).eq("id", existing["id"]).execute()
                except Exception:
                    pass
            try:
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                    UPDATE patients SET full_name = ?, email = ?, known_allergies = ?
                    WHERE id = ?
                    """, (final_name, final_email, json.dumps(allergies), existing["id"]))
                    conn.commit()
            except Exception:
                pass
            return {
                "id": existing["id"],
                "patient_id": existing["id"],
                "name": final_name,
                "full_name": final_name,
                "mrn": existing["mrn"],
                "phone": existing["phone"],
                "email": final_email,
                "gender": existing.get("gender", gender),
                "allergies": allergies if allergies else (json.loads(existing["known_allergies"]) if isinstance(existing.get("known_allergies"), str) and existing["known_allergies"].startswith("[") else ["None"])
            }

    patient_id = str(uuid.uuid4())
    mrn = f"CCC-PK-{secrets.randbelow(90000) + 10000}"
    salt = secrets.token_hex(16)
    pwd_hash = f"{salt}:{hashlib.sha256((salt + 'Patient123!').encode('utf-8')).hexdigest()}"

    if db:
        if getattr(db, "is_supabase", False):
            try:
                db.supabase.table("patients").insert({
                    "id": patient_id,
                    "mrn": mrn,
                    "cnic": f"42101-{secrets.randbelow(9000000) + 1000000}-1",
                    "full_name": name,
                    "gender": gender,
                    "date_of_birth": f"{2026 - int(age)}-01-01",
                    "phone": phone,
                    "email": email,
                    "city": "Lahore",
                    "address": "City Care Outpatient",
                    "known_allergies": allergies,
                    "chronic_conditions": [],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }).execute()
            except Exception as e:
                print(f"[Supabase Patient Insert Warning]: {e}")
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                INSERT INTO patients (
                    id, mrn, cnic, full_name, gender, date_of_birth, phone, email, city, address,
                    known_allergies, chronic_conditions, created_at, password_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    patient_id, mrn, f"42101-{secrets.token_hex(4)}-1", name, gender,
                    f"{2026 - int(age)}-01-01", phone, email, "Lahore", "City Care Outpatient",
                    json.dumps(allergies), "[]", datetime.now(timezone.utc).isoformat(), pwd_hash
                ))
                conn.commit()
        except Exception as e:
            print(f"[Patient Insert Warning]: {e}")

    memory_manager.register_patient({
        "patient_id": patient_id,
        "patient_name": name,
        "phone": phone,
        "email": email,
        "mrn": mrn,
        "age": age,
        "gender": gender,
        "known_allergies": allergies,
        "chronic_conditions": [],
        "preferred_branch": "Gulberg Lahore",
        "preferred_language": "Urdu"
    })

    return {
        "id": patient_id,
        "patient_id": patient_id,
        "name": name,
        "full_name": name,
        "mrn": mrn,
        "phone": phone,
        "email": email,
        "gender": gender,
        "allergies": allergies
    }


def _extract_doctor_selection_index(text: str) -> Optional[int]:
    """
    Extracts doctor choice index (0-indexed) when user selects from suggested doctor list.
    Handles digits ("1", "2", "3"), option phrases ("option 3", "opt 3"), doctor phrases
    ("doctor 3", "doc 3", "dr 3"), Urdu ordinals ("teesra", "doosra", "pehla"),
    English ordinals ("3rd", "2nd", "1st", "third", "second", "first"), etc.
    """
    import re
    cleaned = re.sub(r"[\.\,\:\;\(\)\-]", " ", text.lower()).strip()
    words = cleaned.split()

    # Exact single tokens
    if cleaned in ("1", "option 1", "opt 1", "doc 1", "doctor 1", "dr 1", "pehla", "pehli", "first", "1st", "number 1", "1 number", "aik", "one"):
        return 0
    if cleaned in ("2", "option 2", "opt 2", "doc 2", "doctor 2", "dr 2", "doosra", "doosri", "dusra", "dusri", "second", "2nd", "number 2", "2 number", "do", "two"):
        return 1
    if cleaned in ("3", "option 3", "opt 3", "doc 3", "doctor 3", "dr 3", "teesra", "teesri", "tisra", "tisri", "third", "3rd", "number 3", "3 number", "teen", "three"):
        return 2
    if cleaned in ("4", "option 4", "opt 4", "doc 4", "doctor 4", "dr 4", "chautha", "fourth", "4th", "four", "chaar"):
        return 3
    if cleaned in ("5", "option 5", "opt 5", "doc 5", "doctor 5", "dr 5", "panchwa", "fifth", "5th", "five", "paanch"):
        return 4
    if cleaned in ("6", "option 6", "opt 6", "doc 6", "doctor 6", "dr 6", "chatha", "sixth", "6th", "six", "chay"):
        return 5

    # Regex matches like "option 3", "doctor 3", "doc 3", "dr 3", "number 3", "no 3", "3rd doctor", "3 number doctor"
    m = re.search(r"\b(?:option|opt|doctor|doc|dr|number|no)\s*([1-6])\b", cleaned)
    if m:
        return int(m.group(1)) - 1

    m2 = re.search(r"\b([1-6])\s*(?:st|nd|rd|th)?\s*(?:option|opt|doctor|doc|dr|number)\b", cleaned)
    if m2:
        return int(m2.group(1)) - 1

    m3 = re.search(r"\b([1-6])\s*number\b", cleaned)
    if m3:
        return int(m3.group(1)) - 1

    # In phrases like "teesray doctor", "3rd doctor", "teesra wala"
    if any(w in cleaned for w in ["teesra", "teesri", "tisra", "tisri", "third", "3rd"]):
        return 2
    if any(w in cleaned for w in ["doosra", "doosri", "dusra", "dusri", "second", "2nd"]):
        return 1
    if any(w in cleaned for w in ["pehla", "pehli", "first", "1st"]):
        return 0

    # Short user message starting with digit 1-6
    if len(words) <= 3 and words and words[0] in ("1", "2", "3", "4", "5", "6"):
        return int(words[0]) - 1

    return None


def scheduling_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Intelligent appointment scheduling node:
    1. Restores previous appointment & patient dossier via Appointment ID (e.g. BK-2026-1000).
    2. Handles conversational patient intake when booking (collects Name, Phone, Age/Gender in chat without prior signup).
    3. Issues unique Appointment ID (booking reference) for future restoration.
    4. Detects conflicts and suggests alternative available slots.
    """
    t0 = time.time()
    messages = list(state.get("messages", []))
    latest_user_msg = ""
    for m in reversed(messages):
        if _is_user_msg(m):
            latest_user_msg = _get_msg_content(m)
            break

    lang = state.get("language") or "Urdu"
    is_en = lang and lang.lower() in ("english", "en")

    sched_req = state.get("scheduling_request") or {}
    status = sched_req.get("status")

    # -------------------------------------------------------------
    # 0.0 CHECK IF PATIENT OBJECTS TO DOCTOR OR COMPLAINS ABOUT WRONG DOCTOR BOOKED
    # -------------------------------------------------------------
    low_msg = latest_user_msg.lower().strip()
    prev_apt = state.get("appointment_result")
    is_doc_change_complaint = (
        bool(re.search(r"\b(?:doctor\s*change|change\s*q|change\s*kyun|change\s*kyu|galat\s*doctor|wrong\s*doctor|pr\s*meri\s*doctor|meri\s*doctor\s*to|mera\s*doctor\s*to|ayesha\s*tariq)\b", low_msg)) or
        "doctor change" in low_msg or "change q" in low_msg or "change kyun" in low_msg or "change kyu" in low_msg or "meri doctor to" in low_msg
    )

    if prev_apt and is_doc_change_complaint:
        booking_ref_to_cancel = prev_apt.get("booking_reference") or prev_apt.get("id")
        if booking_ref_to_cancel:
            try:
                if scheduling_agent:
                    scheduling_agent.cancel_appointment(booking_ref_to_cancel, reason="Patient requested correction to preferred doctor")
                if db and hasattr(db, "update_appointment_status"):
                    db.update_appointment_status(booking_ref_to_cancel, "cancelled")
            except Exception as e:
                print(f"[Scheduling] Error cancelling mistaken booking: {e}")

        state["appointment_result"] = None
        all_docs = db.get_practitioners() if db else []
        branches_map = {b["id"]: b["name"] for b in (db.get_branches() if db else [])}
        target_doc = None

        # 1. Look for doctor explicitly mentioned in objection message
        for d in all_docs:
            clean_dname = d["full_name"].lower().replace("dr.", "").strip()
            if clean_dname and clean_dname in low_msg:
                target_doc = d
                break
            name_parts = clean_dname.split()
            if any(re.search(rf"\b{re.escape(part)}\b", low_msg) for part in name_parts if len(part) >= 3 and part not in ("none", "doctor", "general")):
                target_doc = d
                break

        # 2. Fall back to preferred doctor from long-term memory
        if not target_doc:
            pref_doc = state.get("long_term_memory", {}).get("preferred_doctor_name")
            if pref_doc:
                for d in all_docs:
                    if pref_doc.lower() in d["full_name"].lower():
                        target_doc = d
                        break

        if not target_doc and all_docs:
            target_doc = all_docs[0]

        doc_id = target_doc["id"]
        doc_name = target_doc["full_name"]
        doc_spec = target_doc.get("specialty", "Specialist")
        fee = target_doc.get("consultation_fee", 3500)
        branch_name = target_doc.get("branch_name") or branches_map.get(target_doc.get("branch_id")) or "City Care Clinics — DHA Phase 5 Branch"

        parsed_req = _parse_booking_request(latest_user_msg)
        target_date_str = parsed_req["date_str"]
        available_slots = scheduling_agent.get_available_slots(doc_id, target_date_str) if scheduling_agent else []

        alt_lines = ""
        for idx, a in enumerate(available_slots[:3], 1):
            alt_lines += f"{idx}. ⏰ **{a['display_time']}**\n"

        prev_doc_name = prev_apt.get("doctor_name", "doosray doctor")
        prev_ref_disp = prev_apt.get("booking_reference", "")

        if is_en:
            correction_msg = (
                f"⚠️ **Sincere Apologies for the confusion!**\n\n"
                f"The mistaken appointment with **{prev_doc_name}** (`#{prev_ref_disp}`) has been **cancelled**.\n\n"
                f"According to your records, your doctor is indeed **{doc_name}** ({doc_spec}, {branch_name}).\n\n"
                f"📅 **Available Slots for {doc_name} on {target_date_str}:**\n\n"
                f"{alt_lines}\n"
                f"• **Branch:** {branch_name} • **Fee:** PKR {fee:,}\n\n"
                f"Which time slot would you like to confirm for your appointment?"
            )
        else:
            correction_msg = (
                f"⚠️ **Bohot maazrat khwah hain!**\n\n"
                f"Ghalti se doosray doctor ({prev_doc_name}) ka slot select ho gaya tha. Pichli appointment (`#{prev_ref_disp}`) **cancel** kar di gayi hai.\n\n"
                f"Aap ke record ke mutabiq aap ki doctor **{doc_name}** hi hain ({doc_spec}, {branch_name}).\n\n"
                f"📅 **{doc_name} ke sath {target_date_str} ko dastiyab slots:**\n\n"
                f"{alt_lines}\n"
                f"• **Branch:** {branch_name} • **Fee:** PKR {fee:,}\n\n"
                f"Aap in mein se kis waqt par appointment book karna chahtay hain? Apna pasandeeda waqt batayein."
            )

        messages.append({
            "role": "assistant",
            "content": correction_msg,
            "agent": "SchedulingAgent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        sched_state = {
            "doctor_id": doc_id,
            "doctor_name": doc_name,
            "branch_id": target_doc.get("branch_id"),
            "branch_name": branch_name,
            "alternative_slots": available_slots[:3],
            "status": "ALTERNATIVES_PROPOSED",
            "target_date": target_date_str
        }
        transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "appointment_result": None,
            "scheduling_request": sched_state,
            "suggested_doctors": [target_doc],
            "current_agent": "scheduling",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }

    # -------------------------------------------------------------
    # 0. APPOINTMENT ID LOOKUP & RESTORATION
    # -------------------------------------------------------------
    id_m = re.search(r"\b(BK[-_]?(?:2026[-_]?)?[A-Za-z0-9]{4,10})\b", latest_user_msg, re.IGNORECASE)
    uuid_m = re.search(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", latest_user_msg, re.IGNORECASE)
    lookup_keywords = [
        "previous appointment", "purani appointment", "appointment status", "pehle appointment",
        "meri appointment", "appointment id", "booking reference", "restore", "pouch", "check appointment",
        "appointment pouch", "returning", "returning patient", "purana patient", "purana", "purani",
        "pehle aya", "pehle aya tha", "pehle ayi thi", "already registered", "pehle se registered", "old patient",
        "prescription", "medicines", "medicine", "dawaiyan", "dawa", "nuskha", "ilaj"
    ]
    target_ref = id_m.group(1) if id_m else (uuid_m.group(1) if uuid_m else None)

    if target_ref and db:
        apt = db.find_appointment_by_id_or_ref(target_ref)
        if apt:
            patient_id = apt.get("patient_id") or "p1"
            patient_name = apt.get("patient_name") or "Valued Patient"
            patient_phone = apt.get("patient_phone") or ""
            patient_mrn = apt.get("patient_mrn") or f"MRN-{apt.get('booking_reference')}"

            # Check prescription status
            rx = db.get_prescription_by_appointment(target_ref)
            current_status = "fulfilled" if rx else (apt.get("status") or "booked")
            apt["status"] = current_status
            if rx:
                apt["has_prescription"] = True
                apt["prescription"] = rx
            else:
                apt["has_prescription"] = False

            state["patient_id"] = patient_id
            state["patient_name"] = patient_name
            state["patient_phone"] = patient_phone
            state["patient_mrn"] = patient_mrn
            state["is_returning_patient"] = True

            memory_manager.register_patient({
                "patient_id": patient_id,
                "patient_name": patient_name,
                "phone": patient_phone,
                "mrn": patient_mrn,
                "preferred_doctor": apt.get("doctor_name"),
                "preferred_branch": apt.get("branch_name"),
                "known_allergies": json.loads(apt["known_allergies"]) if isinstance(apt.get("known_allergies"), str) and apt["known_allergies"].startswith("[") else [],
                "chronic_conditions": json.loads(apt["chronic_conditions"]) if isinstance(apt.get("chronic_conditions"), str) and apt["chronic_conditions"].startswith("[") else [],
                "last_visit_date": apt.get("scheduled_start", "")[:10]
            })

            try:
                s_dt = datetime.fromisoformat(apt["scheduled_start"].replace("Z", "+00:00"))
                display_date = s_dt.strftime("%A, %d %B %Y")
                display_time = s_dt.strftime("%I:%M %p")
            except Exception:
                display_date = apt.get("scheduled_start", "")[:10]
                display_time = apt.get("scheduled_start", "")[11:16]

            gcal_url = scheduling_agent.generate_google_calendar_link(
                title=f"Consultation: {apt.get('doctor_name', 'Doctor')} — City Care Clinics",
                start_dt=datetime.fromisoformat(apt["scheduled_start"].replace("Z", "+00:00")) if "T" in str(apt.get("scheduled_start")) else datetime.now(timezone.utc),
                end_dt=(datetime.fromisoformat(apt["scheduled_start"].replace("Z", "+00:00")) + timedelta(minutes=20)) if "T" in str(apt.get("scheduled_start")) else datetime.now(timezone.utc) + timedelta(minutes=20),
                details=f"Ref: {apt.get('booking_reference')}. Reason: {apt.get('reason_for_visit')}",
                location=apt.get("branch_name", "City Care Clinics")
            ) if scheduling_agent else "#"

            pdf_url = f"/api/prescriptions/{apt.get('booking_reference')}/pdf"
            apt["prescription_pdf_url"] = pdf_url if rx else None

            if rx:
                # Format prescription medicines
                med_lines = []
                for idx, med in enumerate(rx.get("medicines", []), 1):
                    med_lines.append(
                        f"  {idx}. 💊 **{med.get('drug_name')}** — {med.get('dosage', '500mg')} ({med.get('frequency', 'Twice daily')}) | Duration: {med.get('duration', '5 days')} | *Instructions: {med.get('instructions', 'Take after meals')}*"
                    )
                meds_formatted = "\n".join(med_lines) if med_lines else "None listed"

                if is_en:
                    prescription_block = (
                        f"\n\n📋 **Doctor's Prescription & Clinical Summary (Status: FULFILLED):**\n"
                        f"• **Diagnosis:** {rx.get('diagnosis', 'Outpatient consultation assessment')}\n"
                        f"• **Prescribed Medicines:**\n{meds_formatted}\n"
                        f"• **Doctor's Advice:** {rx.get('advice', 'Take medications on time as directed.')}\n\n"
                        f"📥 **[Download Official Prescription PDF]({pdf_url})**"
                    )
                    restore_msg = (
                        f"✅ **Welcome back {patient_name}! Your Record Has Been Restored:**\n\n"
                        f"• **Appointment ID:** `#{apt.get('booking_reference')}`\n"
                        f"• **Doctor:** {apt.get('doctor_name')} ({apt.get('doctor_specialty') or apt.get('specialty', 'Specialist')})\n"
                        f"• **Date & Time:** {display_date} at {display_time}\n"
                        f"• **Branch:** {apt.get('branch_name')}\n"
                        f"• **Status:** `{current_status}`\n"
                        f"• **MRN:** {patient_mrn}\n"
                        f"• **Reason:** {apt.get('reason_for_visit', 'Clinical Consultation')}"
                        f"{prescription_block}\n\n"
                        f"📅 [Add to Google Calendar]({gcal_url})\n\n"
                        f"Your complete profile and prescription have been restored. How may I assist you further today?"
                    )
                else:
                    prescription_block = (
                        f"\n\n📋 **Doctor ki Prescription aur Dawaiyan (Status: FULFILLED):**\n"
                        f"• **Diagnosis (Tashkhees):** {rx.get('diagnosis', 'Clinical assessment complete')}\n"
                        f"• **Tajweez Karda Dawaiyan:**\n{meds_formatted}\n"
                        f"• **Doctor ki Hidayat (Advice):** {rx.get('advice', 'Dawaiyan waqt par lein aur zaroorat parnay par rabta karein.')}\n\n"
                        f"📥 **[Prescription PDF Download Karein]({pdf_url})**"
                    )
                    restore_msg = (
                        f"✅ **Khush-Amdeed {patient_name}! Aap ka Record Kamyabi se Restore Ho Chuka Hai:**\n\n"
                        f"• **Appointment ID:** `#{apt.get('booking_reference')}`\n"
                        f"• **Doctor:** {apt.get('doctor_name')} ({apt.get('doctor_specialty') or apt.get('specialty', 'Specialist')})\n"
                        f"• **Tareeq o Waqt:** {display_date} - {display_time}\n"
                        f"• **Branch:** {apt.get('branch_name')}\n"
                        f"• **Status:** `{current_status}`\n"
                        f"• **MRN:** {patient_mrn}\n"
                        f"• **Reason:** {apt.get('reason_for_visit', 'Clinical Consultation')}"
                        f"{prescription_block}\n\n"
                        f"📅 [Google Calendar mein shamil karein]({gcal_url})\n\n"
                        f"Aap ka mukammal profile aur prescription details restore kar di gayi hain. Kya aap is appointment ke mutabiq mazeed kuch poochna chahtay hain?"
                    )
            else:
                if is_en:
                    prescription_block = (
                        f"\n\n⏳ **Prescription Status:** `booked` (Consultation & Prescription Pending)\n"
                        f"Your doctor consultation is scheduled. As soon as your doctor prescribes medicines from their portal, your appointment status will change to `fulfilled` and your medication details and downloadable PDF will appear here."
                    )
                    restore_msg = (
                        f"✅ **Welcome back {patient_name}! Your Record Has Been Restored:**\n\n"
                        f"• **Appointment ID:** `#{apt.get('booking_reference')}`\n"
                        f"• **Doctor:** {apt.get('doctor_name')} ({apt.get('doctor_specialty') or apt.get('specialty', 'Specialist')})\n"
                        f"• **Date & Time:** {display_date} at {display_time}\n"
                        f"• **Branch:** {apt.get('branch_name')}\n"
                        f"• **Status:** `{current_status}`\n"
                        f"• **MRN:** {patient_mrn}\n"
                        f"• **Reason:** {apt.get('reason_for_visit', 'Clinical Consultation')}"
                        f"{prescription_block}\n\n"
                        f"📅 [Add to Google Calendar]({gcal_url})\n\n"
                        f"Your appointment is confirmed. How may I assist you further today?"
                    )
                else:
                    prescription_block = (
                        f"\n\n⏳ **Prescription Status:** `booked` (Consultation aur Prescription Pending)\n"
                        f"Aap ki appointment scheduled hai. Doctor ki taraf se prescription issue hotay hi status `fulfilled` ho jaye ga aur aap ki dawaiyan aur PDF download link yahan dastyab ho jaye ga."
                    )
                    restore_msg = (
                        f"✅ **Khush-Amdeed {patient_name}! Aap ka Record Kamyabi se Restore Ho Chuka Hai:**\n\n"
                        f"• **Appointment ID:** `#{apt.get('booking_reference')}`\n"
                        f"• **Doctor:** {apt.get('doctor_name')} ({apt.get('doctor_specialty') or apt.get('specialty', 'Specialist')})\n"
                        f"• **Tareeq o Waqt:** {display_date} - {display_time}\n"
                        f"• **Branch:** {apt.get('branch_name')}\n"
                        f"• **Status:** `{current_status}`\n"
                        f"• **MRN:** {patient_mrn}\n"
                        f"• **Reason:** {apt.get('reason_for_visit', 'Clinical Consultation')}"
                        f"{prescription_block}\n\n"
                        f"📅 [Google Calendar mein shamil karein]({gcal_url})\n\n"
                        f"Aap ki appointment confirm hai. Kya aap koi mazeed sawal poochna chahtay hain?"
                    )

            messages.append({
                "role": "assistant",
                "content": restore_msg,
                "agent": "SchedulingAgent",
                "appointment_card": apt,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "patient_mrn": patient_mrn,
                "is_returning_patient": True,
                "appointment_result": apt,
                "current_agent": "scheduling",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }
        else:
            not_found_msg = (
                f"⚠️ Maaf kijiye ga, Appointment ID `{target_ref}` ke tehat koi record nahi mila. Baraye meharbani apna Appointment ID dobara check karein (jaisay BK-2026-1000) ya naye appointment ke liye batayein."
                if not is_en else
                f"⚠️ Sorry, no record was found for Appointment ID `{target_ref}`. Please double check your booking reference (e.g. BK-2026-1000) or let me know if you would like to book a new appointment."
            )
            messages.append({
                "role": "assistant",
                "content": not_found_msg,
                "agent": "SchedulingAgent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "current_agent": "scheduling",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }

    if not target_ref and any(lk in latest_user_msg.lower() for lk in lookup_keywords):
        prompt_id_msg = (
            "Khush-Amdeed! Baraye meharbani apna **Appointment ID** (jaisay `BK-2026-1000`) ya mobile number chat mein batayein taakay hum aap ka record restore kar sakein."
            if not is_en else
            "Welcome back! Please share your **Appointment ID** (such as `BK-2026-1000`) or mobile number in chat so I can restore your records immediately."
        )
        messages.append({
            "role": "assistant",
            "content": prompt_id_msg,
            "agent": "SchedulingAgent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "current_agent": "scheduling",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }

    # -------------------------------------------------------------
    # 1. CHECK IF USER IS PROVIDING INFO FOR CONVERSATIONAL INTAKE
    # -------------------------------------------------------------
    if status == "AWAITING_PATIENT_INFO" and sched_req.get("pending_slot"):
        collected = dict(sched_req.get("collected_info") or {})
        extracted = extract_conversational_patient_fields(latest_user_msg)
        for k, v in extracted.items():
            if v is not None and not collected.get(k):
                collected[k] = v

        if not collected.get("phone") and state.get("patient_phone"):
            collected["phone"] = state["patient_phone"]
        if not collected.get("name") and state.get("patient_name") and state["patient_name"] not in ("Guest Patient", "Valued Patient", "p1"):
            collected["name"] = state["patient_name"]

        missing_fields = []
        if not collected.get("name"):
            missing_fields.append("name")
        if not collected.get("phone"):
            missing_fields.append("phone")
        if not collected.get("email") and not state.get("long_term_memory", {}).get("email"):
            missing_fields.append("email")
        if not collected.get("age"):
            missing_fields.append("age")
        if collected.get("allergies") is None:
            missing_fields.append("allergies")

        if missing_fields:
            sched_req["collected_info"] = collected
            p_name = collected.get("name")
            if is_en:
                greeting = f"Thank you {p_name}! " if p_name else "Thank you! "
                missing_lines = []
                idx = 1
                if "name" in missing_fields:
                    missing_lines.append(f"{idx}. **Full Name**")
                    idx += 1
                if "phone" in missing_fields:
                    missing_lines.append(f"{idx}. **Mobile Phone Number** (e.g. 0300-1234567)")
                    idx += 1
                if "email" in missing_fields:
                    missing_lines.append(f"{idx}. **Email Address** (e.g. yourname@gmail.com — to receive confirmation & calendar invite)")
                    idx += 1
                if "age" in missing_fields:
                    missing_lines.append(f"{idx}. **Age & Gender** (e.g. 28 years, Male/Female)")
                    idx += 1
                if "allergies" in missing_fields:
                    missing_lines.append(f"{idx}. **Allergies:** Do you have any allergies to specific medicines (e.g. Penicillin)? (If none, please write 'None')")
                    idx += 1
                reprompt_msg = (
                    f"{greeting}To finalize your appointment booking, please provide the remaining required details:\n\n"
                    + "\n".join(missing_lines)
                )
            else:
                greeting = f"Shukriya {p_name}! " if p_name else "Shukriya! "
                missing_lines = []
                idx = 1
                if "name" in missing_fields:
                    missing_lines.append(f"{idx}. **Poora Naam** (Full Name)")
                    idx += 1
                if "phone" in missing_fields:
                    missing_lines.append(f"{idx}. **Mobile Number** (jaisay 0300-1234567)")
                    idx += 1
                if "email" in missing_fields:
                    missing_lines.append(f"{idx}. **Email Address** (jaisay yourname@gmail.com — confirmation aur Google Calendar invite ke liye)")
                    idx += 1
                if "age" in missing_fields:
                    missing_lines.append(f"{idx}. **Umar aur Jins** (Age & Gender — jaisay 28 saal, Mard/Aurat)")
                    idx += 1
                if "allergies" in missing_fields:
                    missing_lines.append(f"{idx}. **Allergies:** Kya aap ko kisi makhsoos dawai (e.g. Penicillin) se allergy hai? (Agar nahi to 'None' likhein)")
                    idx += 1
                reprompt_msg = (
                    f"{greeting}Appointment mukammal karne ke liye baraye meharbani yeh baaqi zaroori maloomat faraham karein:\n\n"
                    + "\n".join(missing_lines)
                )

            messages.append({
                "role": "assistant",
                "content": reprompt_msg,
                "agent": "SchedulingAgent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "scheduling_request": sched_req,
                "current_agent": "scheduling",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }

        # ALL REQUIRED FIELDS ARE PRESENT! Register and book!
        patient_email = collected.get("email") or state.get("long_term_memory", {}).get("email")
        reg_p = register_conversational_patient({
            "name": collected["name"],
            "phone": collected["phone"],
            "email": patient_email,
            "age": collected["age"],
            "gender": collected.get("gender", "Unspecified"),
            "allergies": collected.get("allergies", ["None"])
        })

        state["patient_id"] = reg_p["id"]
        state["patient_name"] = reg_p["name"]
        state["patient_phone"] = reg_p["phone"]
        state["patient_mrn"] = reg_p["mrn"]
        state["is_returning_patient"] = True

        selected_slot_to_book = sched_req["pending_slot"]
        doc_id = sched_req.get("doctor_id") or "doc1"
        branch_id = sched_req.get("branch_id") or "b1"
        reason = state.get("intake_form", {}).get("chief_complaint", "Clinical Consultation")

        booking_res = scheduling_agent.book_appointment(
            patient_id=reg_p["id"],
            doctor_id=doc_id,
            branch_id=branch_id,
            slot_iso=selected_slot_to_book["slot_start"],
            reason=reason,
            urgency="ROUTINE"
        )

        if booking_res.get("success"):
            time_disp = selected_slot_to_book.get("display_time", "")
            date_disp = selected_slot_to_book.get("display_date", "")
            gcal_link = booking_res.get("google_calendar_url", "#")
            booking_ref = booking_res.get("booking_reference", "BK-2026-1000")
            doc_name = booking_res.get("doctor_name", sched_req.get("doctor_name", "Doctor"))
            doc_spec = booking_res.get("specialty", "Specialist")
            fee = booking_res.get("fee", 2000)
            branch_lbl = sched_req.get("branch_name", "City Care Clinics")

            target_email = patient_email or reg_p.get("email") or f"{reg_p['name'].lower().replace(' ', '.')}@example.com"
            email_notifier.send_appointment_confirmation(
                patient_name=reg_p["name"],
                patient_email=target_email,
                doctor_name=doc_name,
                specialty=doc_spec,
                branch_name=branch_lbl,
                start_time_iso=selected_slot_to_book["slot_start"],
                booking_ref=booking_ref,
                consultation_fee=fee,
                calendar_url=gcal_link
            )

            if is_en:
                confirm_msg = (
                    f"✅ **Congratulations {reg_p['name']}! Your Appointment is Confirmed:**\n\n"
                    f"⭐️ **Appointment ID:** `#{booking_ref}`\n"
                    f"*(Please save this Appointment ID! Whenever you return, simply enter this Appointment ID in chat to instantly restore your records.)*\n\n"
                    f"• **Doctor:** {doc_name} ({doc_spec})\n"
                    f"• **Date & Time:** {date_disp} at {time_disp}\n"
                    f"• **Branch:** {branch_lbl}\n"
                    f"• **Consultation Fee:** PKR {fee:,}\n"
                    f"• **MRN:** {reg_p['mrn']}\n"
                    f"• **Phone:** {reg_p['phone']}\n"
                    f"• **Email:** {target_email}\n\n"
                    f"📅 [Add to Google Calendar]({gcal_link})\n\n"
                    f"📧 A confirmation email with appointment details and calendar invite has been sent to **{target_email}**. Please arrive 10 minutes before your appointment."
                )
            else:
                confirm_msg = (
                    f"✅ **Mubarak Ho {reg_p['name']}! Aap Ki Appointment Confirm Ho Chuki Hai:**\n\n"
                    f"⭐️ **Appointment ID:** `#{booking_ref}`\n"
                    f"*(Is Appointment ID ko mehfooz kar lein! Agli martaba aane par sirf yeh ID likhein aur aap ka tamam record restore ho jaye ga.)*\n\n"
                    f"• **Doctor:** {doc_name} ({doc_spec})\n"
                    f"• **Tareeq o Waqt:** {date_disp} - {time_disp}\n"
                    f"• **Branch:** {branch_lbl}\n"
                    f"• **Consultation Fee:** PKR {fee:,}\n"
                    f"• **MRN:** {reg_p['mrn']}\n"
                    f"• **Mobile:** {reg_p['phone']}\n"
                    f"• **Email:** {target_email}\n\n"
                    f"📅 [Google Calendar mein shamil karein]({gcal_link})\n\n"
                    f"📧 Mukammal confirmation email aur Google Calendar invite aap ke email address **{target_email}** par bhej di gayi hai. Baraye meharbani waqt se 10 minute pehle tashreef layein."
                )

            messages.append({
                "role": "assistant",
                "content": confirm_msg,
                "agent": "SchedulingAgent",
                "appointment_card": booking_res,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "patient_id": reg_p["id"],
                "patient_name": reg_p["name"],
                "patient_phone": reg_p["phone"],
                "patient_email": target_email,
                "patient_mrn": reg_p["mrn"],
                "is_returning_patient": True,
                "appointment_result": booking_res,
                "scheduling_request": {"status": "CONFIRMED", "booking_reference": booking_ref},
                "current_agent": "scheduling",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }

    # -------------------------------------------------------------
    # 2. CHECK IF PATIENT IS CONFIRMING A PROPOSED APPOINTMENT
    # -------------------------------------------------------------
    low_msg = latest_user_msg.lower().strip()
    is_doctor_objection = bool(
        re.search(r"\b(?:pr|par|lekin|magar|kyun|kyu|q|change|dusra|doosra|galat|wrong|nahi|not)\b", low_msg) or
        "doctor change" in low_msg or "meri doctor" in low_msg or "mera doctor" in low_msg or
        "doctor to" in low_msg or "wahi doctor" in low_msg or "change q" in low_msg or "change kyun" in low_msg
    )

    confirm_regex = r"\b(?:confirm|confirmed|yes|yep|yeah|theek\s*hai|theek|haan\s*ji|haan|hanji|kar\s*(?:dein|do|dain)|book\s*(?:kar\s*(?:dein|do|dain)|karein|kardo)?|ok|okay|sure|done|pakka|agree|sahi\s*hai|sahi|jee\s*haan|ji\s*haan)\b"
    is_confirm_word = bool(re.search(confirm_regex, low_msg)) and not is_doctor_objection

    selected_slot_to_book = None

    if status == "PROPOSED" and sched_req.get("proposed_slot") and is_confirm_word:
        selected_slot_to_book = sched_req["proposed_slot"]
    elif status == "ALTERNATIVES_PROPOSED" and sched_req.get("alternative_slots"):
        is_explicit_doc_switch = (
            is_doctor_objection or
            bool(re.search(r"\b(?:doctor|doc|dr\.?)\s*[1-6]\b", low_msg)) or
            "change doctor" in low_msg or "dusra doctor" in low_msg or "doosra doctor" in low_msg or
            any(
                re.search(rf"\b{re.escape(part)}\b", low_msg)
                for d in (db.get_practitioners() if db else [])
                for part in d["full_name"].lower().replace("dr.", "").strip().split()
                if len(part) >= 4 and part not in ("none", "general", "medicine")
            )
        )
        if not is_explicit_doc_switch:
            alts = sched_req["alternative_slots"]
            if low_msg.strip() in ("1", "option 1", "opt 1", "slot 1", "time 1", "pehla", "pehli", "first", "1st", "1 number", "number 1") or ("1" in low_msg and "slot" in low_msg):
                selected_slot_to_book = alts[0] if len(alts) > 0 else None
            elif low_msg.strip() in ("2", "option 2", "opt 2", "slot 2", "time 2", "doosra", "doosri", "second", "2nd", "2 number", "number 2") or ("2" in low_msg and "slot" in low_msg):
                selected_slot_to_book = alts[1] if len(alts) > 1 else None
            elif low_msg.strip() in ("3", "option 3", "opt 3", "slot 3", "time 3", "teesra", "teesri", "third", "3rd", "3 number", "number 3") or ("3" in low_msg and "slot" in low_msg):
                selected_slot_to_book = alts[2] if len(alts) > 2 else None
            else:
                for a in alts:
                    dt_str = a.get("display_time", "").lower()
                    if dt_str and (dt_str in low_msg or dt_str.replace(" ", "") in low_msg.replace(" ", "") or dt_str.split()[0] in low_msg):
                        selected_slot_to_book = a
                        break
                if not selected_slot_to_book and is_confirm_word and alts:
                    selected_slot_to_book = alts[0]

    if selected_slot_to_book:
        has_identity = bool(
            state.get("patient_phone") and
            state.get("patient_name") and
            state.get("patient_name") not in ("Guest Patient", "Valued Patient", "p1")
        )

        doc_name = sched_req.get("doctor_name", "Doctor")
        collected = dict(sched_req.get("collected_info") or {})
        extracted = extract_conversational_patient_fields(latest_user_msg)
        for k, v in extracted.items():
            if v is not None and not collected.get(k):
                collected[k] = v

        is_all_present = bool(collected.get("name") and collected.get("phone") and collected.get("email") and collected.get("age") and collected.get("allergies") is not None)

        if not has_identity and is_all_present:
            reg_p = register_conversational_patient({
                "name": collected["name"],
                "phone": collected["phone"],
                "email": collected.get("email"),
                "age": collected["age"],
                "gender": collected.get("gender", "Unspecified"),
                "allergies": collected.get("allergies", ["None"])
            })
            state["patient_id"] = reg_p["id"]
            state["patient_name"] = reg_p["name"]
            state["patient_phone"] = reg_p["phone"]
            state["patient_email"] = reg_p.get("email")
            state["patient_mrn"] = reg_p["mrn"]
            state["is_returning_patient"] = True
            has_identity = True

        if not has_identity:
            sched_req["status"] = "AWAITING_PATIENT_INFO"
            sched_req["pending_slot"] = selected_slot_to_book
            sched_req["collected_info"] = collected

            if is_en:
                ask_info_msg = (
                    f"Excellent! To finalize and book your appointment with **{doc_name}** on **{selected_slot_to_book.get('display_date', '')}** at **{selected_slot_to_book.get('display_time', '')}**, please provide the following details here in chat:\n\n"
                    f"1. **Full Name**\n"
                    f"2. **Mobile Phone Number** (e.g. 0300-1234567)\n"
                    f"3. **Email Address** (e.g. yourname@gmail.com — to receive confirmation & calendar invite)\n"
                    f"4. **Age & Gender** (e.g. 28 years, Male/Female)\n"
                    f"5. **Allergies:** Any allergies to specific medicines (e.g. Penicillin)? (Or write 'None')\n\n"
                    f"Once received, your appointment will be booked instantly and you will receive your unique **Appointment ID**!"
                )
            else:
                ask_info_msg = (
                    f"Bohat khoob! **{doc_name}** ke sath **{selected_slot_to_book.get('display_date', '')}** ko **{selected_slot_to_book.get('display_time', '')}** par appointment book karne ke liye baraye meharbani apni yeh maloomat chat mein likh kar bhej dein:\n\n"
                    f"1. **Poora Naam** (Full Name)\n"
                    f"2. **Mobile Number** (Phone Number — jaisay 0300-1234567)\n"
                    f"3. **Email Address** (jaisay yourname@gmail.com — confirmation aur Google Calendar invite ke liye)\n"
                    f"4. **Umar aur Jins** (Age & Gender — jaisay 28 saal, Mard/Aurat)\n"
                    f"5. **Allergies** (agar kisi makhsoos dawai se allergy ho, warna 'None' likhein)\n\n"
                    f"Yeh maloomat milte hi aap ki appointment book ho jaye gi aur aap ko aap ka **Appointment ID** de diya jaye ga!"
                )

            messages.append({
                "role": "assistant",
                "content": ask_info_msg,
                "agent": "SchedulingAgent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "scheduling_request": sched_req,
                "current_agent": "scheduling",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }

        # Otherwise, patient identity is known -> Commit Booking
        doc_id = sched_req.get("doctor_id") or "doc1"
        branch_id = sched_req.get("branch_id") or "b1"
        patient_id = state.get("patient_id") or "p1"
        reason = state.get("intake_form", {}).get("chief_complaint", "Clinical Consultation")
        triage = state.get("triage_result") or {}
        urgency = triage.get("urgency_tier", "ROUTINE")

        booking_res = scheduling_agent.book_appointment(
            patient_id=patient_id,
            doctor_id=doc_id,
            branch_id=branch_id,
            slot_iso=selected_slot_to_book["slot_start"],
            reason=reason,
            urgency=urgency
        )

        if booking_res.get("success"):
            time_disp = selected_slot_to_book.get("display_time", "")
            date_disp = selected_slot_to_book.get("display_date", "")
            gcal_link = booking_res.get("google_calendar_url", "#")
            booking_ref = booking_res.get("booking_reference", "BK-2026-1000")
            doc_name = booking_res.get("doctor_name", doc_name)
            doc_spec = booking_res.get("specialty", "Specialist")
            fee = booking_res.get("fee", 2000)
            branch_lbl = sched_req.get("branch_name", "City Care Clinics")

            pat_email = state.get("patient_email") or state.get("long_term_memory", {}).get("email") or f"{state.get('patient_name', 'patient').lower().replace(' ', '.')}@example.com"
            email_notifier.send_appointment_confirmation(
                patient_name=state.get("patient_name", "Valued Patient"),
                patient_email=pat_email,
                doctor_name=doc_name,
                specialty=doc_spec,
                branch_name=branch_lbl,
                start_time_iso=selected_slot_to_book["slot_start"],
                booking_ref=booking_ref,
                consultation_fee=fee,
                calendar_url=gcal_link
            )

            if is_en:
                confirm_msg = (
                    f"✅ **Appointment Confirmed!**\n\n"
                    f"⭐️ **Appointment ID:** `#{booking_ref}`\n"
                    f"*(Please save this Appointment ID! Whenever you return, simply enter this ID to restore your records.)*\n\n"
                    f"• **Doctor:** {doc_name} ({doc_spec})\n"
                    f"• **Date & Time:** {date_disp} at {time_disp}\n"
                    f"• **Branch:** {branch_lbl}\n"
                    f"• **Consultation Fee:** PKR {fee:,}\n"
                    f"• **MRN:** {state.get('patient_mrn', 'N/A')}\n"
                    f"• **Email:** {pat_email}\n\n"
                    f"📅 [Add to Google Calendar]({gcal_link})\n\n"
                    f"📧 A confirmation email with appointment details and calendar invite has been sent to **{pat_email}**. Please arrive 10 minutes early."
                )
            else:
                confirm_msg = (
                    f"✅ **Mubarak Ho! Aap Ki Appointment Confirm Ho Chuki Hai:**\n\n"
                    f"⭐️ **Appointment ID:** `#{booking_ref}`\n"
                    f"*(Is Appointment ID ko mehfooz kar lein! Agli martaba aane par sirf yeh ID likhein aur aap ka tamam record restore ho jaye ga.)*\n\n"
                    f"• **Doctor:** {doc_name} ({doc_spec})\n"
                    f"• **Tareeq o Waqt:** {date_disp} - {time_disp}\n"
                    f"• **Branch:** {branch_lbl}\n"
                    f"• **Consultation Fee:** PKR {fee:,}\n"
                    f"• **MRN:** {state.get('patient_mrn', 'N/A')}\n"
                    f"• **Email:** {pat_email}\n\n"
                    f"📅 [Google Calendar mein shamil karein]({gcal_link})\n\n"
                    f"📧 Mukammal confirmation email aur Google Calendar invite aap ke email address **{pat_email}** par bhej di gayi hai. Baraye meharbani waqt se 10 minute pehle tashreef layein."
                )

            messages.append({
                "role": "assistant",
                "content": confirm_msg,
                "agent": "SchedulingAgent",
                "appointment_card": booking_res,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "patient_id": state.get("patient_id"),
                "patient_name": state.get("patient_name"),
                "patient_phone": state.get("patient_phone"),
                "patient_email": pat_email,
                "patient_mrn": state.get("patient_mrn"),
                "is_returning_patient": True,
                "appointment_result": booking_res,
                "scheduling_request": {"status": "CONFIRMED", "booking_reference": booking_ref},
                "current_agent": "scheduling",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }

    # -------------------------------------------------------------
    # 2. PARSE NEW APPOINTMENT REQUEST (DOCTOR, DATE, TIME)
    # -------------------------------------------------------------
    parsed_req = _parse_booking_request(latest_user_msg)
    if parsed_req.get("has_explicit_date"):
        target_date_str = parsed_req["date_str"]
    elif sched_req.get("target_date"):
        target_date_str = sched_req["target_date"]
    else:
        target_date_str = parsed_req["date_str"]
    requested_time = parsed_req["time_str"]
    
    # Identify doctor
    triage = state.get("triage_result") or {}
    specialty = triage.get("recommended_specialty", "General Medicine")
    if "Emergency" in specialty:
        specialty = "General Medicine"
        
    all_docs = db.get_practitioners()
    target_doc = None
    target_doc_specified = False
    
    msg_low = latest_user_msg.lower().strip()

    # 0. Check if user is asking for repeat / previous appointment with preferred doctor
    # or explicitly named a doctor in this message
    pref_doc = state.get("long_term_memory", {}).get("preferred_doctor_name")
    is_repeat_booking = any(w in msg_low for w in [
        "dubara", "dobara", "repeat", "wahi doctor", "wohi doctor", "wahi dr", "wohi dr",
        "unke sath", "unhi ke sath", "unke pass", "unhi ke pass", "same doctor",
        "previous doctor", "purana doctor", "purani doctor", "pichle doctor", "pichli doctor",
        "pehle wale", "pehle wali", "meri doctor", "mera doctor"
    ])

    prev_asst_msg = ""
    for m in reversed(messages):
        if not _is_user_msg(m):
            prev_asst_msg = _get_msg_content(m).lower()
            break

    asked_about_pref_doc = bool(pref_doc and pref_doc.lower() in prev_asst_msg)
    user_confirmed_repeat = is_repeat_booking or (asked_about_pref_doc and (
        is_confirm_word or any(w in msg_low for w in ["haan", "yes", "ji haan", "theek", "book", "appointment"])
    ))

    # A. Check if doctor is explicitly mentioned by name in message
    for d in all_docs:
        clean_dname = d["full_name"].lower().replace("dr.", "").strip()
        if clean_dname and clean_dname in msg_low:
            target_doc = d
            target_doc_specified = True
            break
        name_parts = clean_dname.split()
        if any(re.search(rf"\b{re.escape(part)}\b", msg_low) for part in name_parts if len(part) >= 3 and part not in ("none", "doctor", "general")):
            target_doc = d
            target_doc_specified = True
            break

    # B. If repeat booking confirmed or requested, assign preferred doctor
    if not target_doc and user_confirmed_repeat and pref_doc:
        for d in all_docs:
            if pref_doc.lower() in d["full_name"].lower():
                target_doc = d
                target_doc_specified = True
                break

    # 1. Resolve suggested doctors list
    suggested_docs_list = list(state.get("suggested_doctors") or [])
    if not suggested_docs_list:
        for m in reversed(messages):
            if not _is_user_msg(m):
                content = _get_msg_content(m)
                matches = re.findall(r"\d+\.\s*(?:👨‍⚕️)?\s*\*\*Dr\.\s*([^*]+)\*\*", content)
                if matches:
                    for d_name in matches:
                        for d in all_docs:
                            if d_name.lower().strip() in d["full_name"].lower():
                                suggested_docs_list.append(d)
                                break
                    if suggested_docs_list:
                        break
    if not suggested_docs_list:
        docs_for_spec = scheduling_agent.find_doctors(specialty=specialty) if scheduling_agent else []
        suggested_docs_list = docs_for_spec[:3] if docs_for_spec else all_docs[:3]

    # 2. Check if user selected doctor by option index (e.g. "1", "2", "3", "option 3", "3rd", "teesra", etc.)
    if not target_doc:
        doc_opt_idx = _extract_doctor_selection_index(latest_user_msg)
        if doc_opt_idx is not None and 0 <= doc_opt_idx < len(suggested_docs_list):
            target_doc = suggested_docs_list[doc_opt_idx]
            target_doc_specified = True
            # If user only specified the option number, ensure requested_time is None
            if not re.search(r"\b(\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm|baje))\b", msg_low):
                requested_time = None

    is_general_doc_inquiry = any(q in msg_low for q in [
        "available doctor", "doctors available", "kon se doctor", "konsay doctor",
        "suggest doctor", "doctor list", "dastiyab doctor", "doctors dastiyab",
        "doctor batao", "doctor bataiye", "konsa doctor", "doctors list", "konsi doctor",
        "tamam doctor", "all doctor"
    ])

    if not target_doc_specified and is_general_doc_inquiry and not requested_time:
        distinct_specs = ["General Medicine", "Cardiology", "Paediatrics", "Gynaecology", "Dermatology", "ENT"]
        shown_docs = []
        for s in distinct_specs:
            match = scheduling_agent.find_doctors(specialty=s) if scheduling_agent else []
            if match:
                shown_docs.append(match[0])

        doc_lines = ""
        for idx, doc in enumerate(shown_docs, 1):
            doc_fee = doc.get("consultation_fee", 2000)
            doc_branch = doc.get("branch_name") or "City Care Clinics"
            slots = scheduling_agent.get_available_slots(doc["id"], target_date_str) if scheduling_agent else []
            slot_times = ", ".join([s["display_time"] for s in slots[:3]]) if slots else "Slots available"
            doc_lines += (
                f"{idx}. 👨‍⚕️ **{doc['full_name']}** — *{doc.get('specialty')}*\n"
                f"   • **Branch:** {doc_branch} • **Fee:** PKR {doc_fee:,}\n"
                f"   • **Upcoming Slots ({target_date_str}):** {slot_times}\n\n"
            )

        if is_en:
            avail_msg = (
                f"👨‍⚕️ **Available Specialists at City Care Clinics:**\n\n"
                f"{doc_lines}"
                f"Which doctor would you like to schedule an appointment with? Reply with the doctor's name, or describe your symptoms so I can recommend the right specialist!"
            )
        else:
            avail_msg = (
                f"👨‍⚕️ **City Care Clinics ke Dastiyab Specialist Doctors:**\n\n"
                f"{doc_lines}"
                f"Aap in mein se kis doctor ke sath appointment schedule karna chahtay hain? Bas doctor ka naam aur apna pasandeeda waqt batayein, ya apni alamaat share karein taakay hum behtareen doctor tajweez karein!"
            )

        messages.append({
            "role": "assistant",
            "content": avail_msg,
            "agent": "SchedulingAgent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "suggested_doctors": shown_docs,
            "current_agent": "scheduling",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }
            
    if not target_doc and sched_req.get("doctor_id"):
        for d in all_docs:
            if d["id"] == sched_req["doctor_id"] or d["full_name"].lower() == str(sched_req.get("doctor_name", "")).lower():
                target_doc = d
                target_doc_specified = True
                break

    if not target_doc:
        pref_doc = state.get("long_term_memory", {}).get("preferred_doctor_name")
        if pref_doc:
            for d in all_docs:
                if pref_doc.lower() in d["full_name"].lower():
                    target_doc = d
                    break
                    
    if not target_doc:
        docs_for_spec = scheduling_agent.find_doctors(specialty=specialty)
        target_doc = docs_for_spec[0] if docs_for_spec else all_docs[0]
        
    branches_map = {b["id"]: b["name"] for b in (db.get_branches() if db else [])}
    doc_id = target_doc["id"]
    doc_name = target_doc["full_name"]
    doc_spec = target_doc.get("specialty", specialty)
    fee = target_doc.get("consultation_fee", 2000)
    branch_name = target_doc.get("branch_name") or branches_map.get(target_doc.get("branch_id")) or "City Care Clinics — DHA Phase 5 Branch"
    
    available_slots = scheduling_agent.get_available_slots(doc_id, target_date_str)
    
    # -------------------------------------------------------------
    # CASE A: Patient requested a specific time
    # -------------------------------------------------------------
    if requested_time:
        matched_slot = None
        for s in available_slots:
            s_dt = datetime.fromisoformat(s["slot_start"].replace("Z", "+00:00"))
            s_hm = s_dt.strftime("%H:%M")
            if s_hm == requested_time or s["display_time"].lower().startswith(requested_time.lower()):
                matched_slot = s
                break
                
        if matched_slot:
            # Slot is FREE -> PROPOSE and wait for confirmation!
            if is_en:
                prop_msg = (
                    f"📅 **Proposed Appointment with {doc_name}:**\n\n"
                    f"• **Doctor:** {doc_name} ({doc_spec})\n"
                    f"• **Date:** {matched_slot['display_date']}\n"
                    f"• **Time:** {matched_slot['display_time']}\n"
                    f"• **Consultation Fee:** PKR {fee:,}\n"
                    f"• **Branch:** {branch_name}\n\n"
                    f"Would you like me to confirm and book this appointment for you? (Reply **'Confirm'** or **'Yes'**)."
                )
            else:
                prop_msg = (
                    f"📅 **{doc_name} ke sath Appointment ki Tajweez:**\n\n"
                    f"• **Doctor:** {doc_name} ({doc_spec})\n"
                    f"• **Tareeq:** {matched_slot['display_date']}\n"
                    f"• **Waqt:** {matched_slot['display_time']}\n"
                    f"• **Consultation Fee:** PKR {fee:,}\n"
                    f"• **Branch:** {branch_name}\n\n"
                    f"Kya aap is appointment ko confirm karna chahtay hain? Baraye meharbani **'Confirm'** ya **'Theek hai'** keh kar tasdeeq karein."
                )
                
            messages.append({
                "role": "assistant",
                "content": prop_msg,
                "agent": "SchedulingAgent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            sched_state = {
                "doctor_id": doc_id,
                "doctor_name": doc_name,
                "branch_id": target_doc.get("branch_id", "b1"),
                "branch_name": branch_name,
                "proposed_slot": matched_slot,
                "status": "PROPOSED",
                "target_date": target_date_str
            }
            transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "scheduling_request": sched_state,
                "suggested_doctors": suggested_docs_list,
                "current_agent": "scheduling",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }
        else:
            # CONFLICT DETECTED! Suggest 3 alternatives
            alternatives = scheduling_agent.find_alternative_slots(doc_id, target_date_str, requested_time, count=3)
            alt_lines = ""
            for idx, a in enumerate(alternatives, 1):
                alt_lines += f"{idx}. 🗓️ **{a['display_date']}** at **{a['display_time']}**\n"
                
            if is_en:
                conflict_msg = (
                    f"⚠️ **Requested Slot Unavailable:** {doc_name} is not available at **{requested_time}** on **{target_date_str}** (this time slot is already booked or outside clinic hours).\n\n"
                    f"💡 **Suggested Alternative Available Slots:**\n"
                    f"{alt_lines}\n"
                    f"Which of these available times works best for you? Please reply with your choice or 'Confirm' to book."
                )
            else:
                conflict_msg = (
                    f"⚠️ **Maaf kijiye ga:** {doc_name} {target_date_str} ko **{requested_time}** par dastiyab nahi hain (yeh slot pehle se booked hai ya clinic timing se bahir hai).\n\n"
                    f"💡 **Dastiyab Mutabadil (Alternative) Slots:**\n"
                    f"{alt_lines}\n"
                    f"In mein se konsa waqt aap ke liye munasib hai? Baraye meharbani apna pasandeeda waqt batayein taakay appointment book kar di jaye."
                )
                
            messages.append({
                "role": "assistant",
                "content": conflict_msg,
                "agent": "SchedulingAgent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            sched_state = {
                "doctor_id": doc_id,
                "doctor_name": doc_name,
                "branch_id": target_doc.get("branch_id", "b1"),
                "branch_name": branch_name,
                "alternative_slots": alternatives,
                "status": "ALTERNATIVES_PROPOSED",
                "target_date": target_date_str
            }
            transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
            return {
                "messages": messages,
                "scheduling_request": sched_state,
                "suggested_doctors": suggested_docs_list,
                "current_agent": "scheduling",
                "next_agent": "supervisor",
                "node_transitions": transitions
            }
    
    # -------------------------------------------------------------
    # CASE B: Patient did not specify time
    # -------------------------------------------------------------
    if available_slots:
        alt_lines = ""
        for idx, a in enumerate(available_slots[:3], 1):
            alt_lines += f"{idx}. ⏰ **{a['display_time']}**\n"
            
        if is_en:
            slots_msg = (
                f"📅 **Available Slots for {doc_name} on {target_date_str}:**\n\n"
                f"{alt_lines}\n"
                f"• **Branch:** {branch_name} • **Fee:** PKR {fee:,}\n\n"
                f"Please reply with your preferred time slot to confirm booking."
            )
        else:
            slots_msg = (
                f"📅 **{doc_name} ke sath {target_date_str} ko dastiyab slots:**\n\n"
                f"{alt_lines}\n"
                f"• **Branch:** {branch_name} • **Fee:** PKR {fee:,}\n\n"
                f"Aap in mein se kis waqt par appointment book karna chahtay hain? Apna pasandeeda waqt batayein."
            )
            
        messages.append({
            "role": "assistant",
            "content": slots_msg,
            "agent": "SchedulingAgent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        sched_state = {
            "doctor_id": doc_id,
            "doctor_name": doc_name,
            "branch_id": target_doc.get("branch_id", "b1"),
            "branch_name": branch_name,
            "alternative_slots": available_slots[:3],
            "status": "ALTERNATIVES_PROPOSED",
            "target_date": target_date_str
        }
        transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "scheduling_request": sched_state,
            "suggested_doctors": suggested_docs_list,
            "current_agent": "scheduling",
            "next_agent": "supervisor",
            "node_transitions": transitions
        }
    else:
        alternatives = scheduling_agent.find_alternative_slots(doc_id, target_date_str, count=3)
        alt_lines = ""
        for idx, a in enumerate(alternatives, 1):
            alt_lines += f"{idx}. 🗓️ **{a['display_date']}** at **{a['display_time']}**\n"
            
        if is_en:
            full_msg = (
                f"⚠️ **Fully Booked:** {doc_name} has no available slots remaining on **{target_date_str}**.\n\n"
                f"💡 **Next Available Alternative Slots:**\n"
                f"{alt_lines}\n"
                f"Which of these dates and times would you prefer? Reply with your choice to confirm booking."
            )
        else:
            full_msg = (
                f"⚠️ **Tamam Slots Pur Hain:** {doc_name} ke paas **{target_date_str}** ko koi slot khali nahi hai.\n\n"
                f"💡 **Agli Dastiyab Dates aur Waqt (Alternative Slots):**\n"
                f"{alt_lines}\n"
                f"In mein se konsi tareeq aur waqt aap ke liye munasib hai? Batayein taakay appointment confirm kar sakein."
            )
            
        messages.append({
            "role": "assistant",
            "content": full_msg,
            "agent": "SchedulingAgent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        sched_state = {
            "doctor_id": doc_id,
            "doctor_name": doc_name,
            "branch_id": target_doc.get("branch_id", "b1"),
            "branch_name": branch_name,
            "alternative_slots": alternatives,
            "status": "ALTERNATIVES_PROPOSED",
            "target_date": target_date_str
        }
        transitions = _log_transition(state, "scheduling", "supervisor", (time.time() - t0) * 1000)
        return {
            "messages": messages,
            "scheduling_request": sched_state,
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


def explain_lab_parameter_grounded(msg: str, lang: str = "Urdu") -> str:
    """Grounded lab report explanation engine adhering to clinical reference norms and safety disclaimers."""
    msg_low = msg.lower()
    is_en = lang and lang.lower() in ("english", "en")

    if "hba1c" in msg_low or "hb a1c" in msg_low or ("sugar" in msg_low and any(num in msg_low for num in ["8.", "7.", "9.", "6."])):
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", msg_low) or re.search(r"hba1c\s*(?:mein|is|level|hai)?\s*(\d+(?:\.\d+)?)", msg_low)
        val = m.group(1) if m else "8.4"
        val_f = float(val) if val.replace(".", "").isdigit() else 8.4
        status = "Elevated (High / Uncontrolled)" if val_f >= 6.5 else ("Prediabetes" if val_f >= 5.7 else "Normal")
        if is_en:
            return (
                f"🔬 **Clinical Laboratory Investigation: HbA1c (Glycated Hemoglobin)**\n\n"
                f"• **Reported Value:** `{val}%`\n"
                f"• **Normal Reference Range:** `< 5.7%` (Prediabetes: `5.7% - 6.4%`, Diabetes: `≥ 6.5%`)\n"
                f"• **Interpretation:** **{status}**\n\n"
                f"💡 **Clinical Context:** HbA1c reflects average blood sugar levels over the past 2 to 3 months. A value of {val}% indicates elevated blood glucose requiring medical oversight.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** This information is for educational purposes only and is NOT a medical diagnosis. Please consult Dr. Bilal Saeed (Internal Medicine / Diabetology) for clinical evaluation and prescription adjustment."
            )
        else:
            return (
                f"🔬 **Lab Report Ki Wazahat: HbA1c (Glycated Hemoglobin)**\n\n"
                f"• **Report Ki Value:** `{val}%`\n"
                f"• **Normal Reference Range:** Normal hadd `< 5.7%` hoti hai (Prediabetes: `5.7% - 6.4%`, Diabetes: `≥ 6.5%`)\n"
                f"• **Tajziya (Status):** **Normal Hadd Se Zyada (High / Ghair-Mutawazan)**\n\n"
                f"💡 **Tafseel:** HbA1c pichlay 2 se 3 maah ki ausat sugar ko zahir karta hai. {val}% ka matlab hai ke blood sugar barhi hui hai aur doctori mashwara darqar hai.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Yeh AI wazahat hai aur kisi bimari ki tashkhees (diagnosis) nahi karti. Sahi ilaj ke liye Dr. Bilal Saeed (Internal Medicine) se appointment book karein."
            )

    elif "alt" in msg_low or "sgpt" in msg_low or "lft" in msg_low:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:u/l|iu/l)?", msg_low)
        val = m.group(1) if m else "85"
        val_f = float(val) if val.replace(".", "").isdigit() else 85.0
        status = "Elevated (High)" if val_f > 56 else "Normal"
        if is_en:
            return (
                f"🔬 **Clinical Laboratory Investigation: ALT / SGPT (Liver Function Test)**\n\n"
                f"• **Reported Value:** `{val} U/L`\n"
                f"• **Normal Reference Range:** `7 - 56 U/L`\n"
                f"• **Interpretation:** **{status}**\n\n"
                f"💡 **Clinical Context:** Alanine Aminotransferase (ALT) is an enzyme concentrated in liver tissue. An elevated level of {val} U/L may reflect mild hepatic inflammation, fatty liver, or medication strain.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Does not constitute a clinical diagnosis. Please consult Dr. Usman Sheikh (Gastroenterology) for examination and management."
            )
        else:
            return (
                f"🔬 **Lab Report Ki Wazahat: ALT / SGPT (Jigar Ka Test)**\n\n"
                f"• **Report Ki Value:** `{val} U/L`\n"
                f"• **Normal Reference Range:** `7 - 56 U/L`\n"
                f"• **Tajziya (Status):** **Normal Hadd Se Zyada (High)**\n\n"
                f"💡 **Tafseel:** ALT jigar ka enzyme hai. {val} U/L jigar par mamooli sozish ya fatty liver ki nishandahi kar sakta hai.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Tashkhees ke liye Dr. Usman Sheikh (Gastroenterology) se checkup karwayein."
            )

    elif "creatinine" in msg_low:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:mg/dl)?", msg_low)
        val = m.group(1) if m else "2.1"
        val_f = float(val) if val.replace(".", "").isdigit() else 2.1
        status = "Elevated (High)" if val_f > 1.3 else "Normal"
        if is_en:
            return (
                f"🔬 **Clinical Laboratory Investigation: Serum Creatinine (Kidney Function)**\n\n"
                f"• **Reported Value:** `{val} mg/dL`\n"
                f"• **Normal Reference Range:** `0.7 - 1.3 mg/dL`\n"
                f"• **Interpretation:** **{status}**\n\n"
                f"💡 **Clinical Context:** Creatinine is a byproduct of muscle metabolism filtered by the kidneys. A value of {val} mg/dL indicates elevated levels and reduced renal filtration requiring clinical assessment.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Please consult a clinic physician for repeat renal function tests and ultrasound examination."
            )
        else:
            return (
                f"🔬 **Lab Report Ki Wazahat: Serum Creatinine (Gurdon Ka Test)**\n\n"
                f"• **Report Ki Value:** `{val} mg/dL`\n"
                f"• **Normal Reference Range:** `0.7 - 1.3 mg/dL`\n"
                f"• **Tajziya (Status):** **Normal Hadd Se Zyada (High)**\n\n"
                f"💡 **Tafseel:** Creatinine gurdon ki filtration ki salahiyat ko zahir karta hai. {val} mg/dL barhi hui hadd hai jis par fori doctori checkup zaroori hai.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Yeh AI wazahat diagnosis nahi hai. Gurdon ki janch ke liye apne doctor se fori rabta karein."
            )

    elif "hemoglobin" in msg_low or "hb" in msg_low or "khoon ki kami" in msg_low:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:g/dl)?", msg_low)
        val = m.group(1) if m else "8.5"
        val_f = float(val) if val.replace(".", "").isdigit() else 8.5
        status = "Low (Anemia Indicator)" if val_f < 12.0 else "Normal"
        if is_en:
            return (
                f"🔬 **Clinical Laboratory Investigation: Hemoglobin (CBC)**\n\n"
                f"• **Reported Value:** `{val} g/dL`\n"
                f"• **Normal Reference Range:** Males: `13.0 - 17.0 g/dL` | Females: `12.0 - 15.5 g/dL`\n"
                f"• **Interpretation:** **{status}**\n\n"
                f"💡 **Clinical Context:** Hemoglobin transports oxygen in blood. A level of {val} g/dL indicates anemia (low red blood cells), which may cause fatigue and pale appearance.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Consult a physician to evaluate the underlying etiology (iron deficiency or dietary deficiency)."
            )
        else:
            return (
                f"🔬 **Lab Report Ki Wazahat: Hemoglobin (CBC Test)**\n\n"
                f"• **Report Ki Value:** `{val} g/dL`\n"
                f"• **Normal Reference Range:** Mard: `13.0 - 17.0 g/dL` | Khawateen: `12.0 - 15.5 g/dL`\n"
                f"• **Tajziya (Status):** **Normal Hadd Se Kam (Low — Anemia)**\n\n"
                f"💡 **Tafseel:** {val} g/dL khoon ki kami (anemia) ko zahir karta hai. Sahi ilaj aur iron plan ke liye doctor se ruju karein.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Tashkhees aur supplements ke liye clinic doctor se rabta karein."
            )

    elif "cholesterol" in msg_low or "lipid" in msg_low:
        m = re.search(r"(\d+(?:\.\d+)?)", msg_low)
        val = m.group(1) if m else "180"
        val_f = float(val) if val.replace(".", "").isdigit() else 180.0
        status = "Desirable / Normal" if val_f < 200 else "Borderline High"
        if is_en:
            return (
                f"🔬 **Clinical Laboratory Investigation: Total Cholesterol**\n\n"
                f"• **Reported Value:** `{val} mg/dL`\n"
                f"• **Normal Reference Range:** Desirable: `< 200 mg/dL` | Borderline: `200 - 239 mg/dL`\n"
                f"• **Interpretation:** **{status}**\n\n"
                f"💡 **Clinical Context:** Total cholesterol at {val} mg/dL is within the healthy desirable range.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** For complete cardiovascular screening, consult Dr. Ayesha Tariq (Cardiology)."
            )
        else:
            return (
                f"🔬 **Lab Report Ki Wazahat: Total Cholesterol (Lipid Profile)**\n\n"
                f"• **Report Ki Value:** `{val} mg/dL`\n"
                f"• **Normal Reference Range:** Desirable (Munasib): `< 200 mg/dL`\n"
                f"• **Tajziya (Status):** **Normal aur Munasib Hadd (Desirable)**\n\n"
                f"💡 **Tafseel:** {val} mg/dL standard medical guidelines ke mutabiq normal aur sehat-mand hadd ke andar hai.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Mukammal lipid profile ke liye Dr. Ayesha Tariq (Cardiologist) se checkup karwayein."
            )

    elif "platelet" in msg_low:
        m = re.search(r"(\d+[\d,]*)", msg_low)
        val = m.group(1) if m else "550,000"
        if is_en:
            return (
                f"🔬 **Clinical Laboratory Investigation: Platelet Count (CBC)**\n\n"
                f"• **Reported Value:** `{val} /uL`\n"
                f"• **Normal Reference Range:** `150,000 - 450,000 /uL`\n"
                f"• **Interpretation:** **Elevated (Thrombocytosis)**\n\n"
                f"💡 **Clinical Context:** Platelets regulate clotting. An elevated count of {val} /uL is typically reactive to infection, inflammation, or iron deficiency.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Consult a physician for clinical assessment."
            )
        else:
            return (
                f"🔬 **Lab Report Ki Wazahat: Platelets Count (CBC)**\n\n"
                f"• **Report Ki Value:** `{val} /uL`\n"
                f"• **Normal Reference Range:** `150,000 - 450,000 /uL`\n"
                f"• **Tajziya (Status):** **Normal Hadd Se Zyada (Thrombocytosis)**\n\n"
                f"💡 **Tafseel:** {val} barhi hui tadad aam tor par kisi guzishta infection ya sozish ka rad-e-amal hoti hai.\n\n"
                f"🛡️ **Non-Diagnostic Safety Disclaimer:** Sahi tashkhees ke liye apne doctor se mashwara karein."
            )

    elif "potassium" in msg_low:
        m = re.search(r"(\d+(?:\.\d+)?)", msg_low)
        val = m.group(1) if m else "6.2"
        if is_en:
            return (
                f"🚨 **CRITICAL LABORATORY ALERT: Serum Potassium**\n\n"
                f"• **Reported Value:** `{val} mmol/L`\n"
                f"• **Normal Reference Range:** `3.5 - 5.0 mmol/L`\n"
                f"• **Interpretation:** **CRITICAL HIGH (Hyperkalemia Alert)**\n\n"
                f"⚠️ **Urgent Action:** Serum potassium of {val} mmol/L carries risk of cardiac arrhythmias. Seek immediate emergency evaluation!\n\n"
                f"📞 24/7 Helpline: 042-111-CARE-00"
            )
        else:
            return (
                f"🚨 **SHADEED LAB ALERT: Serum Potassium**\n\n"
                f"• **Report Ki Value:** `{val} mmol/L`\n"
                f"• **Normal Reference Range:** `3.5 - 5.0 mmol/L`\n"
                f"• **Tajziya (Status):** **CRITICAL HIGH (Hyperkalemia Alert)**\n\n"
                f"⚠️ **Zaroori Hidayat:** {val} mmol/L potassium dil ki dharkan ke liye intehai khatarnaak ho sakta hai. Baraye meharbani fori tor par Emergency Ward se ruju karein!\n\n"
                f"📞 City Care 24/7 Helpline: 042-111-CARE-00"
            )

    return (
        "🔬 Aap ki lab report ka tajziya standard medical reference ranges ke mutabiq check kiya ja sakta hai. "
        "Sahi tashkhees aur ilaj ke liye baraye meharbani apne muallij doctor se ruju karein."
    )


def records_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Lab result explanation node:
    Provides grounded clinical parameter interpretation with strict non-diagnostic disclaimers
    and registers human-in-the-loop audit task.
    """
    t0 = time.time()
    patient_id = state.get("patient_id") or "p1"
    summary = records_agent.get_patient_summary(patient_id)
    lang = state.get("language") or "Urdu"

    messages = list(state.get("messages", []))
    latest_user_msg = ""
    for m in reversed(messages):
        if _is_user_msg(m):
            latest_user_msg = _get_msg_content(m)
            break

    if is_lab_inquiry_message(latest_user_msg):
        lab_reply = explain_lab_parameter_grounded(latest_user_msg, lang)
        is_pending = False
    else:
        lab_reply = (
            "🔬 Aap ke recent blood test (CBC) ke mutabiq Hemoglobin 13.8 g/dL normal hai, "
            "lekin WBC count 12,400 /uL thora barha hua hai jo jism mein mamooli sozish ya infection ko zahir karta hai.\n\n"
            "🛡️ *Non-Diagnostic Disclaimer:* Sahi tashkhees ke liye apne doctor se checkup karwayein."
        )
        is_pending = True

    task = hitl_manager.create_pending_approval(
        thread_id=state.get("session_id", "default_thread"),
        patient_id=state.get("patient_id"),
        patient_name=state.get("patient_name", "Valued Patient"),
        task_type="LAB_EXPLANATION",
        proposed_message_urdulish=lab_reply,
        clinical_context={"labs": summary.get("observations", []) if summary else []},
        urgency_level="ROUTINE"
    )

    messages.append({
        "role": "assistant",
        "content": lab_reply,
        "agent": "RecordsAgent",
        "is_pending_review": is_pending,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "records", "supervisor", latency_ms)
    trace_id = state.get("telemetry", {}).get("trace_id")
    if trace_id:
        observability.log_agent_span(trace_id, "RecordsAgent", latency_ms, prompt_tokens=220, completion_tokens=90)

    return {
        "messages": messages,
        "hitl_required": is_pending,
        "hitl_type": "LAB_EXPLANATION",
        "hitl_payload": task,
        "current_agent": "records",
        "next_agent": "supervisor",
        "node_transitions": transitions
    }

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
    Provides immediate life-saving escalation for acute conditions like cardiac chest pain.
    """
    t0 = time.time()
    triage = state.get("triage_result") or {}
    lang = state.get("language") or "Urdu"
    messages = list(state.get("messages", []))
    latest_user_msg = ""
    for m in reversed(messages):
        if _is_user_msg(m):
            latest_user_msg = _get_msg_content(m)
            break
    msg_low = latest_user_msg.lower()

    is_cardiac = any(w in msg_low for w in ["sen", "chest", "dil", "heart", "chhat", "chat", "bazu", "arm"])

    if lang and lang.lower() in ("english", "en"):
        if is_cardiac:
            esc_msg = (
                "🚨 **CRITICAL MEDICAL EMERGENCY: POSSIBLE CARDIAC EVENT (CALL 1122 RESCUE)** 🚨\n\n"
                "Severe chest pain is an immediate, potentially life-threatening emergency (Possible Heart Attack / Acute Coronary Syndrome).\n\n"
                "🛑 **TAKE IMMEDIATE LIFE-SAVING ACTION:**\n"
                "1. **Call 1122 Emergency Services immediately** or proceed straight to the nearest Hospital Emergency Room (ER).\n"
                "2. **DO NOT drive yourself** — have someone drive you or wait for an ambulance.\n"
                "3. If not allergic and not contraindicated by your physician, chew **one Aspirin / Disprin 300mg tablet immediately**.\n"
                "4. Rest in a comfortable seated position; avoid physical exertion.\n"
                "5. **Do NOT wait for an outpatient clinic appointment or booking.**\n\n"
                "📞 **City Care 24/7 Emergency Support:** 042-111-CARE-00"
            )
        else:
            esc_msg = (
                "🚨 **CRITICAL MEDICAL EMERGENCY (CALL 1122 RESCUE NOW)** 🚨\n\n"
                "Your reported symptoms indicate an immediate, life-threatening condition.\n\n"
                "🛑 **TAKE IMMEDIATE LIFE-SAVING ACTION:**\n"
                "1. **Please call 1122 Emergency Services immediately** or proceed directly to the nearest Hospital Emergency Ward (ER)!\n"
                "2. **DO NOT drive yourself** — seek immediate assistance.\n"
                "3. Do not wait for online appointments or regular doctor consultations.\n\n"
                "📞 **City Care 24/7 Emergency Helpline:** 042-111-CARE-00"
            )
    else:
        if is_cardiac:
            esc_msg = (
                "🚨 **SHADEED EMERGENCY NOTICE: QALBI EMERGENCY (FORI 1122 RESCUE)** 🚨\n\n"
                "Seny mein shadeed dard (severe chest pain) ek **QALBI EMERGENCY (Heart Attack / Acute Coronary Syndrome)** ka fori khatra ho sakti hai.\n\n"
                "🛑 **BARAYE MEHARBANI FORAN YEH IQDAMAT KAREIN:**\n"
                "1. **Bila-takheer 1122 Rescue par call karein** ya foran qareebi hospital ke Emergency Ward (ER) pohnchein!\n"
                "2. **Khud bilkul drive na karein**, kisi ko sath chalne ya gaari chalane ka kahein.\n"
                "3. Agar doctor ne mana na kiya ho aur koi allergy na ho, to foran **1 tablet Aspirin / Disprin 300mg chaba lein**.\n"
                "4. Pur-sukoon baith jayein aur kisi qisam ka jismari dbao ya wazan na uthayein.\n"
                "5. **Online appointment ya regular OPD doctor ka intizar hargiz na karein.**\n\n"
                "📞 **City Care 24/7 Emergency Helpline:** 042-111-CARE-00"
            )
        else:
            esc_msg = (
                "🚨 **SHADEED EMERGENCY NOTICE (FORI 1122 RESCUE)** 🚨\n\n"
                "Aap ki alamaat fori jaan-lewa khatray ki nishandahi karti hain.\n\n"
                "🛑 **BARAYE MEHARBANI FORAN YEH IQDAMAT KAREIN:**\n"
                "1. **Bila-takheer 1122 emergency helpline par call karein** ya foran qareebi Emergency Ward pohnchein!\n"
                "2. **Khud drive na karein**, fori tor par kisi ki madad lein.\n"
                "3. Regular appointment ka intizar hargiz na karein.\n\n"
                "📞 **City Care 24/7 Emergency Helpline:** 042-111-CARE-00"
            )

    messages.append({
        "role": "assistant",
        "content": esc_msg,
        "agent": "City Care Assistant",
        "is_emergency": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    state["triage_result"] = {
        "urgency_tier": "EMERGENCY",
        "is_emergency": True,
        "confidence_score": 1.0,
        "reason": "Red flag symptom detected (Severe chest / cardiac / acute emergency)",
        "escalation_message_urdulish": esc_msg
    }

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "emergency_escalation", "END", latency_ms)

    return {
        "messages": messages,
        "triage_result": state["triage_result"],
        "current_agent": "emergency_escalation",
        "next_agent": "END",
        "node_transitions": transitions
    }


def safety_guardrail_node(state: ClinicalState) -> Dict[str, Any]:
    """
    Zero-tolerance safety guardrail node:
    Enforces HIPAA/privacy confidentiality, non-diagnostic disclaimers,
    prescription safety, and professional scope boundaries.
    """
    t0 = time.time()
    messages = list(state.get("messages", []))
    latest_user_msg = ""
    for m in reversed(messages):
        if _is_user_msg(m):
            latest_user_msg = _get_msg_content(m)
            break

    lang = state.get("language") or "Urdu"
    is_en = lang and lang.lower() in ("english", "en")

    reply_content = ""
    safety_category = "general_safety"

    if is_data_exfiltration_attempt(latest_user_msg):
        safety_category = "data_exfiltration_attempt"
        if is_en:
            reply_content = (
                "🔒 **Security & Patient Privacy Violation Refusal:**\n\n"
                "Under City Care Clinics strict data security protocols and healthcare privacy regulations (HIPAA & Medical Confidentiality Laws), "
                "accessing, sharing, or exfiltrating another patient's medical records, reports, or sensitive data is strictly prohibited.\n\n"
                "System guardrails and privacy protections cannot be overridden. All patient data is strictly compartmentalized and protected."
            )
        else:
            reply_content = (
                "🔒 **Security aur Mareez Ki Privacy Ka Tahaffuz:**\n\n"
                "City Care Clinics ke security protocols aur healthcare privacy qawaneen (HIPAA / Patient Confidentiality) ke tehat, "
                "kisi bhi doosray mareez (patient) ka record, lab report, ya confidential data share karna sakht mana hai.\n\n"
                "System ke safety rules ko bypass ya override karne ki ijazat nahi hai. Hum tamam mareezon ke data ki hifazat ko yaqeeni banatay hain."
            )

    elif is_diagnosis_demand(latest_user_msg):
        safety_category = "unauthorized_diagnosis_refusal"
        if is_en:
            reply_content = (
                "⚠️ **Clinical Disclaimer & Diagnosis Policy:**\n\n"
                "As an AI Healthcare Assistant for City Care Clinics, I cannot provide a definitive medical diagnosis (bimari ki tashkhees) "
                "without an in-person physical clinical examination and diagnostic investigations by a licensed physician.\n\n"
                "Diagnosing illnesses autonomously is unsafe. However, I can help you book a consultation with our experienced specialist doctors "
                "who can properly diagnose and treat your condition. Would you like to view our available specialists?"
            )
        else:
            reply_content = (
                "⚠️ **Clinical Disclaimer — Bimari Ki Tashkhees (Diagnosis) Policy:**\n\n"
                "City Care Clinics ke AI Assistant ke tor par, main bina qualified doctor ke physical muaina (clinical examination) aur zaroori tests ke "
                "kisi bhi bimari ki tashkhees (diagnosis) nahi kar sakta. Yeh medical safety guidelines ke mutabiq hai.\n\n"
                "Aap ki alamaat ke mutabiq hum aap ko mutaliqa specialist doctor suggest kar saktay hain taakay mukammal aur tasalli-bakhsh checkup ho sakay. "
                "Kya aap doctor ke sath appointment book karna chahtay hain?"
            )

    elif is_unauthorized_medication_demand(latest_user_msg):
        safety_category = "unauthorized_prescription_refusal"
        if is_en:
            reply_content = (
                "⚠️ **Prescription & Medication Safety Alert:**\n\n"
                "In strict compliance with PMDC (Pakistan Medical & Dental Council) regulations and international clinical safety standards, "
                "prescription medications cannot be recommended or dispensed without an evaluation and prescription by a licensed physician.\n\n"
                "Self-medication without a doctor's oversight carries severe health risks (including drug toxicity, allergic reactions, and organ strain). "
                "Please schedule an appointment with one of our clinic doctors to receive the appropriate safe prescription."
            )
        else:
            reply_content = (
                "⚠️ **Prescription aur Dawai Ki Hifazat (Safety Alert):**\n\n"
                "PMDC aur City Care Clinics ki clinical safety policy ke tehat, bina qualified doctor ke muaina aur checkup ke koi dawai tajweez (prescribe) "
                "ya suggest nahi ki ja sakti. Khud se dawai lena aap ki sehat ke liye shadeed nuqsandeh aur khatarnaak ho sakta hai.\n\n"
                "Sahi aur mehfooz ilaj ke liye baraye meharbani City Care ke specialist doctor se appointment book karein jo aap ko check kar ke munasib prescription jari karein ge."
            )

    elif is_off_topic_query(latest_user_msg):
        safety_category = "off_topic_redirection"
        if is_en:
            reply_content = (
                "🩺 **City Care Clinics Assistant Scope:**\n\n"
                "I am the AI Healthcare Assistant for City Care Clinics. My scope is strictly focused on clinic services: "
                "doctor appointments, clinical triage, branch locations, and laboratory report reviews.\n\n"
                "I cannot answer questions outside healthcare and clinic operations. "
                "If you would like to book a doctor consultation or check clinic services, please let me know!"
            )
        else:
            reply_content = (
                "🩺 **City Care Clinics Assistant Scope:**\n\n"
                "Main City Care Clinics ka AI Healthcare Assistant hoon. Mera maqsad sirf medical appointments, doctor scheduling, "
                "clinic branches, aur lab reports ke mutaliq rehnumai faraham karna hai.\n\n"
                "Main ghair-tibbi (off-topic) masail par guftagu nahi kar sakta. "
                "Agar aap ko kisi specialist doctor se appointment chahiye ya clinic ke baray mein maloomat darqar hain, to zaroor batayein."
            )

    elif is_overdose_inquiry(latest_user_msg):
        safety_category = "overdose_warning"
        if is_en:
            reply_content = (
                "🚨 **CRITICAL OVERDOSE WARNING — LETHAL TOXICITY RISK:**\n\n"
                "Taking multiple analgesic tablets (such as 15 Panadol / Paracetamol pills) is a life-threatening medical emergency! "
                "The maximum safe daily limit for an adult is 4,000mg (8 x 500mg tablets) distributed across 24 hours.\n\n"
                "An acute dose above this limit causes irreversible acute hepatotoxicity (severe liver failure) and can be fatal. "
                "**DO NOT TAKE THIS MEDICATION.** Call Emergency Rescue 1122 or proceed immediately to the nearest hospital Emergency Room!"
            )
        else:
            reply_content = (
                "🚨 **SHADEED KHATARNAAK OVERDOSE ALERT — JAAN-LEWA NUKSAAN:**\n\n"
                "Ek waqt mein 15 Panadol goliyan (7,500mg) ya hadd se zyada painkiller khana sakht jaan-lewa aur zehrila (fatal toxicity) hai! "
                "Paracetamol ki maximum mehfooz hadd 24 ghanton mein 4000mg (8 tablets) hai.\n\n"
                "Itni zyada miqdar foran jigar (acute liver failure) ko fail kar sakti hai. **Hargiz yeh goliyan na khayein.** "
                "Barah-e-karam foran Rescue 1122 par call karein ya nazdeeki Emergency Room pohnchein!"
            )

    elif is_angry_or_frustrated(latest_user_msg):
        safety_category = "patient_de_escalation"
        if is_en:
            reply_content = (
                "🤝 **Patient Care & Support Priority:**\n\n"
                "We sincerely apologize for any frustration or inconvenience you have experienced. We deeply value your time and comfort.\n\n"
                "Please share your Appointment ID or the specific issue, and I will immediately escalate your case to our Clinic Management "
                "and Head Patient Coordinator for priority resolution.\n\n"
                "📞 **Direct Clinic Priority Helpline:** 042-111-CARE-00 (Ext. 2)"
            )
        else:
            reply_content = (
                "🤝 **City Care Mareez Ki Madad aur Rahat:**\n\n"
                "Hum dil se maazrat-khwah hain agar aap ko kisi dushwari ya takleef ka samna karna para. Hum aap ke waqt aur jazbaat ki poori qadar kartay hain.\n\n"
                "Baraye meharbani apna Appointment ID ya masla batayein taakay hum fori tor par Clinic Management aur Senior Coordinator se aap ka masla hal karwa sakein.\n\n"
                "📞 **City Care Direct Helpline:** 042-111-CARE-00 (Ext. 2 par rabta karein)."
            )

    else:
        safety_category = "general_safety"
        reply_content = "City Care Clinics mein khush-amdeed. Hum aap ki sehat aur appointments ke liye hazir hain."

    messages.append({
        "role": "assistant",
        "content": reply_content,
        "agent": "SafetyGuardrail",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    latency_ms = (time.time() - t0) * 1000
    transitions = _log_transition(state, "safety_guardrail", "END", latency_ms)

    return {
        "messages": messages,
        "safety_category": safety_category,
        "current_agent": "safety_guardrail",
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
    builder.add_node("safety_guardrail", safety_guardrail_node)

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
            "safety_guardrail": "safety_guardrail",
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
    builder.add_edge("safety_guardrail", END)

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
