-- =====================================================================
-- City Care Clinics — PostgreSQL / Supabase FHIR-Aligned Database Schema
-- Version: 1.0 (Production-Ready)
-- =====================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------
-- 1. Clinic Branches (FHIR Location / Organization)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clinic_branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    branch_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL CHECK (city IN ('Lahore', 'Islamabad', 'Rawalpindi')),
    address TEXT NOT NULL,
    phone VARCHAR(30) NOT NULL,
    emergency_helpline VARCHAR(30) NOT NULL DEFAULT '1122',
    opening_time TIME NOT NULL DEFAULT '08:00:00',
    closing_time TIME NOT NULL DEFAULT '22:00:00',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 2. Practitioners / Doctors (FHIR Practitioner)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS practitioners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pmdc_number VARCHAR(30) UNIQUE NOT NULL, -- Pakistan Medical & Dental Council Registration
    full_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    specialty VARCHAR(50) NOT NULL CHECK (
        specialty IN ('General Medicine', 'Paediatrics', 'Gynaecology', 'Cardiology', 'Dermatology', 'ENT')
    ),
    qualification VARCHAR(100) NOT NULL, -- e.g. MBBS, FCPS, MRCP
    experience_years INT NOT NULL DEFAULT 5,
    consultation_fee INT NOT NULL DEFAULT 2000, -- PKR
    languages TEXT[] DEFAULT ARRAY['Urdu', 'English'],
    branch_id UUID REFERENCES clinic_branches(id) ON DELETE SET NULL,
    weekly_schedule JSONB NOT NULL, -- {"Monday": ["09:00-13:00", "17:00-21:00"], ...}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 3. Patients (FHIR Patient)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mrn VARCHAR(30) UNIQUE NOT NULL, -- Medical Record Number: e.g. CCC-PK-001092
    cnic VARCHAR(20) UNIQUE NOT NULL, -- Pakistani CNIC: XXXXX-XXXXXXX-X
    full_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    date_of_birth DATE NOT NULL,
    phone VARCHAR(25) NOT NULL, -- Format: +92-3XX-XXXXXXX
    email VARCHAR(100),
    city VARCHAR(50) NOT NULL,
    address TEXT,
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(25),
    known_allergies TEXT[] DEFAULT ARRAY[]::TEXT[], -- e.g. ['Penicillin', 'Sulfa']
    chronic_conditions TEXT[] DEFAULT ARRAY[]::TEXT[], -- e.g. ['Hypertension', 'Type 2 Diabetes']
    current_medications TEXT[] DEFAULT ARRAY[]::TEXT[], -- e.g. ['Glucophage 500mg', 'Loprin 75mg']
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 4. Appointments (FHIR Appointment)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_reference VARCHAR(30) UNIQUE NOT NULL, -- e.g. BK-2026-9041
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    practitioner_id UUID NOT NULL REFERENCES practitioners(id) ON DELETE RESTRICT,
    branch_id UUID NOT NULL REFERENCES clinic_branches(id) ON DELETE RESTRICT,
    scheduled_start TIMESTAMPTZ NOT NULL,
    scheduled_end TIMESTAMPTZ NOT NULL,
    urgency_tier VARCHAR(20) NOT NULL DEFAULT 'ROUTINE' CHECK (
        urgency_tier IN ('EMERGENCY', 'URGENT', 'ROUTINE')
    ),
    status VARCHAR(20) NOT NULL DEFAULT 'booked' CHECK (
        status IN ('booked', 'arrived', 'in-progress', 'fulfilled', 'cancelled', 'noshow')
    ),
    reason_for_visit TEXT NOT NULL,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 5. Encounters (FHIR Encounter - Consultations & Visits)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS encounters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encounter_reference VARCHAR(30) UNIQUE NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    practitioner_id UUID NOT NULL REFERENCES practitioners(id) ON DELETE RESTRICT,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (
        status IN ('planned', 'arrived', 'in-progress', 'completed', 'cancelled')
    ),
    encounter_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    chief_complaint TEXT NOT NULL,
    soap_subjective TEXT,
    soap_objective TEXT,
    soap_assessment TEXT,
    soap_plan TEXT,
    doctor_approved BOOLEAN DEFAULT FALSE,
    doctor_signed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 6. Observations / Lab Results (FHIR Observation)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('laboratory', 'vital-signs', 'imaging', 'procedure')),
    test_code VARCHAR(50) NOT NULL, -- e.g. CBC-HB, LFT-ALT, LIPID-CHOL, HBA1C
    test_name VARCHAR(100) NOT NULL,
    numeric_value NUMERIC(10, 2),
    string_value TEXT,
    unit VARCHAR(30), -- e.g. g/dL, U/L, mg/dL, %
    reference_range_low NUMERIC(10, 2),
    reference_range_high NUMERIC(10, 2),
    flag VARCHAR(20) DEFAULT 'NORMAL' CHECK (flag IN ('NORMAL', 'HIGH', 'LOW', 'CRITICAL_HIGH', 'CRITICAL_LOW')),
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    lab_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 7. Medication Requests / Prescriptions (FHIR MedicationRequest)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medication_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES encounters(id) ON DELETE SET NULL,
    practitioner_id UUID NOT NULL REFERENCES practitioners(id) ON DELETE RESTRICT,
    drug_name VARCHAR(100) NOT NULL, -- Brand: Panadol
    generic_name VARCHAR(100) NOT NULL, -- Paracetamol
    dosage_mg NUMERIC(8, 2) NOT NULL,
    frequency_per_day INT NOT NULL,
    duration_days INT NOT NULL,
    instructions TEXT,
    safety_check_status VARCHAR(20) DEFAULT 'SAFE' CHECK (
        safety_check_status IN ('SAFE', 'WARNING', 'CRITICAL_CLASH', 'OVERRIDDEN_BY_DOCTOR')
    ),
    safety_check_notes TEXT,
    prescribed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- 8. Audit Logs (Compliance & HIPAA/PECA Security)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_id TEXT NOT NULL,
    actor_role VARCHAR(30) NOT NULL CHECK (actor_role IN ('PATIENT', 'RECEPTIONIST', 'DOCTOR', 'SYSTEM_AGENT', 'ADMIN')),
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL,
    resource_accessed VARCHAR(100) NOT NULL,
    tool_name VARCHAR(50),
    ip_address INET,
    change_payload JSONB,
    emergency_flag BOOLEAN DEFAULT FALSE
);

-- ---------------------------------------------------------------------
-- Performance Indexes
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_patients_cnic ON patients(cnic);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patients_mrn ON patients(mrn);
CREATE INDEX IF NOT EXISTS idx_practitioners_specialty ON practitioners(specialty);
CREATE INDEX IF NOT EXISTS idx_practitioners_branch ON practitioners(branch_id);
CREATE INDEX IF NOT EXISTS idx_appointments_start ON appointments(scheduled_start);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id);
CREATE INDEX IF NOT EXISTS idx_observations_patient ON observations(patient_id);
CREATE INDEX IF NOT EXISTS idx_observations_test_code ON observations(test_code);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);

-- ---------------------------------------------------------------------
-- Supabase Row Level Security (RLS) Setup
-- ---------------------------------------------------------------------
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE encounters ENABLE ROW LEVEL SECURITY;
ALTER TABLE observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Allow public read access to clinic branches and doctors for booking
ALTER TABLE clinic_branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE practitioners ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read clinic branches" ON clinic_branches FOR SELECT USING (true);
CREATE POLICY "Public read practitioners" ON practitioners FOR SELECT USING (true);
CREATE POLICY "Service role full access on all tables" ON patients FOR ALL USING (true);
