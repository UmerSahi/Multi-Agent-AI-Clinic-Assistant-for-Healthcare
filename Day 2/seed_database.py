"""
Synthetic Data Generation & Seeding Engine for City Care Clinics
Generates 5 Clinic Branches, 30 Doctors across 6 Specialties,
500+ Synthetic Pakistani Patients, Appointments, Encounters, and Lab Observations.
Seeds both local SQLite DB and Supabase PostgreSQL.
"""

import os
import json
import random
import uuid
from datetime import datetime, timedelta, date, timezone
from pathlib import Path
from faker import Faker

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Pakistani localized faker
fake = Faker(['en_US'])
Faker.seed(42)
random.seed(42)

# ----------------- Pakistan Specific Reference Sets -----------------
FIRST_NAMES_MALE = [
    "Muhammad", "Ali", "Ahmed", "Usman", "Bilal", "Hamza", "Zubair", "Omer", "Hassan", "Hussein",
    "Tariq", "Khurram", "Imran", "Kamran", "Asad", "Faisal", "Saad", "Waleed", "Haris", "Zeeshan",
    "Junaid", "Shahid", "Farhan", "Noman", "Atif", "Salman", "Adeel", "Rashid", "Rizwan", "Sohail"
]

FIRST_NAMES_FEMALE = [
    "Fatima", "Ayesha", "Zainab", "Maryam", "Sana", "Hira", "Sadia", "Amna", "Mahnoor", "Rabia",
    "Nida", "Iqra", "Sidra", "Bushra", "Khadija", "Samina", "Shazia", "Mehwish", "Zunaira", "Anum",
    "Farah", "Maria", "Huma", "Nazia", "Uzma", "Fariha", "Tahira", "Kiran", "Shaista", "Fozia"
]

LAST_NAMES = [
    "Khan", "Malik", "Chaudhry", "Bhatti", "Qureshi", "Siddiqui", "Sheikh", "Raza", "Ansari", "Mirza",
    "Abbasi", "Butt", "Dar", "Hashmi", "Gillani", "Javed", "Akram", "Iqbal", "Ashraf", "Tariq",
    "Shah", "Rehman", "Aziz", "Saeed", "Mahmood", "Riaz", "Latif", "Ghaffar", "Afzal", "Hameed"
]

CITIES_AREAS = {
    "Lahore": ["Gulberg III", "DHA Phase 5", "Johar Town", "Model Town", "Garden Town", "Wapda Town", "Cantt", "Shadman"],
    "Islamabad": ["F-8 Markaz", "F-10 Markaz", "Blue Area", "G-11/3", "E-11", "I-8 Markaz", "DHA Phase 2", "Bahria Town"],
    "Rawalpindi": ["Satellite Town", "Saddar", "Westridge", "Chaklala Scheme III", "Peshawar Road"]
}

SPECIALTIES = [
    "General Medicine",
    "Paediatrics",
    "Gynaecology",
    "Cardiology",
    "Dermatology",
    "ENT"
]

ALLERGIES_POOL = ["Penicillin", "Sulfa drugs", "Aspirin", "NSAIDs", "Ceftriaxone", "Ibuprofen", "Dust / Pollen", "None"]
CONDITIONS_POOL = ["Hypertension", "Type 2 Diabetes", "Asthma", "Ischemic Heart Disease", "PCOD", "Hyperlipidemia", "GERD", "Hypothyroidism", "None"]
MEDICATIONS_POOL = [
    "Panadol 500mg", "Glucophage 500mg", "Lipiget 20mg", "Loprin 75mg", "Concor 2.5mg",
    "Risek 20mg", "Ventolin Inhaler", "Augmentin 625mg", "Brufen 400mg", "Zestril 5mg"
]

def generate_cnic(city: str) -> str:
    prefix = "35201" if city == "Lahore" else ("61101" if city == "Islamabad" else "37405")
    middle = f"{random.randint(1000000, 9999999)}"
    last = f"{random.randint(1, 9)}"
    return f"{prefix}-{middle}-{last}"

def generate_pakistani_phone() -> str:
    prefix = random.choice(["0300", "0301", "0321", "0333", "0345", "0312", "0331", "0322"])
    num = f"{random.randint(1000000, 9999999)}"
    return f"+92-{prefix[1:]}-{num}"

