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

try:
    from db_client import db  # type: ignore
except Exception:
    db = None

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

# Predefined Verified Doctor Staff Accounts
DOCTOR_ACCOUNTS = [
    {
        "id": "doc1",
        "email": "dr.bilal@citycare.com",
        "password": "Doctor123!",
        "name": "Dr. Bilal Saeed",
        "specialty": "General Medicine",
        "branch": "Gulberg Lahore",
        "pmdc_number": "PMDC-68210-P",
        "role": "Senior Consultant Physician"
    },
    {
        "id": "doc2",
        "email": "dr.ayesha@citycare.com",
        "password": "Doctor123!",
        "name": "Dr. Ayesha Tariq",
        "specialty": "Gynaecology",
        "branch": "DHA Lahore",
        "pmdc_number": "PMDC-74921-P",
        "role": "Consultant Gynaecologist"
    },
    {
        "id": "doc3",
        "email": "dr.usman@citycare.com",
        "password": "Doctor123!",
        "name": "Dr. Usman Sheikh",
        "specialty": "Paediatrics",
        "branch": "F-8 Markaz Islamabad",
        "pmdc_number": "PMDC-55102-I",
        "role": "Consultant Paediatrician"
    },
    {
        "id": "doc4",
        "email": "dr.maryam@citycare.com",
        "password": "Doctor123!",
        "name": "Dr. Maryam Naveed",
        "specialty": "Executive Health & Clinical Quality",
        "branch": "Headquarters Lahore",
        "pmdc_number": "PMDC-41298-P",
        "role": "Medical Director"
    }
]


# =====================================================================
# Request / Response Schemas
# =====================================================================

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    patient_identifier: Optional[str] = None
    is_returning_patient: Optional[bool] = None
    language: Optional[str] = "Urdu" # "English" or "Urdu"
    trigger_type: Optional[str] = None # "chat", "lab_inquiry", "prescription_check"

class DoctorDecisionRequest(BaseModel):
    task_id: str
    decision: Literal["approved", "edited", "rejected"]
    doctor_notes: Optional[str] = None
    edited_message: Optional[str] = None
    doctor_name: Optional[str] = "Dr. Maryam Naveed (Medical Director)"

class PatientSignupRequest(BaseModel):
    patient_name: str
    phone: str
    age: Optional[int] = 30
    gender: Optional[str] = "Unspecified"
    known_allergies: Optional[List[str]] = []
    chronic_conditions: Optional[List[str]] = []
    preferred_language: Optional[str] = "English"
    preferred_doctor_name: Optional[str] = "Dr. Bilal Saeed"
    preferred_branch: Optional[str] = "Gulberg Lahore"
    initial_complaint: Optional[str] = None

class DoctorLoginRequest(BaseModel):
    email: str
    password: str


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


