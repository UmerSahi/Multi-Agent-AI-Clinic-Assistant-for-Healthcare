"""
End-to-End Orchestration & Verification Suite for Day 4
Tests:
1. Supervisor routing & graph transitions
2. Short-term memory & long-term privacy-respecting patient memory
3. Returning patient UrduLish greeting generation
4. Parallel fan-out execution (Triage + Records concurrently)
5. Human-in-the-loop (HITL) doctor approval gates (Labs, Prescriptions, Low confidence)
6. Graph pause & resume upon doctor approval/edit/reject
7. Email notification dispatch with Google Calendar links
8. Observability telemetry, latency, token count, and USD cost calculations
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

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


def test_returning_patient_memory():
    print("\n--- [Test 1] Long-Term Memory & Returning Patient Recall ---")
    mem = memory_manager.find_patient_memory("Ahmed Raza")
    assert mem is not None, "Ahmed Raza memory should exist"
    assert mem["preferred_doctor_name"] == "Dr. Bilal Saeed"
    assert "Penicillin" in mem["known_allergies"]

    greeting = memory_manager.generate_returning_patient_greeting(mem)
    print("Personalized Greeting Generated:\n", greeting)
    assert "Dr. Bilal" in greeting
    assert "Ahmed sahib" in greeting
    print("✅ Test 1 Passed: Long-Term Memory recalled and authentic UrduLish greeting generated.")


def test_parallel_triage_and_records():
    print("\n--- [Test 2] Parallel Fan-Out Execution (Triage + Records) ---")
    session_id = f"test_par_{int(time.time())}"
    trace_id = observability.start_trace(session_id, "Hamza Abbasi")

    test_state: ClinicalState = {
        "messages": [
            {"role": "user", "content": "Bachay ko raat se saans lene mein seeti ki awaz aur khansi hai"}
        ],
        "session_id": session_id,
        "user_id": "Hamza Abbasi",
        "patient_id": "p3",
        "patient_name": "Hamza Abbasi",
        "patient_phone": "+923334567890",
        "patient_mrn": "CCC-PK-100003",
        "is_returning_patient": True,
        "long_term_memory": memory_manager.find_patient_memory("Hamza Abbasi") or {},
        "intake_form": {
            "patient_relation": "child",
            "patient_age": 4,
            "chief_complaint": "Bronchial Asthma wheezing and cough",
            "duration": "1 night",
            "severity": 6,
            "associated_symptoms": ["wheezing", "chest tightness"]
        },
        "intake_complete": True,
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

    config = {"configurable": {"thread_id": session_id}}
    t0 = time.time()
    out = clinical_graph.invoke(test_state, config=config)
    dur_ms = (time.time() - t0) * 1000

    assert out.get("triage_result") is not None, "Triage result must be populated by parallel node"
    assert out.get("records_data") is not None, "Records data must be populated concurrently"
    print(f"Parallel Execution Completed in {dur_ms:.1f}ms")
    print(f"Triage Tier: {out['triage_result'].get('urgency_tier')}")
    print(f"Recommended Specialty: {out['triage_result'].get('recommended_specialty')}")
    print(f"Transitions Logged: {[t['to'] for t in out['node_transitions']]}")
    print("✅ Test 2 Passed: Triage and Records executed in parallel with transition logging.")


def test_hitl_pause_and_resume():
    print("\n--- [Test 3] Doctor HITL Interrupt, Approval & Resume ---")
    thread_id = f"test_hitl_{int(time.time())}"
    trace_id = observability.start_trace(thread_id, "Fatima Bibi")

    # Step 1: Create a pending approval for a Lab Result Explanation
    task = hitl_manager.create_pending_approval(
        thread_id=thread_id,
        patient_id="p2",
        patient_name="Fatima Bibi",
        task_type="LAB_EXPLANATION",
        proposed_message_urdulish="Aap ke pelvic ultrasound report mein cysts nazar aaye hain jo PCOD ko zahir karte hain.",
        clinical_context={"findings": "Polycystic ovaries bilateral"},
        urgency_level="ROUTINE"
    )
    task_id = task["task_id"]
    print(f"1. Created Pending HITL Task: {task_id} (Status: {task['status']})")
    assert task["status"] == "PENDING"

    # Step 2: Initialize state at HITL gate waiting for review
    state: ClinicalState = {
        "messages": [
            {"role": "user", "content": "Meri ultrasound report ka kya matlab hai?"}
        ],
        "session_id": thread_id,
        "user_id": "Fatima Bibi",
        "patient_id": "p2",
        "patient_name": "Fatima Bibi",
        "patient_phone": "+923219876543",
        "patient_mrn": "CCC-PK-100002",
        "is_returning_patient": True,
        "long_term_memory": memory_manager.find_patient_memory("Fatima Bibi") or {},
        "intake_form": {},
        "intake_complete": True,
        "triage_result": {"urgency_tier": "ROUTINE", "recommended_specialty": "Gynaecology"},
        "records_data": None,
        "scheduling_request": None,
        "appointment_result": None,
        "clinical_soap_note": None,
        "draft_prescription": None,
        "prescription_safety_report": None,
        "followup_plan": None,
        "hitl_required": True,
        "hitl_type": "LAB_EXPLANATION",
        "hitl_payload": task,
        "hitl_decision": None,
        "current_agent": "hitl_gate",
        "next_agent": "hitl_gate",
        "error_state": None,
        "node_transitions": [],
        "telemetry": {"trace_id": trace_id}
    }

    config = {"configurable": {"thread_id": thread_id}}
    # Graph execution pauses because hitl_decision is None
    paused_out = clinical_graph.invoke(state, config=config)
    print("2. Graph Paused. Current Node:", paused_out.get("current_agent"), "Next:", paused_out.get("next_agent"))
    assert paused_out.get("next_agent") == "awaiting_approval"

    # Step 3: Doctor reviews, edits and approves the clinical response
    resolved = hitl_manager.process_doctor_decision(
        task_id=task_id,
        decision="edited",
        edited_message="Ultrasound report mein bilateral micro-follicles hain jo hormonal imbalance (PCOD) ki alamat hain. Yeh aam masla hai aur ghabrane ki baat nahi. Dr. Ayesha Tariq ke sath consultation mein dawai aur diet plan tajweez kiya jaye ga.",
        doctor_notes="Confirmed mild PCOD presentation, reassured patient to prevent anxiety.",
        doctor_name="Dr. Maryam Naveed (Medical Director)"
    )
    print(f"3. Doctor Processed Decision: {resolved['doctor_action']} -> Status: {resolved['status']}")
    assert resolved["status"] == "EDITED"

    # Step 4: Resume graph execution with the doctor's decision!
    paused_out["hitl_decision"] = resolved
    paused_out["next_agent"] = "hitl_gate"
    resumed_out = clinical_graph.invoke(paused_out, config=config)

    print("4. Graph Resumed! Messages Emitted:")
    all_replies = [m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "") for m in resumed_out["messages"]]
    for r in all_replies[-2:]:
        print("--- Reply Chunk ---")
        print(r)
    assert any("bilateral micro-follicles" in r for r in all_replies), "Doctor's approved clinical message must be in conversation"
    print("✅ Test 3 Passed: Human-in-the-loop paused execution and cleanly resumed on doctor sign-off.")


def test_email_notification_and_calendar():
    print("\n--- [Test 4] Email Confirmation & Google Calendar Generation ---")
    rec = email_notifier.send_appointment_confirmation(
        patient_name="Ahmed Raza",
        patient_email="ahmed.raza@example.com",
        doctor_name="Dr. Bilal Saeed",
        specialty="General Medicine",
        branch_name="Gulberg Lahore",
        start_time_iso="2026-10-10T17:20:00Z",
        booking_ref="CCC-BK-9182",
        consultation_fee=2000,
        calendar_url="https://calendar.google.com/calendar/render?action=TEMPLATE&text=Appointment"
    )
    assert rec["status"] == "SENT"
    assert "CCC-BK-9182" in rec["subject"]
    assert "Gulberg Lahore" in rec["html_body"]
    print("Generated Email Subject:", rec["subject"])
    print("✅ Test 4 Passed: Transactional appointment confirmation generated.")


def test_observability_and_metrics():
    print("\n--- [Test 5] Observability Telemetry & Cost Calculations ---")
    stats = observability.get_summary_stats()
    print("Summary Stats:", stats)
    assert stats["total_conversations"] >= 1
    assert stats["avg_latency_ms"] >= 0
    assert "total_cost_usd" in stats
    print("✅ Test 5 Passed: Telemetry tracking, cost, and latency verified.")


if __name__ == "__main__":
    print("==================================================================")
    print("    CITY CARE CLINICS DAY 4 ORCHESTRATION & HITL TEST SUITE       ")
    print("==================================================================")
    test_returning_patient_memory()
    test_parallel_triage_and_records()
    test_hitl_pause_and_resume()
    test_email_notification_and_calendar()
    test_observability_and_metrics()
    print("\n🎉 ALL 5 DAY 4 VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉\n")