# ----------------- 1. Branches -----------------
def generate_branches():
    return [
        {
            "id": "11111111-1111-4111-a111-111111111111",
            "branch_code": "CCC-LHR-GLB",
            "name": "City Care Clinics — Gulberg Branch",
            "city": "Lahore",
            "address": "14-C Main Boulevard, Gulberg III, Lahore",
            "phone": "+92-42-35789011",
            "emergency_helpline": "1122",
            "opening_time": "08:00:00",
            "closing_time": "22:00:00",
            "is_active": True
        },
        {
            "id": "22222222-2222-4222-a222-222222222222",
            "branch_code": "CCC-LHR-DHA",
            "name": "City Care Clinics — DHA Phase 5 Branch",
            "city": "Lahore",
            "address": "Plaza 88, Commercial Sector C, DHA Phase 5, Lahore",
            "phone": "+92-42-35712344",
            "emergency_helpline": "1122",
            "opening_time": "08:00:00",
            "closing_time": "22:00:00",
            "is_active": True
        },
        {
            "id": "33333333-3333-4333-a333-333333333333",
            "branch_code": "CCC-LHR-JHT",
            "name": "City Care Clinics — Johar Town Branch",
            "city": "Lahore",
            "address": "Block G-3, M.A. Johar Town, Lahore",
            "phone": "+92-42-35309988",
            "emergency_helpline": "1122",
            "opening_time": "08:00:00",
            "closing_time": "22:00:00",
            "is_active": True
        },
        {
            "id": "44444444-4444-4444-a444-444444444444",
            "branch_code": "CCC-ISB-F8",
            "name": "City Care Clinics — F-8 Markaz Branch",
            "city": "Islamabad",
            "address": "Ayub Market, F-8 Markaz, Islamabad",
            "phone": "+92-51-2856677",
            "emergency_helpline": "1122",
            "opening_time": "08:00:00",
            "closing_time": "22:00:00",
            "is_active": True
        },
        {
            "id": "55555555-5555-4555-a555-555555555555",
            "branch_code": "CCC-ISB-BLU",
            "name": "City Care Clinics — Blue Area Branch",
            "city": "Islamabad",
            "address": "Fazl-ul-Haq Road, Blue Area, Islamabad",
            "phone": "+92-51-2279911",
            "emergency_helpline": "1122",
            "opening_time": "08:00:00",
            "closing_time": "22:00:00",
            "is_active": True
        }
    ]

# ----------------- 2. Practitioners (30 Doctors) -----------------
def generate_practitioners(branches):
    doctors = []
    qualifications = {
        "General Medicine": ["MBBS, FCPS (Medicine)", "MBBS, MRCP (UK)"],
        "Paediatrics": ["MBBS, FCPS (Paediatrics)", "MBBS, DCH, MCPS"],
        "Gynaecology": ["MBBS, FCPS (Obs & Gynae)", "MBBS, MRCOG (UK)"],
        "Cardiology": ["MBBS, FCPS (Cardiology)", "MBBS, MD (Cardiology)"],
        "Dermatology": ["MBBS, FCPS (Dermatology)", "MBBS, MCPS (Dermatology)"],
        "ENT": ["MBBS, FCPS (Otolaryngology)", "MBBS, FRCS (ENT)"]
    }

    # 5 doctors per specialty = 30 doctors
    doc_index = 100
    for specialty in SPECIALTIES:
        for i in range(5):
            gender = "Female" if specialty == "Gynaecology" or (i % 2 == 1 and specialty in ["Paediatrics", "Dermatology"]) else "Male"
            fname = random.choice(FIRST_NAMES_FEMALE) if gender == "Female" else random.choice(FIRST_NAMES_MALE)
            lname = random.choice(LAST_NAMES)
            branch = branches[(len(doctors)) % len(branches)]
            
            weekly_schedule = {
                "Monday": ["09:00-13:00", "17:00-21:00"],
                "Tuesday": ["09:00-13:00", "17:00-21:00"],
                "Wednesday": ["09:00-13:00", "17:00-21:00"],
                "Thursday": ["09:00-13:00", "17:00-21:00"],
                "Friday": ["09:00-12:30", "15:30-20:00"],
                "Saturday": ["10:00-16:00"]
            }

            doctors.append({
                "id": str(uuid.uuid4()),
                "pmdc_number": f"{random.randint(10000, 99999)}-P",
                "full_name": f"Dr. {fname} {lname}",
                "gender": gender,
                "specialty": specialty,
                "qualification": random.choice(qualifications[specialty]),
                "experience_years": random.randint(6, 25),
                "consultation_fee": random.choice([2000, 2500, 3000, 3500]),
                "languages": ["Urdu", "English", "Punjabi"],
                "branch_id": branch["id"],
                "weekly_schedule": weekly_schedule,
                "is_active": True
            })
    return doctors

