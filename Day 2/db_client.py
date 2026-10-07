"""
Database Client Module for City Care Clinics
Seamlessly connects to Supabase PostgreSQL when credentials exist in .env,
and falls back to SQLite (clinic_local.db) for reliable offline/local testing.
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timezone
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DB_PATH = DATA_DIR / "clinic_local.db"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", "")).strip()

_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    if SUPABASE_URL and SUPABASE_KEY and not SUPABASE_URL.startswith("https://your-project"):
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            return _supabase_client
        except Exception as e:
            print(f"[DB Warning] Could not initialize Supabase client: {e}. Falling back to SQLite.")
            return None
    return None

class DatabaseClient:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.is_supabase = self.supabase is not None
        self._init_sqlite()

    def _init_sqlite(self):
        """Initializes SQLite schema matching the FHIR tables."""
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinic_branches (
            id TEXT PRIMARY KEY,
            branch_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            emergency_helpline TEXT DEFAULT '1122',
            opening_time TEXT DEFAULT '08:00:00',
            closing_time TEXT DEFAULT '22:00:00',
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS practitioners (
            id TEXT PRIMARY KEY,
            pmdc_number TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            gender TEXT,
            specialty TEXT NOT NULL,
            qualification TEXT NOT NULL,
            experience_years INTEGER DEFAULT 5,
            consultation_fee INTEGER DEFAULT 2000,
            languages TEXT,
            branch_id TEXT,
            weekly_schedule TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            mrn TEXT UNIQUE NOT NULL,
            cnic TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            gender TEXT,
            date_of_birth TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            city TEXT NOT NULL,
            address TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            known_allergies TEXT,
            chronic_conditions TEXT,
            current_medications TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            booking_reference TEXT UNIQUE NOT NULL,
            patient_id TEXT NOT NULL,
            practitioner_id TEXT NOT NULL,
            branch_id TEXT NOT NULL,
            scheduled_start TEXT NOT NULL,
            scheduled_end TEXT NOT NULL,
            urgency_tier TEXT DEFAULT 'ROUTINE',
            status TEXT DEFAULT 'booked',
            reason_for_visit TEXT NOT NULL,
            cancellation_reason TEXT,
            created_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS encounters (
            id TEXT PRIMARY KEY,
            encounter_reference TEXT UNIQUE NOT NULL,
            patient_id TEXT NOT NULL,
            practitioner_id TEXT NOT NULL,
            appointment_id TEXT,
            status TEXT DEFAULT 'completed',
            encounter_date TEXT NOT NULL,
            chief_complaint TEXT NOT NULL,
            soap_subjective TEXT,
            soap_objective TEXT,
            soap_assessment TEXT,
            soap_plan TEXT,
            doctor_approved INTEGER DEFAULT 0,
            doctor_signed_at TEXT,
            created_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            encounter_id TEXT,
            category TEXT NOT NULL,
            test_code TEXT NOT NULL,
            test_name TEXT NOT NULL,
            numeric_value REAL,
            string_value TEXT,
            unit TEXT,
            reference_range_low REAL,
            reference_range_high REAL,
            flag TEXT DEFAULT 'NORMAL',
            issued_at TEXT NOT NULL,
            lab_notes TEXT,
            created_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medication_requests (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            encounter_id TEXT,
            practitioner_id TEXT NOT NULL,
            drug_name TEXT NOT NULL,
            generic_name TEXT NOT NULL,
            dosage_mg REAL NOT NULL,
            frequency_per_day INTEGER NOT NULL,
            duration_days INTEGER NOT NULL,
            instructions TEXT,
            safety_check_status TEXT DEFAULT 'SAFE',
            safety_check_notes TEXT,
            prescribed_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            patient_id TEXT,
            action_type TEXT NOT NULL,
            resource_accessed TEXT NOT NULL,
            tool_name TEXT,
            ip_address TEXT,
            change_payload TEXT,
            emergency_flag INTEGER DEFAULT 0
        )
        """)

        conn.commit()
        conn.close()

    def get_connection(self):
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------ Branch & Practitioner Operations ------------------
    def get_branches(self) -> List[Dict[str, Any]]:
        if self.is_supabase:
            res = self.supabase.table("clinic_branches").select("*").eq("is_active", True).execute()
            return res.data
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clinic_branches WHERE is_active = 1")
            return [dict(r) for r in cur.fetchall()]

    def get_practitioners(self, specialty: Optional[str] = None, branch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.is_supabase:
            q = self.supabase.table("practitioners").select("*, clinic_branches(name, city)").eq("is_active", True)
            if specialty:
                q = q.eq("specialty", specialty)
            if branch_id:
                q = q.eq("branch_id", branch_id)
            res = q.execute()
            return res.data
        
        query = "SELECT * FROM practitioners WHERE is_active = 1"
        params = []
        if specialty:
            query += " AND specialty = ?"
            params.append(specialty)
        if branch_id:
            query += " AND branch_id = ?"
            params.append(branch_id)
            
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = [dict(r) for r in cur.fetchall()]
            for r in rows:
                if isinstance(r.get("languages"), str):
                    try:
                        r["languages"] = json.loads(r["languages"])
                    except:
                        r["languages"] = r["languages"].split(",")
                if isinstance(r.get("weekly_schedule"), str):
                    try:
                        r["weekly_schedule"] = json.loads(r["weekly_schedule"])
                    except:
                        pass
            return rows

    def get_practitioner_by_id(self, practitioner_id: str) -> Optional[Dict[str, Any]]:
        if self.is_supabase:
            res = self.supabase.table("practitioners").select("*").eq("id", practitioner_id).execute()
            return res.data[0] if res.data else None
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM practitioners WHERE id = ?", (practitioner_id,))
            row = cur.fetchone()
            if row:
                d = dict(row)
                if isinstance(d.get("weekly_schedule"), str):
                    d["weekly_schedule"] = json.loads(d["weekly_schedule"])
                return d
            return None

    # ------------------ Patient Operations ------------------
    def find_patient_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        # Normalize phone
        clean_phone = phone.replace(" ", "").replace("-", "")
        if self.is_supabase:
            res = self.supabase.table("patients").select("*").ilike("phone", f"%{clean_phone[-9:]}%").execute()
            return res.data[0] if res.data else None
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE replace(replace(phone, ' ', ''), '-', '') LIKE ?", (f"%{clean_phone[-9:]}%",))
            row = cur.fetchone()
            if row:
                return self._parse_patient_json_fields(dict(row))
            return None

    def find_patient_by_mrn(self, mrn: str) -> Optional[Dict[str, Any]]:
        if self.is_supabase:
            res = self.supabase.table("patients").select("*").eq("mrn", mrn.strip().upper()).execute()
            return res.data[0] if res.data else None
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE mrn = ?", (mrn.strip().upper(),))
            row = cur.fetchone()
            return self._parse_patient_json_fields(dict(row)) if row else None

    def find_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        if self.is_supabase:
            res = self.supabase.table("patients").select("*").eq("id", patient_id).execute()
            return res.data[0] if res.data else None
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            row = cur.fetchone()
            return self._parse_patient_json_fields(dict(row)) if row else None

    def _parse_patient_json_fields(self, p: Dict[str, Any]) -> Dict[str, Any]:
        for field in ["known_allergies", "chronic_conditions", "current_medications"]:
            if isinstance(p.get(field), str):
                try:
                    p[field] = json.loads(p[field])
                except:
                    p[field] = [x.strip() for x in p[field].split(",") if x.strip()]
        return p

    # ------------------ Appointments ------------------
    def create_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_supabase:
            res = self.supabase.table("appointments").insert(appointment_data).execute()
            return res.data[0]
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO appointments (
                id, booking_reference, patient_id, practitioner_id, branch_id,
                scheduled_start, scheduled_end, urgency_tier, status, reason_for_visit, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                appointment_data["id"],
                appointment_data["booking_reference"],
                appointment_data["patient_id"],
                appointment_data["practitioner_id"],
                appointment_data["branch_id"],
                appointment_data["scheduled_start"],
                appointment_data["scheduled_end"],
                appointment_data.get("urgency_tier", "ROUTINE"),
                appointment_data.get("status", "booked"),
                appointment_data.get("reason_for_visit", "Consultation"),
                appointment_data.get("created_at", datetime.now(timezone.utc).isoformat())
            ))
            conn.commit()
            return appointment_data

    def get_patient_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        if self.is_supabase:
            res = self.supabase.table("appointments").select("*, practitioners(full_name, specialty), clinic_branches(name, city)").eq("patient_id", patient_id).order("scheduled_start", desc=True).execute()
            return res.data
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT a.*, p.full_name as doctor_name, p.specialty as doctor_specialty, b.name as branch_name, b.city as branch_city
            FROM appointments a
            LEFT JOIN practitioners p ON a.practitioner_id = p.id
            LEFT JOIN clinic_branches b ON a.branch_id = b.id
            WHERE a.patient_id = ?
            ORDER BY a.scheduled_start DESC
            """, (patient_id,))
            return [dict(r) for r in cur.fetchall()]

    def update_appointment_status(self, appointment_id: str, status: str, cancellation_reason: Optional[str] = None) -> bool:
        if self.is_supabase:
            update_data = {"status": status}
            if cancellation_reason:
                update_data["cancellation_reason"] = cancellation_reason
            res = self.supabase.table("appointments").update(update_data).eq("id", appointment_id).execute()
            return len(res.data) > 0
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            UPDATE appointments SET status = ?, cancellation_reason = ? WHERE id = ?
            """, (status, cancellation_reason, appointment_id))
            conn.commit()
            return cur.rowcount > 0

    # ------------------ Observations & Encounters ------------------
    def get_patient_observations(self, patient_id: str, test_code: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.is_supabase:
            q = self.supabase.table("observations").select("*").eq("patient_id", patient_id).order("issued_at", desc=True)
            if test_code:
                q = q.eq("test_code", test_code)
            res = q.execute()
            return res.data
        with self.get_connection() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM observations WHERE patient_id = ?"
            params = [patient_id]
            if test_code:
                query += " AND test_code = ?"
                params.append(test_code)
            query += " ORDER BY issued_at DESC"
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]

    def get_patient_encounters(self, patient_id: str) -> List[Dict[str, Any]]:
        if self.is_supabase:
            res = self.supabase.table("encounters").select("*, practitioners(full_name, specialty)").eq("patient_id", patient_id).order("encounter_date", desc=True).execute()
            return res.data
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT e.*, p.full_name as doctor_name, p.specialty as doctor_specialty
            FROM encounters e
            LEFT JOIN practitioners p ON e.practitioner_id = p.id
            WHERE e.patient_id = ?
            ORDER BY e.encounter_date DESC
            """, (patient_id,))
            return [dict(r) for r in cur.fetchall()]

    def get_patient_medications(self, patient_id: str) -> List[Dict[str, Any]]:
        if self.is_supabase:
            res = self.supabase.table("medication_requests").select("*").eq("patient_id", patient_id).order("prescribed_at", desc=True).execute()
            return res.data
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM medication_requests WHERE patient_id = ? ORDER BY prescribed_at DESC", (patient_id,))
            return [dict(r) for r in cur.fetchall()]

    # ------------------ Audit Logging ------------------
    def log_audit(self, actor_id: str, actor_role: str, action_type: str, resource_accessed: str,
                  patient_id: Optional[str] = None, tool_name: Optional[str] = None,
                  change_payload: Optional[Dict] = None, emergency_flag: bool = False):
        import uuid
        payload = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "patient_id": patient_id,
            "action_type": action_type,
            "resource_accessed": resource_accessed,
            "tool_name": tool_name,
            "change_payload": json.dumps(change_payload) if change_payload else None,
            "emergency_flag": 1 if emergency_flag else 0
        }
        if self.is_supabase:
            try:
                self.supabase.table("audit_logs").insert(payload).execute()
                return
            except Exception as e:
                print(f"[Audit Error Supabase] {e}")

        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                INSERT INTO audit_logs (id, timestamp, actor_id, actor_role, patient_id, action_type, resource_accessed, tool_name, change_payload, emergency_flag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    payload["id"], payload["timestamp"], payload["actor_id"], payload["actor_role"],
                    payload["patient_id"], payload["action_type"], payload["resource_accessed"],
                    payload["tool_name"], payload["change_payload"], payload["emergency_flag"]
                ))
                conn.commit()
        except Exception as e:
            print(f"[Audit Error Local] {e}")


# Singleton instance
db = DatabaseClient()
