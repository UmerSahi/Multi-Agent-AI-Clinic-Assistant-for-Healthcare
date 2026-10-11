import sys
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.extend(['Day 4', 'Day 2', 'Day 3', 'Day 3/agents'])
from langgraph_workflow import build_clinical_graph
from clinical_state import ClinicalState
from memory_manager import memory_manager
from db_client import db

print("Building graph...")
graph = build_clinical_graph()

# ==============================================================================
# TEST CASE 1: Returning patient p2 -> "dubara appointment book krni ha"
# ==============================================================================
print("\n--- TEST CASE 1: Repeat booking for Fatima Bibi (p2) ---")
mem = memory_manager.find_patient_memory("p2")
state: ClinicalState = {
    "messages": [
        {
            "role": "assistant",
            "content": "Assalam-o-Alaikum Fatima sahib! City Care Clinics mein khush-amdeed.\nRecord ke mutabiq aap pichli dafa (2026-08-18) Dr. Ayesha Tariq ko dikhaye thay (DHA Lahore branch mein).\nKya aap dobara Dr. Ayesha Tariq ke saath appointment book karna chahte hain, ya koi nayi takleef ke liye doosray specialist se mashwara chahiye?",
            "agent": "MemoryManager"
        },
        {
            "role": "user",
            "content": "dubara appointment book krni ha"
        }
    ],
    "session_id": "test_sess_p2_1",
    "user_id": "p2",
    "patient_id": "p2",
    "patient_name": "Fatima Bibi",
    "patient_phone": "+923219876543",
    "patient_mrn": "CCC-PK-100002",
    "is_returning_patient": True,
    "language": "Urdu",
    "long_term_memory": mem,
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
    "telemetry": {"trace_id": "tr_test_1"}
}

config = {"configurable": {"thread_id": "test_thread_1"}}
out = graph.invoke(state, config=config)
def get_content(m):
    return getattr(m, "content", "") if hasattr(m, "content") else m.get("content", "")

last_msg = get_content(out["messages"][-1])
print("\n[Case 1 Response]:")
print(last_msg)

assert "Dr. Ayesha Tariq" in last_msg, f"FAIL: Expected Dr. Ayesha Tariq in response, got: {last_msg}"
sched_req = out.get("scheduling_request")
print("Doctor in sched_req:", sched_req.get("doctor_name"))
print("Branch in sched_req:", sched_req.get("branch_name"))
assert sched_req.get("doctor_name") == "Dr. Ayesha Tariq", f"FAIL: doctor_name is {sched_req.get('doctor_name')}"
print(">>> PASS: Test Case 1 passed successfully! Offered Dr. Ayesha Tariq!")

# ==============================================================================
# TEST CASE 2: Patient selects slot 1 ("10:00 AM")
# ==============================================================================
print("\n--- TEST CASE 2: Patient confirms slot 1 (10:00 AM) ---")
out["messages"].append({
    "role": "user",
    "content": "10:00 AM"
})
out2 = graph.invoke(out, config=config)
confirm_msg = get_content(out2["messages"][-1])
print("\n[Case 2 Response]:")
print(confirm_msg)

assert "Dr. Ayesha Tariq" in confirm_msg, f"FAIL: Expected Dr. Ayesha Tariq confirmed, got: {confirm_msg}"
assert "Appointment Confirm Ho Chuki Hai" in confirm_msg or "Confirmed" in confirm_msg
apt_res = out2.get("appointment_result")
print("Confirmed Doctor:", apt_res.get("doctor_name"))
print("Booking Ref:", apt_res.get("booking_reference"))
assert apt_res.get("doctor_name") == "Dr. Ayesha Tariq"
print(">>> PASS: Test Case 2 passed successfully! Booked Dr. Ayesha Tariq!")

# Cleanup created test appointment
if apt_res.get("id"):
    scheduling_agent.cancel_appointment(apt_res["id"], reason="Test cleanup")
    print("Cleaned up test booking:", apt_res.get("id"))

# ==============================================================================
# TEST CASE 3: Patient complains "doctor change q kr diya jb mein ny dubara appointment ka bola ha"
# ==============================================================================
print("\n--- TEST CASE 3: Doctor change complaint handling ---")
# Simulate state where an appointment with Dr. Kiran Raza was mistakenly booked
mock_wrong_booking = {
    "id": "mock_kiran_apt_1",
    "booking_reference": "BK-2026-MOCK1",
    "doctor_name": "Dr. Kiran Raza",
    "status": "booked"
}
state_complaint: ClinicalState = dict(state)
state_complaint["appointment_result"] = mock_wrong_booking
state_complaint["scheduling_request"] = {"status": "CONFIRMED", "booking_reference": "BK-2026-MOCK1"}
state_complaint["messages"] = [
    {
        "role": "assistant",
        "content": "✅ Mubarak Ho! Aap Ki Appointment Confirm Ho Chuki Hai:\n• Doctor: Dr. Kiran Raza"
    },
    {
        "role": "user",
        "content": "doctor change q kr diya jb mein ny dubara appointment ka bola ha"
    }
]

config3 = {"configurable": {"thread_id": "test_thread_3"}}
out3 = graph.invoke(state_complaint, config=config3)
complaint_reply = get_content(out3["messages"][-1])
print("\n[Case 3 Response]:")
print(complaint_reply)

assert "Dr. Ayesha Tariq" in complaint_reply, f"FAIL: Expected Dr. Ayesha Tariq in apology reply, got: {complaint_reply}"
assert "Dr. Kiran Raza" in complaint_reply, f"FAIL: Expected mention of previous doctor in apology, got: {complaint_reply}"
assert "cancel" in complaint_reply.lower(), "FAIL: Expected cancel notification"
assert out3.get("appointment_result") is None, "FAIL: appointment_result should be cleared"
sched_req3 = out3.get("scheduling_request")
assert sched_req3.get("doctor_name") == "Dr. Ayesha Tariq"
print(">>> PASS: Test Case 3 passed successfully! Handled complaint, cancelled wrong doctor, offered Dr. Ayesha Tariq!")

print("\n==========================================")
print("ALL TESTS PASSED WITH ZERO ERRORS!")
print("==========================================")