# ----------------- 3. Patients (500+ Synthetic) -----------------
def generate_patients(count=520):
    patients = []
    cities = ["Lahore", "Islamabad", "Rawalpindi"]
    weights = [0.55, 0.30, 0.15]

    for i in range(1, count + 1):
        gender = random.choice(["Male", "Female"])
        fname = random.choice(FIRST_NAMES_FEMALE) if gender == "Female" else random.choice(FIRST_NAMES_MALE)
        lname = random.choice(LAST_NAMES)
        city = random.choices(cities, weights=weights)[0]
        area = random.choice(CITIES_AREAS[city])
        
        # Age distribution: 15% pediatric, 65% adult, 20% geriatric
        age_group = random.choices(["pediatric", "adult", "geriatric"], weights=[0.15, 0.65, 0.20])[0]
        if age_group == "pediatric":
            age_years = random.randint(1, 14)
        elif age_group == "adult":
            age_years = random.randint(18, 55)
        else:
            age_years = random.randint(56, 82)
            
        dob = (datetime.now() - timedelta(days=age_years*365 + random.randint(0, 300))).date()
        
        # Clinical profiles
        has_allergy = random.random() < 0.25
        allergies = [random.choice([a for a in ALLERGIES_POOL if a != "None"])] if has_allergy else []
        
        has_condition = random.random() < 0.40
        conditions = random.sample([c for c in CONDITIONS_POOL if c != "None"], k=random.randint(1, 2)) if has_condition else []
        
        meds = []
        if "Type 2 Diabetes" in conditions:
            meds.append("Glucophage 500mg")
        if "Hypertension" in conditions:
            meds.append(random.choice(["Concor 2.5mg", "Zestril 5mg"]))
        if "Ischemic Heart Disease" in conditions:
            meds.append("Loprin 75mg")
        if "Asthma" in conditions:
            meds.append("Ventolin Inhaler")

        em_fname = random.choice(FIRST_NAMES_MALE)
        em_lname = lname

        patients.append({
            "id": str(uuid.uuid4()),
            "mrn": f"CCC-PK-{100000 + i}",
            "cnic": generate_cnic(city),
            "full_name": f"{fname} {lname}",
            "gender": gender,
            "date_of_birth": dob.isoformat(),
            "phone": generate_pakistani_phone(),
            "email": f"{fname.lower()}.{lname.lower()}{i}@example.com",
            "city": city,
            "address": f"House #{random.randint(1, 250)}, Street #{random.randint(1, 25)}, {area}, {city}",
            "emergency_contact_name": f"{em_fname} {em_lname}",
            "emergency_contact_phone": generate_pakistani_phone(),
            "known_allergies": allergies,
            "chronic_conditions": conditions,
            "current_medications": meds
        })
    return patients

