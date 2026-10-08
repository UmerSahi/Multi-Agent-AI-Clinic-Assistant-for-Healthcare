"""
Comprehensive End-to-End Verification Test Suite for Day 3 Specialist Agents
City Care Clinics Multi-Agent Healthcare Architecture
Tests all 7 specialist agents:
1. Intake Agent (conversational UrduLish collection & JSON form)
2. Triage Agent (deterministic red flags + LLM urgency classification)
3. Scheduling Agent (specialty routing, doctor search, anti-double-booking, Google Calendar)
4. Records Agent (patient file Q&A, lab observations)
5. Clinical Summary Agent (pre-visit SOAP note with fact/AI segregation)
6. Prescription Safety Agent (allergy, DDI, contraindications, physician banner)
7. Follow-up Agent (care plan, medication schedule, lab reminders, feedback re-triage)
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

# Ensure root directories and .env are always resolved correctly
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
DAY2_DIR = ROOT_DIR / "Day 2"
DAY3_AGENTS_DIR = CURRENT_DIR / "agents"

# Load environment variables explicitly from root
load_dotenv(ROOT_DIR / ".env")

# Configure sys.path for direct script and IDE execution
for p in [str(CURRENT_DIR), str(DAY3_AGENTS_DIR), str(DAY2_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from intake_agent import intake_agent
    from triage_agent import triage_agent
    from scheduling_agent import scheduling_agent
    from records_agent import records_agent
    from clinical_summary_agent import clinical_summary_agent
    from prescription_safety_agent import prescription_safety_agent
    from followup_agent import followup_agent
except ImportError:
    from agents.intake_agent import intake_agent
    from agents.triage_agent import triage_agent
    from agents.scheduling_agent import scheduling_agent
    from agents.records_agent import records_agent
    from agents.clinical_summary_agent import clinical_summary_agent
    from agents.prescription_safety_agent import prescription_safety_agent
    from agents.followup_agent import followup_agent

import db_client


def ensure_database_ready():
    """Verifies that the synthetic clinic database is populated; auto-seeds if empty."""
    try:
        with db_client.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM practitioners")
            count = cur.fetchone()[0]
            if count > 0:
                return
    except Exception:
        pass

    print("[Setup] Seeding local clinic database for testing...")
    seed_script = DAY2_DIR / "seed_database.py"
    if seed_script.exists():
        subprocess.run([sys.executable, str(seed_script)], check=True)


def test_1_intake_agent():
    print("\n--- [Test 1] Intake Agent ---")
    
    # Turn 1: Initial complaint
    turn1 = intake_agent.process_turn("Salam doctor sahab, mujhe 3 din se bukhar aur shadeed gala kharab hai.")
    print(f"Turn 1 Response: {turn1['reply']}")
    assert turn1["is_complete"] is False, "Intake should not be complete on turn 1"
    assert len(turn1["reply"]) > 0, "Should ask a follow-up question"
    
    # Turn 2: Severity and details
    turn2 = intake_agent.process_turn("Dard kafi shadeed hai, taqreeban 7/10. Khansi bhi hai halki.", turn1["form"])
    print(f"Turn 2 Response: {turn2['reply']}")
    
    # Turn 3: Allergies and meds
    turn3 = intake_agent.process_turn("Mujhe Penicillin se allergy hai. Filhal sirf Panadol li hai.", turn2["form"])
    print(f"Turn 3 Response: {turn3['reply']}")
    
    # Turn 4: Relevant history & self
    turn4 = intake_agent.process_turn("Mujhe Sugar (Diabetes) hai. Yeh checkup mere apne liye (self) hai.", turn3["form"])
    print(f"Turn 4 Complete: {turn4['is_complete']}")
    
    final_form = turn4["form"]
    if not turn4["is_complete"]:
        turn5 = intake_agent.process_turn("Koi aur beemari nahi hai, sab bata diya hai.", final_form)
        final_form = turn5["form"]

    assert final_form.get("chief_complaint") is not None, "Chief complaint must be extracted"
    extracted_text = final_form["chief_complaint"].lower()
    assert any(term in extracted_text for term in ["bukhar", "fever", "gala", "throat"]), "Should capture chief complaint"
    print(f"Extracted Form: Complaint='{final_form['chief_complaint']}', Severity={final_form.get('severity')}, Allergies={final_form.get('allergies')}")
    print("✅ Intake Agent: Passed!")
    return final_form


def test_2_triage_agent():
    print("\n--- [Test 2] Triage Agent ---")
    
    # Case A: Life-Threatening Red Flag (Deterministic Tier)
    crit_res = triage_agent.triage({
        "chief_complaint": "Seenay mein shadeed dabao aur dard, bayen baazu mein dard ja raha hai aur paseenay aa rahe hain",
        "severity": 9,
        "associated_symptoms": ["cold sweats", "nausea"]
    })
    print(f"Emergency Case Result: {crit_res.urgency_tier} (Emergency={crit_res.is_emergency}, Confidence={crit_res.confidence_score})")
    assert crit_res.urgency_tier == "EMERGENCY", "Must flag acute coronary syndrome as EMERGENCY"
    assert crit_res.is_emergency is True, "Must flag is_emergency as True"
    assert crit_res.confidence_score == 1.0, "Rule-based tier has confidence 1.0"
    assert crit_res.escalation_message_urdulish is not None, "Must include 1122 escalation message"
    
    # Case B: Urgent non-emergency case
    urg_res = triage_agent.triage({
        "chief_complaint": "4 saal ke bachay ko tez bukhar 103 F hai aur achanak kaan mein shadeed dard",
        "severity": 8,
        "associated_symptoms": ["vomiting", "irritability"]
    })
    print(f"Urgent Case Result: {urg_res.urgency_tier} (Confidence={urg_res.confidence_score})")
    assert urg_res.urgency_tier in ["URGENT", "EMERGENCY"], "Should triage acute high pediatric fever as URGENT"
    
    # Case C: Routine case
    rout_res = triage_agent.triage({
        "chief_complaint": "Chehre par daanay aur keel pichle 2 mahine se hain",
        "severity": 3,
        "associated_symptoms": []
    })
    print(f"Routine Case Result: {rout_res.urgency_tier} (Confidence={rout_res.confidence_score})")
    assert rout_res.urgency_tier == "ROUTINE", "Acne should triage as ROUTINE"
    
    print("✅ Triage Agent: Passed!")


def test_3_scheduling_agent():
    print("\n--- [Test 3] Scheduling Agent ---")
    
    # 1. Symptom Mapping
    spec_skin = scheduling_agent.map_symptoms_to_specialty("Jild par khushk dhabay aur daanay")
    print(f"Symptom 'Jild par daanay' -> Specialty: {spec_skin}")
    assert spec_skin == "Dermatology", "Should map skin rash to Dermatology"
    
    spec_heart = scheduling_agent.map_symptoms_to_specialty("Dil ki dharkan tez aur high blood pressure")
    print(f"Symptom 'Dil ki dharkan' -> Specialty: {spec_heart}")
    assert spec_heart == "Cardiology", "Should map heart palpitations to Cardiology"
    
    # 2. Find Doctors
    doctors = scheduling_agent.find_doctors(specialty="General Medicine", branch_city="Lahore")
    print(f"Found {len(doctors)} General Medicine doctors in Lahore")
    assert len(doctors) > 0, "Should find at least 1 doctor"
    target_doc = doctors[0]
    
    # 3. Query available slots
    target_date = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")
    slots = scheduling_agent.get_available_slots(
        doctor_id=target_doc["id"],
        target_date_str=target_date
    )
    print(f"Found {len(slots)} available slots for Dr. {target_doc['full_name']} on {target_date}")
    assert len(slots) > 0, "Should find at least 1 slot"
    selected_slot = slots[0]
    
    # 4. Book Appointment
    patient_id = "test_patient_day3_01"
    booking = scheduling_agent.book_appointment(
        patient_id=patient_id,
        doctor_id=target_doc["id"],
        branch_id=target_doc.get("branch_id", "b1"),
        slot_iso=selected_slot["slot_start"],
        reason="Fever and throat pain consultation"
    )
    print(f"Booking Status: Success={booking.get('success')}, Appt ID: {booking.get('appointment_id')}")
    assert booking.get("success") is True, f"Booking must succeed: {booking.get('error')}"
    assert "google_calendar_url" in booking, "Must include Google Calendar URL"
    
    # 5. Anti-Double Booking Test
    double_booking = scheduling_agent.book_appointment(
        patient_id="test_patient_day3_02",
        doctor_id=target_doc["id"],
        branch_id=target_doc.get("branch_id", "b1"),
        slot_iso=selected_slot["slot_start"],
        reason="Checkup attempt on same slot"
    )
    print(f"Double-Booking Prevention Check: Success={double_booking.get('success')} (Error: {double_booking.get('error')})")
    assert double_booking.get("success") is False, "Must prevent double booking on the same slot"
    
    # 6. Anti-Past-Booking Test
    past_slot = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    past_booking = scheduling_agent.book_appointment(
        patient_id=patient_id,
        doctor_id=target_doc["id"],
        branch_id=target_doc.get("branch_id", "b1"),
        slot_iso=past_slot,
        reason="Past date checkup"
    )
    print(f"Past-Booking Prevention Check: Success={past_booking.get('success')}")
    assert past_booking.get("success") is False, "Must reject booking in the past"
    
    # 7. Cancellation
    cancel_res = scheduling_agent.cancel_appointment(
        appointment_id=booking["appointment_id"],
        reason="Patient has travel emergency"
    )
    print(f"Cancellation Check: Success={cancel_res.get('success')}")
    assert cancel_res.get("success") is True, "Cancellation must succeed"
    
    print("✅ Scheduling Agent: Passed!")


def test_4_records_and_summary_agents():
    print("\n--- [Test 4] Records & Clinical Summary Agents ---")
    
    # 1. Records Agent Q&A
    with db_client.db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients LIMIT 1")
        row = cur.fetchone()
    assert row is not None, "Synthetic database must have patients"
    sample_pt = dict(row)
    pt_id = sample_pt["id"]
    pt_mrn = sample_pt["mrn"]
    pt_name = sample_pt["full_name"]
    print(f"Testing Records Agent on Patient: {pt_name} (MRN: {pt_mrn})")
    
    rec_ans = records_agent.answer_patient_query(
        patient_identifier=pt_mrn,
        query="Meri pichli reports aur dawaiyon ki maloomat batayein."
    )
    print(f"Records Agent Response (Excerpt): {rec_ans['answer'][:200]}...")
    assert len(rec_ans.get("answer", "")) > 50, "Should return informative UrduLish response"
    assert rec_ans.get("success") is True, "Patient record should be found"
    
    # 2. Clinical Summary Agent (Pre-visit SOAP note)
    intake_data = {
        "patient_name": pt_name,
        "chief_complaint": "Seenay mein jalan aur khatti dakarein pichle 2 hafton se",
        "duration": "2 haftay",
        "severity": 6,
        "associated_symptoms": ["matli", "khana khane ke baad pait mein dard"],
        "allergies": ["Penicillin"],
        "current_medications": ["Risek 20mg"],
        "medical_history": ["Hypertension"]
    }
    soap = clinical_summary_agent.generate_soap_note(intake_data)
    print(f"Generated SOAP Note Title: {soap.patient_name} - {soap.timestamp}")
    print(f"Section 1 (Subjective Facts): {soap.subjective_patient_reported['chief_complaint']}")
    print(f"Section 3 (AI Differentials): {soap.assessment_ai_considerations['ai_differential_considerations']}")
    
    # Verify strict demarcation
    assert "SECTION 1: SUBJECTIVE" in soap.formatted_markdown
    assert "SECTION 3: ASSESSMENT" in soap.formatted_markdown
    assert "DISCLAIMER" in soap.formatted_markdown
    print("✅ Records & Clinical Summary Agents: Passed!")
    return soap


def test_5_prescription_safety_and_followup():
    print("\n--- [Test 5] Prescription Safety & Follow-up Agents ---")
    
    # 1. Prescription Safety Agent
    # Patient has Penicillin allergy, doctor drafts Augmentin (Amoxicillin/Clavulanate)
    safety_rep = prescription_safety_agent.review_draft_prescription(
        proposed_drugs=["Augmentin 625mg", "Panadol 500mg"],
        patient_allergies=["Penicillin"],
        patient_age=35,
        is_pregnant=False
    )
    print(f"Safety Tier: {safety_rep.safety_tier}")
    print(f"Physician Alert Banner: {safety_rep.doctor_alert_banner}")
    assert safety_rep.is_safe is False, "Must catch Penicillin allergy clash with Augmentin"
    assert "CRITICAL" in safety_rep.safety_tier or "WARNING" in safety_rep.safety_tier
    assert "⚠️" in safety_rep.doctor_alert_banner or "ALERT" in safety_rep.doctor_alert_banner
    
    # 2. Follow-up Agent
    followup_plan = followup_agent.generate_care_plan(
        patient_name="Hamza Abbasi",
        doctor_name="Dr. Usman Tariq",
        prescribed_meds=[
            {"drug_name": "Cefixime 400mg", "frequency_per_day": 1},
            {"drug_name": "Panadol 500mg", "frequency_per_day": 3}
        ],
        advised_labs=["Complete Blood Count (CBC)"],
        followup_days=5
    )
    print(f"Follow-up Plan Created! Recommendation: {followup_plan.followup_visit_recommendation}")
    print(f"Day 1 Outreach Message: {followup_plan.outreach_messages['day_1_adherence_check'][:160]}...")
    assert len(followup_plan.medication_schedule) == 2
    assert len(followup_plan.outreach_messages) >= 3
    
    # 3. Patient Feedback Re-Triage
    # Patient reports worsening severe symptoms
    fb = followup_agent.process_patient_feedback(
        "Dawai shuru ki hai lekin saans bohot phool raha hai aur seenay mein dabao barh gaya hai!"
    )
    print(f"Patient Feedback Evaluation: Status={fb['status']}, Action={fb['action']}")
    assert fb["status"] == "ESCALATION_REQUIRED", "Must escalate worsening severe respiratory/cardiac symptoms"
    assert fb["action"] == "TRIGGER_RE_TRIAGE", "Must trigger re-triage workflow"
    
    print("✅ Prescription Safety & Follow-up Agents: Passed!")


def main():
    print("=" * 70)
    print("🏥 CITY CARE CLINICS — DAY 3 SPECIALIST AGENTS END-TO-END SUITE")
    print("=" * 70)
    
    ensure_database_ready()
    test_1_intake_agent()
    test_2_triage_agent()
    test_3_scheduling_agent()
    test_4_records_and_summary_agents()
    test_5_prescription_safety_and_followup()
    
    print("\n" + "=" * 70)
    print("🎉 ALL DAY 3 SPECIALIST AGENT VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
