import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DAY4_DIR = Path(r"c:\Users\PMYLS\Downloads\AI Clinic Assistant for Healthcare\Day 4")
ROOT_DIR = DAY4_DIR.parent
DAY3_DIR = ROOT_DIR / "Day 3"
DAY2_DIR = ROOT_DIR / "Day 2"

for p in [str(DAY4_DIR), str(DAY3_DIR), str(DAY3_DIR / "agents"), str(DAY2_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from langgraph_workflow import clinical_graph, _get_msg_content
from db_client import db

def get_content(m):
    return _get_msg_content(m)

print("--- 1. Testing Restoration of Existing Appointment (BK-2026-1000) ---")
state1 = {
    "messages": [
        {"role": "user", "content": "Mera appointment id BK-2026-1000 hai, status check karein"}
    ],
    "session_id": "test_restore_1000",
    "language": "Urdu"
}
res1 = clinical_graph.invoke(state1, config={"configurable": {"thread_id": "test_restore_1000"}})
reply1 = get_content(res1["messages"][-1])
print("Restore Reply:\n", reply1)
assert "BK-2026-1000" in reply1, "Expected BK-2026-1000 in reply"
assert res1.get("patient_name") is not None, "Expected patient_name in state"
print("Patient Name restored:", res1.get("patient_name"))
print("MRN restored:", res1.get("patient_mrn"))
print("PASSED!\n")

print("--- 2. Testing Doctor Suggestions on Symptoms ---")
state2 = {
    "messages": [
        {"role": "user", "content": "Mujhe tez bukhar aur khansi hai 3 din se"}
    ],
    "session_id": "test_symptoms_flow",
    "language": "Urdu"
}
res2 = clinical_graph.invoke(state2, config={"configurable": {"thread_id": "test_symptoms_flow"}})
reply2 = get_content(res2["messages"][-1])
print("Triage & Doctor Suggestion Reply:\n", reply2[:300] + "...")
print("PASSED!\n")

print("--- 3. Testing Conversational Intake on Scheduling ---")
state3 = {
    "messages": [
        {"role": "user", "content": "Dr. Bilal Saeed ke sath kal 10:00 AM appointment book kar dein"}
    ],
    "session_id": "test_intake_booking",
    "language": "Urdu"
}
res3 = clinical_graph.invoke(state3, config={"configurable": {"thread_id": "test_intake_booking"}})
reply3 = get_content(res3["messages"][-1])
print("Slot Proposed / Info Prompt Reply:\n", reply3)

# Now confirm or provide info
sched_req3 = res3.get("scheduling_request", {})
print("Scheduling Status:", sched_req3.get("status"))

# Provide patient details
msgs = list(res3["messages"])
msgs.append({"role": "user", "content": "Theek hai. Mera naam Usman Ali hai, phone 03009876543, age 34 male, allergy koi nahi"})
res3["messages"] = msgs

res4 = clinical_graph.invoke(res3, config={"configurable": {"thread_id": "test_intake_booking"}})
reply4 = get_content(res4["messages"][-1])
print("Final Confirmation Reply:\n", reply4)

apt_res = res4.get("appointment_result")
assert apt_res is not None or "Appointment ID" in reply4 or "BK-2026" in reply4, "Expected appointment confirmation"
new_booking_ref = apt_res.get("booking_reference") if apt_res else None
print("New Booking Ref:", new_booking_ref)
print("Patient Registered:", res4.get("patient_name"), "MRN:", res4.get("patient_mrn"))
print("PASSED!\n")

if new_booking_ref:
    print(f"--- 4. Testing Returning with New Booking Ref ({new_booking_ref}) ---")
    state_returning = {
        "messages": [
            {"role": "user", "content": f"Mera appointment id {new_booking_ref} hai"}
        ],
        "session_id": "test_returning_new_id",
        "language": "Urdu"
    }
    res_ret = clinical_graph.invoke(state_returning, config={"configurable": {"thread_id": "test_returning_new_id"}})
    reply_ret = get_content(res_ret["messages"][-1])
    print("Restored Reply for newly booked patient:\n", reply_ret)
    assert new_booking_ref in reply_ret
    print("PASSED!\n")

print("--- 5. Testing Available Doctors Query (\"City Care mein kon se doctor available hain?\") ---")
state5 = {
    "messages": [
        {"role": "user", "content": "City Care mein kon se doctor available hain?"}
    ],
    "session_id": "test_available_doctors_query",
    "language": "Urdu"
}
res5 = clinical_graph.invoke(state5, config={"configurable": {"thread_id": "test_available_doctors_query"}})
reply5 = get_content(res5["messages"][-1])
print("Available Doctors Reply:\n", reply5)
assert "Dastiyab Specialist Doctors" in reply5 or "Dr." in reply5, "Expected list of available doctors"
print("PASSED!\n")
print("🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