# ----------------- 4. Appointments, Encounters & Observations -----------------
def generate_clinical_history(patients, doctors, branches):
    appointments = []
    encounters = []
    observations = []
    medication_requests = []
    
    chief_complaints_by_specialty = {
        "General Medicine": [
            ("3 din se tez bukhar aur badan dard", "Acute febrile illness, likely viral fever", "Panadol 500mg"),
            ("Khansi, balgham aur halka saans phoolna", "Upper respiratory tract infection", "Augmentin 625mg"),
            ("Pait mein maror aur patlay dast", "Acute gastroenteritis", "Flagyl 400mg")
        ],
        "Paediatrics": [
            ("Bache ko 2 din se bukhar aur ultiyan", "Pediatric viral gastroenteritis", "Pediatric ORS sachets"),
            ("Seenay mein se seetiyan baj rahi hain aur khansi", "Bronchiolitis / pediatric wheeze", "Ventolin Nebulizer")
        ],
        "Cardiology": [
            ("Seene mein thora bhari-pan chalte hue", "Exertional angina, hypertension", "Loprin 75mg"),
            ("Blood pressure barh raha hai 150/95", "Uncontrolled essential hypertension", "Concor 5mg")
        ],
        "Gynaecology": [
            ("Mahwari mein shadeed dard aur bayqaidgi", "Dysmenorrhea and hormonal irregularity", "Ponstan 500mg"),
            ("Pregnancy routine 2nd trimester check-up", "Routine antenatal care 24 weeks", "Fefol-Vit capsules")
        ],
        "Dermatology": [
            ("Jild par surakh dhabay aur shadeed kharish", "Contact dermatitis / Allergic eczema", "Claritek 10mg"),
            ("Chehre par daanay aur keel", "Acne vulgaris grade 2", "Dalacin T lotion")
        ],
        "ENT": [
            ("Kaan mein shadeed dard aur peep", "Acute otitis media", "Augmentin 625mg"),
            ("Gala band aur nigalne mein dard", "Acute tonsillopharyngitis", "Panadol 500mg")
        ]
    }

    # Generate historical encounters for first 200 patients
    for idx, patient in enumerate(patients[:200]):
        doc = random.choice(doctors)
        complaint_tuple = random.choice(chief_complaints_by_specialty.get(doc["specialty"], chief_complaints_by_specialty["General Medicine"]))
        complaint, assessment, med_name = complaint_tuple

        past_days = random.randint(3, 45)
        enc_time = datetime.now(timezone.utc) - timedelta(days=past_days)
        
        app_id = str(uuid.uuid4())
        enc_id = str(uuid.uuid4())

        # Appointment
        appointments.append({
            "id": app_id,
            "booking_reference": f"BK-{2026}-{1000 + idx}",
            "patient_id": patient["id"],
            "practitioner_id": doc["id"],
            "branch_id": doc["branch_id"],
            "scheduled_start": enc_time.isoformat(),
            "scheduled_end": (enc_time + timedelta(minutes=20)).isoformat(),
            "urgency_tier": "ROUTINE",
            "status": "fulfilled",
            "reason_for_visit": complaint
        })

        # Encounter with SOAP note
        encounters.append({
            "id": enc_id,
            "encounter_reference": f"ENC-{2026}-{1000 + idx}",
            "patient_id": patient["id"],
            "practitioner_id": doc["id"],
            "appointment_id": app_id,
            "status": "completed",
            "encounter_date": enc_time.isoformat(),
            "chief_complaint": complaint,
            "soap_subjective": f"Patient presents with: {complaint}. Duration: 3-4 days. Known allergies: {', '.join(patient['known_allergies']) or 'None'}.",
            "soap_objective": f"BP: 120/80 mmHg, Pulse: 82/min, Temp: 99.4 F, Chest: Clear, Abdomen: Soft non-tender.",
            "soap_assessment": assessment,
            "soap_plan": f"Advised rest, oral hydration, prescribed {med_name}. Follow up in 5 days if unresolved.",
            "doctor_approved": True,
            "doctor_signed_at": enc_time.isoformat()
        })

        # Prescription
        medication_requests.append({
            "id": str(uuid.uuid4()),
            "patient_id": patient["id"],
            "encounter_id": enc_id,
            "practitioner_id": doc["id"],
            "drug_name": med_name,
            "generic_name": med_name.split()[0],
            "dosage_mg": 500.0,
            "frequency_per_day": 2,
            "duration_days": 5,
            "instructions": "Khane ke baad 1 goli subah sham paani ke sath lein.",
            "safety_check_status": "SAFE",
            "safety_check_notes": "Prescription safety verified against allergies and dosage limits."
        })

        # Lab observations for a subset
        if random.random() < 0.5:
            # CBC Observations
            hb_val = round(random.uniform(10.5, 16.5), 1)
            wbc_val = random.randint(4500, 14000)
            plt_val = random.randint(120, 380) * 1000

            observations.append({
                "id": str(uuid.uuid4()),
                "patient_id": patient["id"],
                "encounter_id": enc_id,
                "category": "laboratory",
                "test_code": "CBC-HB",
                "test_name": "Haemoglobin (Hb)",
                "numeric_value": hb_val,
                "unit": "g/dL",
                "reference_range_low": 12.0,
                "reference_range_high": 17.0,
                "flag": "LOW" if hb_val < 12.0 else "NORMAL",
                "issued_at": enc_time.isoformat()
            })
            observations.append({
                "id": str(uuid.uuid4()),
                "patient_id": patient["id"],
                "encounter_id": enc_id,
                "category": "laboratory",
                "test_code": "CBC-WBC",
                "test_name": "Total Leukocyte Count (WBC)",
                "numeric_value": wbc_val,
                "unit": "/mcL",
                "reference_range_low": 4000.0,
                "reference_range_high": 11000.0,
                "flag": "HIGH" if wbc_val > 11000 else "NORMAL",
                "issued_at": enc_time.isoformat()
            })
            observations.append({
                "id": str(uuid.uuid4()),
                "patient_id": patient["id"],
                "encounter_id": enc_id,
                "category": "laboratory",
                "test_code": "CBC-PLT",
                "test_name": "Platelet Count",
                "numeric_value": plt_val,
                "unit": "/mcL",
                "reference_range_low": 150000.0,
                "reference_range_high": 450000.0,
                "flag": "LOW" if plt_val < 150000 else "NORMAL",
                "issued_at": enc_time.isoformat()
            })

    return appointments, encounters, observations, medication_requests

