import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
DAY4_DIR = Path(r"c:\Users\PMYLS\Downloads\AI Clinic Assistant for Healthcare\Day 4")
ROOT_DIR = DAY4_DIR.parent
DAY3_DIR = ROOT_DIR / "Day 3"
DAY2_DIR = ROOT_DIR / "Day 2"

for p in [str(DAY4_DIR), str(DAY3_DIR), str(DAY3_DIR / "agents"), str(DAY2_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from langgraph_workflow import clinical_graph, _get_msg_content

def get_content(m):
    return _get_msg_content(m)

print("=" * 70)
print("TEST 1: User says 'new patient hun'")
print("=" * 70)
s1 = {
    "messages": [{"role": "user", "content": "new patient hun"}],
    "session_id": "test_s1",
    "language": "Urdu"
}
r1 = clinical_graph.invoke(s1, config={"configurable": {"thread_id": "test_s1"}})
reply1 = get_content(r1["messages"][-1])
print("Assistant Reply:\n", reply1)
assert "khushamdeed" in reply1.lower() or "alamaat" in reply1.lower(), "Expected welcome asking for symptoms"
print("✅ TEST 1 PASSED!\n")

print("=" * 70)
print("TEST 2: User says 'returning patient hun'")
print("=" * 70)
s2 = {
    "messages": [{"role": "user", "content": "returning patient hun"}],
    "session_id": "test_s2",
    "language": "Urdu"
}
r2 = clinical_graph.invoke(s2, config={"configurable": {"thread_id": "test_s2"}})
reply2 = get_content(r2["messages"][-1])
print("Assistant Reply:\n", reply2)
assert "appointment id" in reply2.lower() or "bk-2026" in reply2.lower(), "Expected prompt for appointment id"
print("✅ TEST 2 PASSED!\n")

print("=" * 70)
print("TEST 3 & 4: Multi-turn symptom inquiry: 'sir mein dard ha' -> ask 'kitni or kb sy ha' -> then suggest doctors")
print("=" * 70)
s3 = {
    "messages": [{"role": "user", "content": "sir mein dard ha"}],
    "session_id": "test_s3_multi",
    "language": "Urdu"
}
r3 = clinical_graph.invoke(s3, config={"configurable": {"thread_id": "test_s3_multi"}})
reply3 = get_content(r3["messages"][-1])
print("Turn 1 Assistant Reply (Clarifying kitni or kb sy ha):\n", reply3)
assert "kab se" in reply3.lower() or "shiddat" in reply3.lower() or "1 se 10" in reply3.lower(), "Expected duration & severity question"
print("✅ Turn 1 PASSED: Assistant correctly asked kitni or kb sy ha!\n")

# Now user answers "2 din se hai aur shiddat 6 hai"
msgs = list(r3["messages"])
msgs.append({"role": "user", "content": "2 din se hai aur shiddat 6 hai"})
r3["messages"] = msgs

r4 = clinical_graph.invoke(r3, config={"configurable": {"thread_id": "test_s3_multi"}})
reply4 = get_content(r4["messages"][-1])
print("Turn 2 Assistant Reply (Doctor suggestions):\n", reply4)
assert "Dr." in reply4 or "doctor" in reply4.lower() or "tajweez" in reply4.lower(), "Expected doctor suggestions after answering duration/severity"
print("✅ Turn 2 PASSED: Assistant correctly suggested doctors after details provided!\n")

print("=" * 70)
print("TEST 5: Single message: 'mujhy sir mein dard ha koi doctor bta do jis ko dekha sakun'")
print("=" * 70)
s5 = {
    "messages": [{"role": "user", "content": "mujhy sir mein dard ha koi doctor bta do jis ko dekha sakun"}],
    "session_id": "test_s5_single",
    "language": "Urdu"
}
r5 = clinical_graph.invoke(s5, config={"configurable": {"thread_id": "test_s5_single"}})
reply5 = get_content(r5["messages"][-1])
print("Single-message Assistant Reply:\n", reply5)
assert ("Dr." in reply5 or "doctor" in reply5.lower()) and ("General Medicine" in reply5 or "tajweez" in reply5.lower() or "dastiyab" in reply5.lower()), "Expected doctor options directly"
print("✅ TEST 5 PASSED: Assistant gave doctor options directly in one turn!\n")

print("=" * 70)
print("TEST 6: Restore previous appointment BK-2026-1000")
print("=" * 70)
s6 = {
    "messages": [{"role": "user", "content": "BK-2026-1000"}],
    "session_id": "test_s6_restore",
    "language": "Urdu"
}
r6 = clinical_graph.invoke(s6, config={"configurable": {"thread_id": "test_s6_restore"}})
reply6 = get_content(r6["messages"][-1])
print("Restore Reply:\n", reply6)
assert "Atif Iqbal" in reply6 or "BK-2026-1000" in reply6, "Expected Atif Iqbal record restored"
print("✅ TEST 6 PASSED!\n")

print("🎉 ALL SPECIFIED SCENARIOS PASSED WITH FLYING COLORS! 🎉")
