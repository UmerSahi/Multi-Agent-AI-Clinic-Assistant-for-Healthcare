import sqlite3
import json
import uuid
from datetime import datetime, timezone

db_path = "Day 2/data/clinic_local.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Ensure patients table has the official test patients with correct MRN and Phone
patients_data = [
    {
        "id": "p1",
        "mrn": "CCC-PK-100001",
        "cnic": "35201-1111111-1",
        "full_name": "Ahmed Raza",
        "gender": "Male",
        "dob": "1981-04-12",
        "phone": "+923001234567",
        "email": "ahmed.raza@example.com",
        "city": "Lahore",
        "address": "Gulberg III, Lahore",
        "allergies": ["Penicillin"],
        "conditions": ["Hypertension"]
    },
    {
        "id": "p2",
        "mrn": "CCC-PK-100002",
        "cnic": "35201-2222222-2",
        "full_name": "Fatima Bibi",
        "gender": "Female",
        "dob": "1997-09-25",
        "phone": "+923219876543",
        "email": "fatima.bibi@example.com",
        "city": "Lahore",
        "address": "DHA Phase 5, Lahore",
        "allergies": ["Sulfa drugs"],
        "conditions": ["PCOD"]
    },
    {
        "id": "p3",
        "mrn": "CCC-PK-100003",
        "cnic": "61101-3333333-3",
        "full_name": "Hamza Abbasi",
        "gender": "Male",
        "dob": "2017-02-14",
        "phone": "+923334567890",
        "email": "hamza.abbasi@example.com",
        "city": "Islamabad",
        "address": "F-8 Markaz, Islamabad",
        "allergies": [],
        "conditions": ["Bronchial Asthma"]
    },
    {
        "id": "p4",
        "mrn": "CCC-PK-100004",
        "cnic": "35201-4444444-4",
        "full_name": "Nazia Abbasi",
        "gender": "Female",
        "dob": "1988-11-30",
        "phone": "+92-301-8434500",
        "email": "nazia.abbasi4@example.com",
        "city": "Lahore",
        "address": "Johar Town, Lahore",
        "allergies": ["Aspirin"],
        "conditions": ["Type 2 Diabetes"]
    },
    {
        "id": "p5",
        "mrn": "CCC-PK-100005",
        "cnic": "61101-5555555-5",
        "full_name": "Tariq Mahmood",
        "gender": "Male",
        "dob": "1974-06-18",
        "phone": "+92-300-7194416",
        "email": "tariq.mahmood10@example.com",
        "city": "Islamabad",
        "address": "Blue Area, Islamabad",
        "allergies": [],
        "conditions": ["Coronary Artery Disease"]
    }
]

