"""
Comprehensive End-to-End Test for Doctor Prescription & Fulfillment Workflow:
1. Book an appointment -> status 'booked'
2. Restore appointment in chat -> status 'booked' (pending prescription)
3. Doctor issues prescription from portal -> status changes to 'fulfilled'
4. Restore appointment in chat -> status 'fulfilled', displays diagnosis, medicines list, and PDF link
5. Fetch prescription PDF endpoint -> verify HTTP 200, application/pdf, and valid PDF bytes
"""

import urllib.request
import urllib.parse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("==================================================================")
    print("TEST: End-to-End Doctor Prescription & Chat Fulfillment Workflow")
    print("==================================================================")

    import random
    from datetime import datetime, timezone, timedelta
    random_days = random.randint(20, 90)
    random_hour = random.choice([9, 10, 11, 12, 14, 15, 16])
    random_min = random.choice([0, 20, 40])
    slot_dt = datetime.now(timezone.utc) + timedelta(days=random_days, hours=random_hour, minutes=random_min)
    slot_iso = slot_dt.strftime("%Y-%m-%dT%H:%M:00Z")

    booking_payload = {
        "patient_id": f"p_test_e2e_{random.randint(100, 999)}",
        "doctor_id": "doc_1",
        "branch_id": "b1",
        "slot_iso": slot_iso,
        "reason": "Severe tension headache and eye strain for 3 days",
        "urgency": "ROUTINE",
        "patient_name": "Tariq Mahmood",
        "patient_email": "tariq.m@example.com"
    }

    req = urllib.request.Request(
        f"{BASE_URL}/api/appointments/book",
        data=json.dumps(booking_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        book_res = json.loads(resp.read().decode())
    
    assert book_res.get("success"), f"Booking failed: {book_res}"
    booking_ref = book_res.get("booking_reference")
    print(f"Booked successfully! Reference: #{booking_ref}, Doctor: {book_res.get('doctor_name')}")

    # 2. Check initial status via appointment restore
    print("\n--- Step 2: Chat Status Before Prescription (Must be 'booked') ---")
    chat_payload_1 = {
        "session_id": "session_test_rx_1",
        "message": f"Mera appointment status check karein #{booking_ref}",
        "language": "Urdu"
    }
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=json.dumps(chat_payload_1).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req2) as resp:
        chat_res_1 = json.loads(resp.read().decode())
    
    chat_msg_1 = chat_res_1.get("reply") or chat_res_1.get("response", "")
    print(f"Chat Response (Initial):\n{chat_msg_1[:250]}...")
    assert "booked" in chat_msg_1.lower(), f"Expected 'booked' in chat response before prescription: {chat_msg_1}"
    assert "pending" in chat_msg_1.lower() or "dawaiyan" in chat_msg_1.lower(), "Expected pending notice before prescription"
    print("SUCCESS: Chat correctly reported status 'booked' with pending consultation notice.")

    # 3. Doctor issues prescription from portal
    print("\n--- Step 3: Doctor Issues Prescription from Appointment Portal ---")
    prescribe_payload = {
        "appointment_id": booking_ref,
        "diagnosis": "Acute Tension Headache / Tension Cephalea with Cervical Muscle Spasm",
        "medicines": [
            {
                "drug_name": "Tab Panadol Extra (Paracetamol + Caffeine)",
                "dosage": "500mg/65mg",
                "frequency": "Twice daily after meals",
                "duration": "3 days",
                "instructions": "Take with a full glass of water. Avoid taking on empty stomach."
            },
            {
                "drug_name": "Tab Sandomigran (Pizotifen)",
                "dosage": "0.5mg",
                "frequency": "Once daily at bedtime",
                "duration": "5 days",
                "instructions": "Take before sleeping to relax cranial vascular spasm."
            },
            {
                "drug_name": "Tab Myonal (Eperisone HCl)",
                "dosage": "50mg",
                "frequency": "Twice daily",
                "duration": "5 days",
                "instructions": "Muscle relaxant for neck tension. Take after meals."
            }
        ],
        "advice": "Adequate hydration (2-3 liters/day), reduce screen exposure, and take adequate rest. Contact clinic if pain persists.",
        "doctor_name": "Dr. Bilal Saeed",
        "doctor_specialty": "General Medicine & Internal Medicine",
        "pmdc_number": "PMDC-22280-P",
        "branch_name": "City Care Clinics — Gulberg Lahore"
    }

    req3 = urllib.request.Request(
        f"{BASE_URL}/api/doctor/prescribe",
        data=json.dumps(prescribe_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req3) as resp:
        prescribe_res = json.loads(resp.read().decode())
    
    assert prescribe_res.get("success"), f"Prescribe failed: {prescribe_res}"
    assert prescribe_res.get("status") == "fulfilled", f"Expected status 'fulfilled', got {prescribe_res.get('status')}"
    print(f"Doctor Prescription Successfully Saved! Status updated to: {prescribe_res.get('status')}")

    # 4. Check status in Chat on Return (Must be 'fulfilled' with medicines list & PDF link)
    print("\n--- Step 4: Patient Returns to Chat (Must be 'fulfilled' with Rx Details & PDF Link) ---")
    chat_payload_2 = {
        "session_id": "session_test_rx_2",
        "message": f"Mera record restore karein #{booking_ref}",
        "language": "Urdu"
    }
    req4 = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=json.dumps(chat_payload_2).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req4) as resp:
        chat_res_2 = json.loads(resp.read().decode())
    
    chat_msg_2 = chat_res_2.get("reply") or chat_res_2.get("response", "")
    print(f"\nChat Response (After Prescription):\n{chat_msg_2}\n")
    assert "fulfilled" in chat_msg_2.lower(), f"Expected 'fulfilled' in chat response after prescription: {chat_msg_2}"
    assert "panadol extra" in chat_msg_2.lower(), f"Expected medicine Panadol Extra in chat response: {chat_msg_2}"
    assert "sandomigran" in chat_msg_2.lower(), f"Expected medicine Sandomigran in chat response: {chat_msg_2}"
    assert "pdf" in chat_msg_2.lower(), f"Expected PDF download link in chat response: {chat_msg_2}"
    print("SUCCESS: Chat successfully restored record with 'fulfilled' status, medication schedule, and PDF link.")

    # 5. Download the PDF and verify bytes
    print("\n--- Step 5: Verifying PDF Download Endpoint ---")
    pdf_url = f"{BASE_URL}/api/prescriptions/{booking_ref}/pdf"
    with urllib.request.urlopen(pdf_url) as resp:
        content_type = resp.headers.get("Content-Type")
        disposition = resp.headers.get("Content-Disposition")
        pdf_bytes = resp.read()

    print(f"Content-Type: {content_type}")
    print(f"Content-Disposition: {disposition}")
    print(f"Downloaded PDF size: {len(pdf_bytes)} bytes")
    assert content_type == "application/pdf", f"Expected application/pdf, got {content_type}"
    assert pdf_bytes.startswith(b"%PDF-"), f"Downloaded bytes do not start with %PDF- header!"
    assert len(pdf_bytes) > 1000, f"PDF file size too small ({len(pdf_bytes)} bytes)"
    print("SUCCESS: Downloaded authentic, valid PDF with correct headers and size!")

    # 6. Verify Doctor Appointments API returns fulfilled status and has_prescription
    print("\n--- Step 6: Verifying Doctor Appointments Endpoint ---")
    with urllib.request.urlopen(f"{BASE_URL}/api/doctor/appointments") as resp:
        doc_apps = json.loads(resp.read().decode())
    
    matched = [a for a in doc_apps.get("appointments", []) if a.get("booking_reference") == booking_ref]
    assert len(matched) > 0, f"Appointment #{booking_ref} not found in doctor appointments list"
    app_data = matched[0]
    print(f"Doctor Appointments Table Status: {app_data.get('status')}, has_prescription: {app_data.get('has_prescription')}")
    assert app_data.get("status") == "fulfilled", f"Expected status 'fulfilled', got {app_data.get('status')}"
    assert app_data.get("has_prescription") is True, f"Expected has_prescription True"

    print("\n==================================================================")
    print("ALL TESTS PASSED! DOCTOR PRESCRIPTION & FULFILLMENT WORKFLOW VERIFIED")
    print("==================================================================")

if __name__ == "__main__":
    run_test()