def save_json_files(branches, practitioners, patients, appointments, encounters, observations, medication_requests):
    datasets = {
        "clinic_branches.json": branches,
        "practitioners.json": practitioners,
        "patients.json": patients,
        "appointments.json": appointments,
        "encounters.json": encounters,
        "observations.json": observations,
        "medication_requests.json": medication_requests
    }
    for filename, data in datasets.items():
        filepath = DATA_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  -> Saved {len(data)} records to {filepath.name}")

def seed_sqlite(branches, practitioners, patients, appointments, encounters, observations, medication_requests):
    import sqlite3
    from db_client import SQLITE_DB_PATH, DatabaseClient

    # Ensure schema is created
    db = DatabaseClient()
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()

    # Clear existing
    for tbl in ["medication_requests", "observations", "encounters", "appointments", "patients", "practitioners", "clinic_branches"]:
        cur.execute(f"DELETE FROM {tbl}")

    # Seed Branches
    for b in branches:
        cur.execute("""
        INSERT INTO clinic_branches (id, branch_code, name, city, address, phone, emergency_helpline, opening_time, closing_time, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (b["id"], b["branch_code"], b["name"], b["city"], b["address"], b["phone"], b["emergency_helpline"], b["opening_time"], b["closing_time"], 1))

    # Seed Practitioners
    for p in practitioners:
        cur.execute("""
        INSERT INTO practitioners (id, pmdc_number, full_name, gender, specialty, qualification, experience_years, consultation_fee, languages, branch_id, weekly_schedule, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p["id"], p["pmdc_number"], p["full_name"], p["gender"], p["specialty"], p["qualification"], p["experience_years"], p["consultation_fee"], json.dumps(p["languages"]), p["branch_id"], json.dumps(p["weekly_schedule"]), 1))

    # Seed Patients
    for pt in patients:
        cur.execute("""
        INSERT INTO patients (id, mrn, cnic, full_name, gender, date_of_birth, phone, email, city, address, emergency_contact_name, emergency_contact_phone, known_allergies, chronic_conditions, current_medications)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pt["id"], pt["mrn"], pt["cnic"], pt["full_name"], pt["gender"], pt["date_of_birth"], pt["phone"], pt["email"], pt["city"], pt["address"], pt["emergency_contact_name"], pt["emergency_contact_phone"], json.dumps(pt["known_allergies"]), json.dumps(pt["chronic_conditions"]), json.dumps(pt["current_medications"])))

    # Seed Appointments
    for a in appointments:
        cur.execute("""
        INSERT INTO appointments (id, booking_reference, patient_id, practitioner_id, branch_id, scheduled_start, scheduled_end, urgency_tier, status, reason_for_visit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (a["id"], a["booking_reference"], a["patient_id"], a["practitioner_id"], a["branch_id"], a["scheduled_start"], a["scheduled_end"], a["urgency_tier"], a["status"], a["reason_for_visit"]))

    # Seed Encounters
    for e in encounters:
        cur.execute("""
        INSERT INTO encounters (id, encounter_reference, patient_id, practitioner_id, appointment_id, status, encounter_date, chief_complaint, soap_subjective, soap_objective, soap_assessment, soap_plan, doctor_approved, doctor_signed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (e["id"], e["encounter_reference"], e["patient_id"], e["practitioner_id"], e["appointment_id"], e["status"], e["encounter_date"], e["chief_complaint"], e["soap_subjective"], e["soap_objective"], e["soap_assessment"], e["soap_plan"], 1 if e["doctor_approved"] else 0, e["doctor_signed_at"]))

    # Seed Observations
    for o in observations:
        cur.execute("""
        INSERT INTO observations (id, patient_id, encounter_id, category, test_code, test_name, numeric_value, unit, reference_range_low, reference_range_high, flag, issued_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (o["id"], o["patient_id"], o["encounter_id"], o["category"], o["test_code"], o["test_name"], o["numeric_value"], o["unit"], o["reference_range_low"], o["reference_range_high"], o["flag"], o["issued_at"]))

    # Seed Medication Requests
    for m in medication_requests:
        cur.execute("""
        INSERT INTO medication_requests (id, patient_id, encounter_id, practitioner_id, drug_name, generic_name, dosage_mg, frequency_per_day, duration_days, instructions, safety_check_status, safety_check_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (m["id"], m["patient_id"], m["encounter_id"], m["practitioner_id"], m["drug_name"], m["generic_name"], m["dosage_mg"], m["frequency_per_day"], m["duration_days"], m["instructions"], m["safety_check_status"], m["safety_check_notes"]))

    conn.commit()
    conn.close()
    print("  -> Successfully seeded SQLite local database!")

def seed_supabase_if_configured(branches, practitioners, patients, appointments, encounters, observations, medication_requests):
    from db_client import db
    if not db.is_supabase:
        print("  -> [Supabase Info] Supabase credentials not set in .env. Skipping cloud push (Local SQLite is ready).")
        return
    print("  -> [Supabase] Connected to live Supabase! Seeding cloud PostgreSQL tables...")
    try:
        # Upsert branches
        db.supabase.table("clinic_branches").upsert(branches).execute()
        db.supabase.table("practitioners").upsert(practitioners).execute()
        # Seed patients in chunks of 100
        for i in range(0, len(patients), 100):
            db.supabase.table("patients").upsert(patients[i:i+100]).execute()
        for i in range(0, len(appointments), 100):
            db.supabase.table("appointments").upsert(appointments[i:i+100]).execute()
        for i in range(0, len(encounters), 100):
            db.supabase.table("encounters").upsert(encounters[i:i+100]).execute()
        for i in range(0, len(observations), 100):
            db.supabase.table("observations").upsert(observations[i:i+100]).execute()
        for i in range(0, len(medication_requests), 100):
            db.supabase.table("medication_requests").upsert(medication_requests[i:i+100]).execute()
        print("  -> [Supabase] All tables successfully populated in Supabase!")
    except Exception as e:
        print(f"  -> [Supabase Error] Seeding to Supabase failed: {e}")

def main():
    print("=== City Care Clinics Synthetic Data Seeder ===")
    branches = generate_branches()
    print(f"Generated {len(branches)} clinic branches.")
    
    practitioners = generate_practitioners(branches)
    print(f"Generated {len(practitioners)} practitioners (30 doctors across 6 specialties).")
    
    patients = generate_patients(520)
    print(f"Generated {len(patients)} synthetic Pakistani patient records.")
    
    appointments, encounters, observations, medication_requests = generate_clinical_history(patients, practitioners, branches)
    print(f"Generated {len(appointments)} appointments, {len(encounters)} encounters, {len(observations)} observations, and {len(medication_requests)} medication requests.")

    print("\nSaving JSON cache files...")
    save_json_files(branches, practitioners, patients, appointments, encounters, observations, medication_requests)

    print("\nSeeding local SQLite database...")
    seed_sqlite(branches, practitioners, patients, appointments, encounters, observations, medication_requests)

    print("\nChecking Supabase cloud synchronization...")
    seed_supabase_if_configured(branches, practitioners, patients, appointments, encounters, observations, medication_requests)

    print("\n=== Seeding Completed Successfully! ===")

if __name__ == "__main__":
    main()
