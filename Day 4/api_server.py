"""
FastAPI Backend Server for City Care Clinics Multi-Agent Architecture
Powers:
1. Patient Portal Web Chat with LangGraph Execution & Session Checkpointing
2. Returning Patient Recognition & Long-Term Clinical Memory
3. Doctor HITL Command Center (Approve / Edit / Reject pending clinical gates)
4. Pre-Visit SOAP Briefs & Clinical Summaries
5. Real-Time Observability, Latency, and Cost Tracking
"""

import sys
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Literal
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure imports
DAY4_DIR = Path(__file__).resolve().parent
ROOT_DIR = DAY4_DIR.parent
DAY3_DIR = ROOT_DIR / "Day 3"
DAY2_DIR = ROOT_DIR / "Day 2"

for p in [str(DAY4_DIR), str(DAY3_DIR), str(DAY3_DIR / "agents"), str(DAY2_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from clinical_state import ClinicalState
from langgraph_workflow import clinical_graph, get_mermaid_graph
from memory_manager import memory_manager
from hitl_manager import hitl_manager
from observability import observability
from email_notifier import email_notifier
from clinical_summary_agent import clinical_summary_agent  # type: ignore

app = FastAPI(
    title="City Care Clinics Multi-Agent Healthcare API",
    description="LangGraph Orchestration, Long-Term Memory, and Doctor Human-in-the-Loop Engine",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session state storage for fast retrieval
active_sessions: Dict[str, Dict[str, Any]] = {}


# =====================================================================
# Request / Response Schemas
# =====================================================================

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    patient_identifier: Optional[str] = None
    is_returning_patient: Optional[bool] = None
    trigger_type: Optional[str] = None # "chat", "lab_inquiry", "prescription_check"

class DoctorDecisionRequest(BaseModel):
    task_id: str
    decision: Literal["approved", "edited", "rejected"]
    doctor_notes: Optional[str] = None
    edited_message: Optional[str] = None
    doctor_name: Optional[str] = "Dr. Maryam Naveed (Medical Director)"


# =====================================================================
# API Endpoints
# =====================================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "City Care Clinics Multi-Agent Orchestration",
        "model": "gemini-3.5-flash-lite",
        "langgraph_ready": True,
        "branches": ["Gulberg Lahore", "DHA Lahore", "Johar Town Lahore", "F-8 Islamabad", "Blue Area Islamabad"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/patients")
def list_patients():
    """Lists preloaded returning patients for easy switching in the web demo."""
    patients = []
    for pid, mem in memory_manager._memory_cache.items():
        patients.append({
            "patient_id": mem.get("patient_id"),
            "patient_name": mem.get("patient_name"),
            "phone": mem.get("phone"),
            "mrn": mem.get("mrn"),
            "preferred_doctor": mem.get("preferred_doctor_name"),
            "preferred_branch": mem.get("preferred_branch"),
            "known_allergies": mem.get("known_allergies", []),
            "chronic_conditions": mem.get("chronic_conditions", []),
            "last_visit_date": mem.get("last_visit_date")
        })
    return {"patients": patients}


@app.get("/api/patients/{identifier}/memory")
def get_patient_memory(identifier: str):
    """Retrieves long-term memory profile for a patient."""
    mem = memory_manager.find_patient_memory(identifier)
    if not mem:
        raise HTTPException(status_code=404, detail="Patient memory profile not found.")
    return mem


@app.get("/api/patients/{identifier}/soap")
def get_patient_soap_note(identifier: str):
    """Generates or retrieves pre-visit SOAP brief with fact vs AI segregation."""
    mem = memory_manager.find_patient_memory(identifier) or {}
    sample_intake = {
        "chief_complaint": mem.get("past_complaints", ["General health consultation"])[-1] if mem.get("past_complaints") else "General Checkup",
        "duration": "1 week",
        "severity": 4,
        "allergies": mem.get("known_allergies", []),
        "medical_history": mem.get("chronic_conditions", [])
    }
    soap = clinical_summary_agent.generate_soap_note(sample_intake, mem.get("patient_id", "p1"))
    return soap.model_dump() if hasattr(soap, "model_dump") else dict(soap)


@app.post("/api/chat")
def handle_patient_chat(req: ChatRequest):
    """
    Core conversational endpoint.
    Orchestrates turn through LangGraph with checkpointer and observability.
    """
    session_id = req.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    t0 = time.time()

    # 1. Initialize or load session state
    if session_id not in active_sessions:
        trace_id = observability.start_trace(session_id, req.patient_identifier)
        patient_mem = memory_manager.find_patient_memory(req.patient_identifier) if req.patient_identifier else None
        is_returning = True if patient_mem else (req.is_returning_patient or False)
        p_name = patient_mem.get("patient_name") if patient_mem else (req.patient_identifier or "Valued Patient")

        state: ClinicalState = {
            "messages": [],
            "session_id": session_id,
            "user_id": req.patient_identifier or "guest",
            "patient_id": patient_mem.get("patient_id") if patient_mem else "p1",
            "patient_name": p_name,
            "patient_phone": patient_mem.get("phone") if patient_mem else None,
            "patient_mrn": patient_mem.get("mrn") if patient_mem else None,
            "is_returning_patient": is_returning,
            "long_term_memory": patient_mem or {},
            "intake_form": {},
            "intake_complete": False,
            "triage_result": None,
            "records_data": None,
            "scheduling_request": None,
            "appointment_result": None,
            "clinical_soap_note": None,
            "draft_prescription": None,
            "prescription_safety_report": None,
            "followup_plan": None,
            "hitl_required": False,
            "hitl_type": None,
            "hitl_payload": None,
            "hitl_decision": None,
            "current_agent": "supervisor",
            "next_agent": None,
            "error_state": None,
            "node_transitions": [],
            "telemetry": {"trace_id": trace_id}
        }
        active_sessions[session_id] = state
    else:
        state = active_sessions[session_id]

    # Handle special direct triggers (e.g. lab inquiry button or prescription trigger)
    if req.trigger_type == "lab_inquiry":
        state["next_agent"] = "records"
    elif req.trigger_type == "prescription_check":
        state["draft_prescription"] = [{"drug_name": "Augmentin 625mg", "dose": "625mg BID"}]
        state["next_agent"] = "prescription_safety"

    # 2. Append user message
    user_msg_dict = {
        "role": "user",
        "content": req.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    state["messages"].append(user_msg_dict)

    # 3. Invoke LangGraph workflow
    config = {"configurable": {"thread_id": session_id}}
    updated_state = clinical_graph.invoke(state, config=config)

    # Update session in memory
    active_sessions[session_id] = updated_state

    # 4. Extract latest assistant message
    latest_reply = "Hum aap ki madad ke liye hazir hain."
    for m in reversed(updated_state.get("messages", [])):
        if m.get("role") == "assistant":
            latest_reply = m.get("content", "")
            break

    latency_ms = (time.time() - t0) * 1000

    return {
        "session_id": session_id,
        "reply": latest_reply,
        "messages": updated_state.get("messages", []),
        "current_agent": updated_state.get("current_agent"),
        "intake_form": updated_state.get("intake_form"),
        "triage_result": updated_state.get("triage_result"),
        "appointment_result": updated_state.get("appointment_result"),
        "hitl_required": updated_state.get("hitl_required", False),
        "hitl_type": updated_state.get("hitl_type"),
        "hitl_payload": updated_state.get("hitl_payload"),
        "node_transitions": updated_state.get("node_transitions", []),
        "latency_ms": round(latency_ms, 2)
    }


@app.get("/api/doctor/pending")
def get_pending_doctor_tasks():
    """Returns all pending human-in-the-loop review tasks."""
    tasks = hitl_manager.get_pending_tasks()
    return {"pending_tasks": tasks, "count": len(tasks)}


@app.post("/api/doctor/decision")
def post_doctor_decision(req: DoctorDecisionRequest):
    """
    Applies the physician's review decision (approve, edit, reject)
    and resumes the paused LangGraph workflow for the patient!
    """
    task = hitl_manager.process_doctor_decision(
        task_id=req.task_id,
        decision=req.decision,
        doctor_notes=req.doctor_notes,
        edited_message=req.edited_message,
        doctor_name=req.doctor_name or "Dr. Maryam Naveed (Medical Director)"
    )

    thread_id = task.get("thread_id")
    resumed_reply = task.get("final_message_urdulish", "")

    # If this thread is an active session, resume the graph!
    if thread_id and thread_id in active_sessions:
        state = active_sessions[thread_id]
        state["hitl_decision"] = task
        state["next_agent"] = "hitl_gate"

        config = {"configurable": {"thread_id": thread_id}}
        resumed_state = clinical_graph.invoke(state, config=config)
        active_sessions[thread_id] = resumed_state

        for m in reversed(resumed_state.get("messages", [])):
            if m.get("role") == "assistant":
                resumed_reply = m.get("content", "")
                break

    return {
        "success": True,
        "task": task,
        "resumed_reply": resumed_reply
    }


@app.get("/api/telemetry/stats")
def get_telemetry_stats():
    """Returns aggregate observability metrics."""
    return observability.get_summary_stats()


@app.get("/api/telemetry/traces")
def get_recent_traces():
    """Returns the most recent conversation traces with spans and tool calls."""
    return {"traces": observability._traces[-15:]}


@app.get("/api/graph/mermaid")
def get_graph_mermaid():
    """Returns the Mermaid diagram source string."""
    return {"mermaid": get_mermaid_graph()}


if __name__ == "__main__":
    import uvicorn
    print("Starting City Care Clinics FastAPI backend on port 8000...")
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=False)