for p in patients_data:
    # Check if patient exists by id or mrn
    cur.execute("SELECT id FROM patients WHERE id = ? OR mrn = ?", (p["id"], p["mrn"]))
    row = cur.fetchone()
    if row:
        cur.execute("""
            UPDATE patients SET
                id = ?, mrn = ?, full_name = ?, gender = ?, date_of_birth = ?,
                phone = ?, email = ?, city = ?, address = ?,
                known_allergies = ?, chronic_conditions = ?
            WHERE id = ? OR mrn = ?
        """, (
            p["id"], p["mrn"], p["full_name"], p["gender"], p["dob"],
            p["phone"], p["email"], p["city"], p["address"],
            json.dumps(p["allergies"]), json.dumps(p["conditions"]),
            p["id"], p["mrn"]
        ))
    else:
        cur.execute("""
            INSERT INTO patients (
                id, mrn, cnic, full_name, gender, date_of_birth, phone,
                email, city, address, known_allergies, chronic_conditions, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["id"], p["mrn"], p["cnic"], p["full_name"], p["gender"], p["dob"],
            p["phone"], p["email"], p["city"], p["address"],
            json.dumps(p["allergies"]), json.dumps(p["conditions"]),
            datetime.now(timezone.utc).isoformat()
        ))

print(f"Updated {len(patients_data)} patient accounts in SQLite.")

# 2. Get practitioner mapping
cur.execute("SELECT id, full_name, specialty, pmdc_number, branch_id FROM practitioners")
docs = {row[1]: {"id": row[0], "name": row[1], "specialty": row[2], "pmdc": row[3], "branch_id": row[4]} for row in cur.fetchall()}

# Branch mapping
cur.execute("SELECT id, name FROM clinic_branches")
branches = {row[0]: row[1] for row in cur.fetchall()}

# Ensure Dr. Ayesha Tariq doc info
ayesha_doc = docs.get("Dr. Ayesha Tariq") or {
    "id": "doc_ayesha_tariq",
    "name": "Dr. Ayesha Tariq",
    "specialty": "Gynaecology",
    "pmdc": "PMDC-31415-P",
    "branch_id": "22222222-2222-4222-a222-222222222222"
}
bilal_doc = docs.get("Dr. Bilal Saeed") or {
    "id": "doc_1",
    "name": "Dr. Bilal Saeed",
    "specialty": "General Medicine",
    "pmdc": "PMDC-22280-P",
    "branch_id": "11111111-1111-4111-a111-111111111111"
}
usman_doc = docs.get("Dr. Usman Sheikh") or {
    "id": "doc_usman_sheikh",
    "name": "Dr. Usman Sheikh",
    "specialty": "Paediatrics",
    "pmdc": "PMDC-41892-P",
    "branch_id": "44444444-4444-4444-a444-444444444444"
}
maryam_doc = docs.get("Dr. Maryam Naveed") or {
    "id": "doc_3",
    "name": "Dr. Maryam Naveed",
    "specialty": "Cardiology",
    "pmdc": "PMDC-23434-P",
    "branch_id": "11111111-1111-4111-a111-111111111111"
}

# 3. Seeded Historical & Fulfilled Consultations
appointments_and_prescriptions = [
    # FATIMA BIBI (p2)
    {
        "appointment_id": "apt_fatima_p2_visit1",
        "booking_reference": "BK-2026-818AT1",
        "patient_id": "p2",
        "doctor": ayesha_doc,
        "branch_name": "City Care Clinics — DHA Phase 5 Branch",
        "start": "2026-08-18T10:00:00+00:00",
        "end": "2026-08-18T10:20:00+00:00",
        "reason": "Routine Gynaecology Consultation & PCOD Review",
        "status": "fulfilled",
        "rx": {
            "id": "RX-2026-818AT1",
            "diagnosis": "Polycystic Ovarian Syndrome (PCOD) with Mild Dysmenorrhea",
            "medicines": [
                {
                    "medicine_name": "Tab Metformin HCl (Glucophage 500mg)",
                    "drug_name": "Tab Metformin HCl (Glucophage 500mg)",
                    "dosage": "500mg",
                    "frequency": "Once daily with dinner",
                    "duration": "30 days",
                    "instructions": "Take with meal to avoid gastric discomfort."
                },
                {
                    "medicine_name": "Tab Inositol + Folic Acid (Inofolic 2000mg/200mcg)",
                    "drug_name": "Tab Inositol + Folic Acid (Inofolic 2000mg/200mcg)",
                    "dosage": "1 sachet",
                    "frequency": "Twice daily dissolved in water",
                    "duration": "30 days",
                    "instructions": "Ovarian metabolic regulation support."
                },
                {
                    "medicine_name": "Tab Mefenamic Acid (Ponstan 500mg)",
                    "drug_name": "Tab Mefenamic Acid (Ponstan 500mg)",
                    "dosage": "500mg",
                    "frequency": "As needed for pelvic pain (max 3/day)",
                    "duration": "5 days",
                    "instructions": "Take after meals only during cycle pain."
                }
            ],
            "advice": "Maintain low GI diet, 30 mins daily brisk walk. Repeat pelvic ultrasound and fasting insulin in 6 weeks."
        }
    },
    {
        "appointment_id": "apt_fatima_p2_visit2",
        "booking_reference": "BK-2026-610AT2",
        "patient_id": "p2",
        "doctor": ayesha_doc,
        "branch_name": "City Care Clinics — DHA Phase 5 Branch",
        "start": "2026-06-10T11:20:00+00:00",
        "end": "2026-06-10T11:40:00+00:00",
        "reason": "Pelvic scan review & CBC blood test",
        "status": "fulfilled",
        "rx": {
            "id": "RX-2026-610AT2",
            "diagnosis": "Mild Microcytic Hypochromic Anemia & Pelvic Scan Review",
            "medicines": [
                {
                    "medicine_name": "Cap Fefol-Vit (Ferrous Sulphate + Vit B-Complex)",
                    "drug_name": "Cap Fefol-Vit (Ferrous Sulphate + Vit B-Complex)",
                    "dosage": "1 capsule",
                    "frequency": "Once daily after lunch",
                    "duration": "30 days",
                    "instructions": "Do not take with tea, coffee, or dairy."
                },
                {
                    "medicine_name": "Tab Vitamin C (Cecon 500mg)",
                    "drug_name": "Tab Vitamin C (Cecon 500mg)",
                    "dosage": "500mg",
                    "frequency": "Once daily",
                    "duration": "30 days",
                    "instructions": "Enhances intestinal iron absorption."
                }
            ],
            "advice": "Increase dietary green leafy vegetables, pomegranate, and lentils. Follow up CBC in 4 weeks."
        }
    },
    # AHMED RAZA (p1)
    {
        "appointment_id": "apt_ahmed_p1_visit1",
        "booking_reference": "BK-2026-915BS1",
        "patient_id": "p1",
        "doctor": bilal_doc,
        "branch_name": "City Care Clinics — Gulberg Branch",
        "start": "2026-09-15T09:40:00+00:00",
        "end": "2026-09-15T10:00:00+00:00",
        "reason": "Hypertension monitoring and routine checkup",
        "status": "fulfilled",
        "rx": {
            "id": "RX-2026-915BS1",
            "diagnosis": "Essential Hypertension Stage 1 (Well-Controlled)",
            "medicines": [
                {
                    "medicine_name": "Tab Amlodipine (Norvasc 5mg)",
                    "drug_name": "Tab Amlodipine (Norvasc 5mg)",
                    "dosage": "5mg",
                    "frequency": "Once daily in morning",
                    "duration": "30 days",
                    "instructions": "Monitor blood pressure regularly."
                },
                {
                    "medicine_name": "Tab Nebivolol (Nebicard 2.5mg)",
                    "drug_name": "Tab Nebivolol (Nebicard 2.5mg)",
                    "dosage": "2.5mg",
                    "frequency": "Once daily",
                    "duration": "30 days",
                    "instructions": "Cardioselective beta-blocker."
                },
                {
                    "medicine_name": "Cap Omega-3 Fish Oil 1000mg",
                    "drug_name": "Cap Omega-3 Fish Oil 1000mg",
                    "dosage": "1 capsule",
                    "frequency": "Once daily",
                    "duration": "30 days",
                    "instructions": "Cardiovascular lipid support."
                }
            ],
            "advice": "Low sodium DASH diet, restrict salt under 2g/day. Record daily morning BP."
        }
    },
    {
        "appointment_id": "apt_ahmed_p1_visit2",
        "booking_reference": "BK-2026-722BS2",
        "patient_id": "p1",
        "doctor": bilal_doc,
        "branch_name": "City Care Clinics — Gulberg Branch",
        "start": "2026-07-22T10:20:00+00:00",
        "end": "2026-07-22T10:40:00+00:00",
        "reason": "Seasonal allergic rhinitis & throat discomfort",
        "status": "fulfilled",
        "rx": {
            "id": "RX-2026-722BS2",
            "diagnosis": "Acute Allergic Rhinitis & Pharyngitis (Patient Penicillin Allergic)",
            "medicines": [
                {
                    "medicine_name": "Tab Levocetirizine (T-Day 5mg)",
                    "drug_name": "Tab Levocetirizine (T-Day 5mg)",
                    "dosage": "5mg",
                    "frequency": "Once daily at night",
                    "duration": "7 days",
                    "instructions": "Non-sedating antihistamine."
                },
                {
                    "medicine_name": "Nasal Spray Fluticasone (Flixonase)",
                    "drug_name": "Nasal Spray Fluticasone (Flixonase)",
                    "dosage": "1 puff each nostril",
                    "frequency": "Twice daily",
                    "duration": "14 days",
                    "instructions": "Shake well before spraying."
                },
                {
                    "medicine_name": "Tab Montelukast (Myteka 10mg)",
                    "drug_name": "Tab Montelukast (Myteka 10mg)",
                    "dosage": "10mg",
                    "frequency": "Once daily at bedtime",
                    "duration": "14 days",
                    "instructions": "Airway anti-inflammatory."
                }
            ],
            "advice": "Warm salt water gargles twice daily. Avoid direct dust and cold air exposure."
        }
    },
    # HAMZA ABBASI (p3 - Child)
    {
        "appointment_id": "apt_hamza_p3_visit1",
        "booking_reference": "BK-2026-902US1",
        "patient_id": "p3",
        "doctor": usman_doc,
        "branch_name": "City Care Clinics — F-8 Markaz Branch",
        "start": "2026-09-02T11:00:00+00:00",
        "end": "2026-09-02T11:20:00+00:00",
        "reason": "Bronchial asthma follow-up and wheezing assessment",
        "status": "fulfilled",
        "rx": {
            "id": "RX-2026-902US1",
            "diagnosis": "Moderate Persistent Pediatric Bronchial Asthma",
            "medicines": [
                {
                    "medicine_name": "Inhaler Salbutamol (Ventolin 100mcg)",
                    "drug_name": "Inhaler Salbutamol (Ventolin 100mcg)",
                    "dosage": "2 puffs",
                    "frequency": "As needed for wheezing (via spacer)",
                    "duration": "15 days",
                    "instructions": "Rinse mouth with water after use."
                },
                {
                    "medicine_name": "Inhaler Budesonide (Pulmicort 200mcg)",
                    "drug_name": "Inhaler Budesonide (Pulmicort 200mcg)",
                    "dosage": "1 puff",
                    "frequency": "Twice daily regularly via spacer",
                    "duration": "30 days",
                    "instructions": "Preventer controller therapy. Use daily."
                },
                {
                    "medicine_name": "Syp Montelukast (Montiget 5mg)",
                    "drug_name": "Syp Montelukast (Montiget 5mg)",
                    "dosage": "1 chewable tablet",
                    "frequency": "Once daily at bedtime",
                    "duration": "30 days",
                    "instructions": "Pediatric leukotriene receptor antagonist."
                }
            ],
            "advice": "Keep bedroom free from carpet dust and pet hair. Always carry rescue inhaler with spacer."
        }
    },
    # NAZIA ABBASI (p4)
    {
        "appointment_id": "apt_nazia_p4_visit1",
        "booking_reference": "BK-2026-805NA1",
        "patient_id": "p4",
        "doctor": bilal_doc,
        "branch_name": "City Care Clinics — Gulberg Branch",
        "start": "2026-08-05T10:40:00+00:00",
        "end": "2026-08-05T11:00:00+00:00",
        "reason": "Type 2 Diabetes Quarterly Glycemic Checkup",
        "status": "fulfilled",
        "rx": {
            "id": "RX-2026-805NA1",
            "diagnosis": "Type 2 Diabetes Mellitus with Good Glycemic Control (Aspirin Sensitive)",
            "medicines": [
                {
                    "medicine_name": "Tab Empagliflozin (Jardiance 10mg)",
                    "drug_name": "Tab Empagliflozin (Jardiance 10mg)",
                    "dosage": "10mg",
                    "frequency": "Once daily in morning",
                    "duration": "30 days",
                    "instructions": "SGLT2 inhibitor. Drink plenty of water."
                },
                {
                    "medicine_name": "Tab Sitagliptin + Metformin (Janumet 50/850mg)",
                    "drug_name": "Tab Sitagliptin + Metformin (Janumet 50/850mg)",
                    "dosage": "1 tablet",
                    "frequency": "Twice daily with meals",
                    "duration": "30 days",
                    "instructions": "Dual glycemic regulation."
                }
            ],
            "advice": "Log fasting blood sugar twice weekly. Daily foot inspection. Follow up HbA1c in 3 months."
        }
    },
    # TARIQ MAHMOOD (p5)
    {
        "appointment_id": "apt_tariq_p5_visit1",
        "booking_reference": "BK-2026-928TM1",
        "patient_id": "p5",
        "doctor": maryam_doc,
        "branch_name": "City Care Clinics — Gulberg Branch",
        "start": "2026-09-28T11:40:00+00:00",
        "end": "2026-09-28T12:00:00+00:00",
        "reason": "Cardiology post-stent outpatient evaluation",
        "status": "fulfilled",
        "rx": {
            "id": "RX-2026-928TM1",
            "diagnosis": "Stable Ischemic Heart Disease / Post-PCI Stent Maintenance",
            "medicines": [
                {
                    "medicine_name": "Tab Rosuvastatin (Crestor 20mg)",
                    "drug_name": "Tab Rosuvastatin (Crestor 20mg)",
                    "dosage": "20mg",
                    "frequency": "Once daily at bedtime",
                    "duration": "30 days",
                    "instructions": "High-intensity lipid management."
                },
                {
                    "medicine_name": "Tab Clopidogrel (Plavix 75mg)",
                    "drug_name": "Tab Clopidogrel (Plavix 75mg)",
                    "dosage": "75mg",
                    "frequency": "Once daily with breakfast",
                    "duration": "30 days",
                    "instructions": "Antiplatelet therapy."
                },
                {
                    "medicine_name": "Tab Bisoprolol (Concor 2.5mg)",
                    "drug_name": "Tab Bisoprolol (Concor 2.5mg)",
                    "dosage": "2.5mg",
                    "frequency": "Once daily in morning",
                    "duration": "30 days",
                    "instructions": "Cardiac rate control."
                }
            ],
            "advice": "Strict low-fat diet. Daily 20-min moderate walking. Immediate clinic contact if chest tightness occurs."
        }
    }
]

# Insert/replace each appointment & prescription
for item in appointments_and_prescriptions:
    doc = item["doctor"]
    cur.execute("""
        INSERT OR REPLACE INTO appointments (
            id, booking_reference, patient_id, practitioner_id, branch_id,
            scheduled_start, scheduled_end, urgency_tier, status, reason_for_visit, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ROUTINE', ?, ?, ?)
    """, (
        item["appointment_id"],
        item["booking_reference"],
        item["patient_id"],
        doc["id"],
        doc.get("branch_id", "11111111-1111-4111-a111-111111111111"),
        item["start"],
        item["end"],
        item["status"],
        item["reason"],
        item["start"]
    ))

    # Prescription
    rx = item["rx"]
    cur.execute("""
        INSERT OR REPLACE INTO prescriptions (
            id, appointment_id, booking_reference, patient_id, practitioner_id,
            doctor_name, doctor_specialty, pmdc_number, branch_name,
            diagnosis, medicines_json, advice, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'fulfilled', ?)
    """, (
        rx["id"],
        item["appointment_id"],
        item["booking_reference"],
        item["patient_id"],
        doc["id"],
        doc["name"],
        doc.get("specialty", "Specialist"),
        doc.get("pmdc", "PMDC-REG"),
        item["branch_name"],
        rx["diagnosis"],
        json.dumps(rx["medicines"]),
        rx["advice"],
        item["start"]
    ))

conn.commit()
print(f"Successfully seeded {len(appointments_and_prescriptions)} appointments with complete doctor prescriptions!")