@app.post("/api/patients/signup")
def patient_signup(req: PatientSignupRequest):
    """Registers a new patient with MRN, stores long-term memory, and returns profile."""
    record = memory_manager.register_patient(req.model_dump())

    # Sync into SQLite EHR patients table if available
    if db:
        try:
            import json
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                INSERT OR IGNORE INTO patients (
                    id, mrn, cnic, full_name, gender, date_of_birth, phone, email, city, address,
                    known_allergies, chronic_conditions, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record["patient_id"],
                    record["mrn"],
                    f"42101-{uuid.uuid4().hex[:7]}-1",
                    record["patient_name"],
                    record.get("gender", "Unspecified"),
                    f"{1995 - int(record.get('age', 30))}-01-01",
                    record.get("phone", ""),
                    f"{record['patient_name'].lower().replace(' ', '.')}@example.com",
                    record.get("preferred_branch", "Lahore").split()[0],
                    f"Near {record.get('preferred_branch', 'City Care')}",
                    json.dumps(record.get("known_allergies", [])),
                    json.dumps(record.get("chronic_conditions", [])),
                    datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
        except Exception as e:
            print(f"[Patient Signup DB Note]: {e}")

    return {
        "success": True,
        "message": f"Patient {record['patient_name']} registered successfully with MRN {record['mrn']}!",
        "patient": record
    }


@app.get("/api/doctor/credentials")
def get_doctor_credentials():
    """Returns verified doctor credentials for 1-click login and testing."""
    return {"accounts": DOCTOR_ACCOUNTS}


@app.post("/api/doctor/login")
def doctor_login(req: DoctorLoginRequest):
    """Authenticates doctor against staff credentials."""
    clean_email = req.email.strip().lower()
    for d in DOCTOR_ACCOUNTS:
        if d["email"].lower() == clean_email and d["password"] == req.password.strip():
            return {
                "success": True,
                "token": f"token_{d['id']}_{int(time.time())}",
                "doctor": {
                    "id": d["id"],
                    "email": d["email"],
                    "name": d["name"],
                    "specialty": d["specialty"],
                    "branch": d["branch"],
                    "role": d["role"],
                    "pmdc_number": d["pmdc_number"]
                }
            }
    raise HTTPException(status_code=401, detail="Invalid doctor credentials. Please use provided staff accounts.")


@app.get("/api/doctor/appointments")
def get_doctor_appointments(doctor_name: Optional[str] = None):
    """Retrieves all scheduled appointments with patient details and status."""
    appointments = []
    if db:
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                query = """
                SELECT a.id, a.booking_reference, a.patient_id, a.scheduled_start, a.scheduled_end,
                       a.urgency_tier, a.status, a.reason_for_visit,
                       p.full_name as doctor_name, p.specialty as doctor_specialty,
                       b.name as branch_name,
                       pt.full_name as patient_name, pt.mrn as patient_mrn, pt.phone as patient_phone
                FROM appointments a
                LEFT JOIN practitioners p ON a.practitioner_id = p.id
                LEFT JOIN clinic_branches b ON a.branch_id = b.id
                LEFT JOIN patients pt ON a.patient_id = pt.id OR a.patient_id = pt.mrn
                ORDER BY a.scheduled_start DESC
                LIMIT 60
                """
                cur.execute(query)
                rows = [dict(r) for r in cur.fetchall()]

                for r in rows:
                    if doctor_name and doctor_name.lower() not in (r.get("doctor_name") or "").lower():
                        continue
                    if not r.get("patient_name"):
                        mem = memory_manager.find_patient_memory(r.get("patient_id") or "")
                        if mem:
                            r["patient_name"] = mem.get("patient_name")
                            r["patient_mrn"] = mem.get("mrn")
                            r["patient_phone"] = mem.get("phone")
                        else:
                            r["patient_name"] = "Registered Patient"
                    appointments.append(r)
        except Exception as e:
            print(f"[Appointments Query Error]: {e}")

    return {"appointments": appointments, "count": len(appointments)}


@app.get("/api/patients/{identifier}/history")
def get_patient_full_history(identifier: str):
    """
    Retrieves complete past medical dossier for a patient:
    - Long-term memory profile
    - Past visit history & complaints timeline
    - EHR Encounters with SOAP notes
    - Laboratory observations with normal/abnormal flags
    - Prescriptions & safety checks
    - Latest Pre-Visit SOAP Brief
    """
    mem = memory_manager.find_patient_memory(identifier) or {}
    mrn = mem.get("mrn") or identifier
    patient_id = mem.get("patient_id") or identifier

    encounters = []
    labs = []
    meds = []

    if db:
        db_p = db.find_patient_by_mrn(mrn) or db.find_patient_by_id(patient_id) or db.find_patient_by_phone(mem.get("phone", ""))
        target_pid = db_p["id"] if db_p else patient_id

        try:
            encounters = db.get_patient_encounters(target_pid)
        except Exception:
            encounters = []

        try:
            labs = db.get_patient_observations(target_pid)
        except Exception:
            labs = []

        try:
            meds = db.get_patient_medications(target_pid)
        except Exception:
            meds = []

    # Pre-visit SOAP brief
    sample_intake = {
        "chief_complaint": mem.get("past_complaints", ["Clinical Outpatient Consultation"])[-1] if mem.get("past_complaints") else "Clinical Outpatient Consultation",
        "duration": "4 days",
        "severity": 4,
        "allergies": mem.get("known_allergies", []),
        "medical_history": mem.get("chronic_conditions", [])
    }
    soap = clinical_summary_agent.generate_soap_note(sample_intake, patient_id)
    soap_dict = soap.model_dump() if hasattr(soap, "model_dump") else dict(soap)

    return {
        "patient_id": patient_id,
        "patient_name": mem.get("patient_name", "Valued Patient"),
        "mrn": mrn,
        "phone": mem.get("phone", "N/A"),
        "age": mem.get("age", 42),
        "gender": mem.get("gender", "Unspecified"),
        "preferred_doctor": mem.get("preferred_doctor_name", "Dr. Bilal Saeed"),
        "preferred_branch": mem.get("preferred_branch", "Gulberg Lahore"),
        "preferred_language": mem.get("preferred_language", "English"),
        "known_allergies": mem.get("known_allergies", []),
        "chronic_conditions": mem.get("chronic_conditions", []),
        "past_complaints": mem.get("past_complaints", []),
        "last_visit_date": mem.get("last_visit_date", "2026-09-06"),
        "encounters": encounters,
        "observations": labs,
        "medications": meds,
        "soap_note": soap_dict
    }


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
            "language": req.language or (patient_mem.get("preferred_language") if patient_mem else "Urdu"),
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
        if req.language:
            state["language"] = req.language

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

    def _serialize_msg(m: Any) -> Dict[str, Any]:
        if isinstance(m, dict):
            return m
        role = "assistant" if getattr(m, "type", "") == "ai" else "user"
        res = {
            "role": role,
            "content": getattr(m, "content", str(m)),
            "agent": getattr(m, "name", "ClinicalAssistant"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        for attr in ["is_pending_review", "is_approved_by_doctor", "is_emergency", "appointment_card"]:
            if hasattr(m, attr):
                res[attr] = getattr(m, attr)
        return res

    raw_msgs = updated_state.get("messages", [])
    serialized_msgs = [_serialize_msg(m) for m in raw_msgs]

    # 4. Extract latest assistant message
    latest_reply = "Hum aap ki madad ke liye hazir hain."
    for m in reversed(serialized_msgs):
        if m.get("role") == "assistant":
            latest_reply = m.get("content", "")
            break

    latency_ms = (time.time() - t0) * 1000

    return {
        "session_id": session_id,
        "reply": latest_reply,
        "messages": serialized_msgs,
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
            role = m.get("role") if isinstance(m, dict) else getattr(m, "type", "")
            if role in ("assistant", "ai"):
                resumed_reply = m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
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
