"""
Scheduling Agent for City Care Clinics
Handles:
1. Symptom to Specialty Mapping
2. Doctor preference filtering (gender, branch, language, max fee)
3. Strict Slot Verification: Anti-Double-Booking & Anti-Past-Booking
4. Full Appointment Lifecycle (Book, Reschedule, Cancel)
5. Google Calendar / iCal event generation
6. UrduLish conversational confirmations
"""

import sys
import uuid
import urllib.parse
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "Day 2"))

# Safe import from Day 2
from db_client import db

SPECIALTY_KEYWORDS = {
    "Paediatrics": ["bacha", "child", "infant", "toddler", "beta", "beti", "pediatric", "teething", "growth milestone"],
    "Cardiology": ["dil", "heart", "chest pain", "seena", "dhadkan", "palpitations", "angina", "high bp", "hypertension check"],
    "Gynaecology": ["pregnancy", "hamal", "period", "mahwari", "pelvic", "pcod", "khawateen", "ultrasound pregnancy", "infertility"],
    "Dermatology": ["jild", "skin", "kharish", "rash", "acne", "daanay", "keel", "baal", "hair fall", "dandruff", "eczema", "fungal"],
    "ENT": ["kaan", "ear", "gala", "throat", "naak", "nose", "sinus", "tonsil", "awaz baithna", "chakkar", "vertigo", "tinnitus"],
    "General Medicine": ["bukhar", "fever", "khansi", "cough", "badan dard", "kamzori", "fatigue", "pait dard", "stomach", "sugar"]
}

class SchedulingAgent:
    def __init__(self):
        pass

    def map_symptoms_to_specialty(self, symptoms_text: str, patient_relation: Optional[str] = None, age: Optional[int] = None) -> str:
        """
        Maps clinical symptoms to the appropriate specialty.
        Prioritizes Paediatrics for children under 14.
        """
        text_lower = symptoms_text.lower()

        # Priority 1: Pediatric rule (age < 14 or relation == child)
        if (age is not None and age < 14) or (patient_relation and patient_relation.lower() == "child"):
            return "Paediatrics"

        # Priority 2: Keyword match
        for specialty, keywords in SPECIALTY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return specialty

        return "General Medicine"

    def find_doctors(self, specialty: str, gender_preference: Optional[str] = None,
                     branch_city: Optional[str] = None, branch_name: Optional[str] = None,
                     max_fee: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Searches available doctors matching clinical specialty and patient preferences.
        """
        all_docs = db.get_practitioners(specialty=specialty)
        branches = {b["id"]: b for b in db.get_branches()}

        filtered = []
        for doc in all_docs:
            b_info = branches.get(doc["branch_id"], {})
            doc_branch_name = b_info.get("name", "")
            doc_city = b_info.get("city", "")

            # Filter gender
            if gender_preference and doc.get("gender", "").lower() != gender_preference.lower():
                continue

            # Filter city/branch
            if branch_city and branch_city.lower() not in doc_city.lower():
                continue
            if branch_name and branch_name.lower() not in doc_branch_name.lower():
                continue

            # Filter fee
            if max_fee and doc.get("consultation_fee", 0) > max_fee:
                continue

            doc_copy = dict(doc)
            doc_copy["branch_name"] = doc_branch_name
            doc_copy["branch_city"] = doc_city
            filtered.append(doc_copy)

        return filtered

    def get_available_slots(self, doctor_id: str, target_date_str: str) -> List[Dict[str, Any]]:
        """
        Returns non-conflicting available slots for a doctor on a given date.
        Strictly enforces:
        1. NEVER BOOK IN THE PAST
        2. NEVER DOUBLE-BOOK (checks existing appointments in DB)
        """
        doc = db.get_practitioner_by_id(doctor_id)
        if not doc:
            return []

        now_utc = datetime.now(timezone.utc)
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

        # Check existing booked appointments for this doctor on target date
        existing_appointments = []
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT scheduled_start, scheduled_end, status FROM appointments
            WHERE practitioner_id = ? AND status != 'cancelled'
            """, (doctor_id,))
            existing_appointments = [dict(r) for r in cur.fetchall()]

        booked_ranges = []
        for a in existing_appointments:
            try:
                s_dt = datetime.fromisoformat(a["scheduled_start"].replace("Z", "+00:00"))
                e_dt = datetime.fromisoformat(a["scheduled_end"].replace("Z", "+00:00"))
                booked_ranges.append((s_dt, e_dt))
            except:
                pass

        # Standard schedule slots: 10:00 to 13:00 and 17:00 to 20:30 (20 min intervals)
        slots = []
        time_windows = [("10:00", "13:00"), ("17:00", "20:30")]

        for start_t, end_t in time_windows:
            start_hour, start_min = map(int, start_t.split(":"))
            end_hour, end_min = map(int, end_t.split(":"))

            slot_start = datetime(target_date.year, target_date.month, target_date.day,
                                  start_hour, start_min, tzinfo=timezone.utc)
            slot_limit = datetime(target_date.year, target_date.month, target_date.day,
                                  end_hour, end_min, tzinfo=timezone.utc)

            while slot_start < slot_limit:
                slot_end = slot_start + timedelta(minutes=20)

                # Rule 1: Never in the past
                if slot_start <= now_utc:
                    slot_start = slot_end
                    continue

                # Rule 2: Never double-book
                is_double_booked = any(
                    (slot_start < b_end and slot_end > b_start)
                    for b_start, b_end in booked_ranges
                )

                if not is_double_booked:
                    slots.append({
                        "slot_start": slot_start.isoformat(),
                        "slot_end": slot_end.isoformat(),
                        "display_time": slot_start.strftime("%I:%M %p"),
                        "display_date": slot_start.strftime("%A, %d %B %Y")
                    })

                slot_start = slot_end

        return slots

    def book_appointment(self, patient_id: str, doctor_id: str, branch_id: str,
                         slot_iso: str, reason: str, urgency: str = "ROUTINE") -> Dict[str, Any]:
        """
        Commits an appointment booking with safety validations.
        """
        # Validate past check
        slot_dt = datetime.fromisoformat(slot_iso.replace("Z", "+00:00"))
        now_utc = datetime.now(timezone.utc)
        if slot_dt <= now_utc:
            return {
                "success": False,
                "error": "Cannot book an appointment in the past. Please select an upcoming future time slot."
            }

        # Validate anti-double-booking
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT id FROM appointments
            WHERE practitioner_id = ? AND scheduled_start = ? AND status != 'cancelled'
            """, (doctor_id, slot_dt.isoformat()))
            if cur.fetchone():
                return {
                    "success": False,
                    "error": "This slot was just reserved by another patient (Double-booking prevented). Please choose another time."
                }

        booking_ref = f"BK-2026-{uuid.uuid4().hex[:6].upper()}"
        end_dt = slot_dt + timedelta(minutes=20)
        app_id = str(uuid.uuid4())

        record = {
            "id": app_id,
            "booking_reference": booking_ref,
            "patient_id": patient_id,
            "practitioner_id": doctor_id,
            "branch_id": branch_id,
            "scheduled_start": slot_dt.isoformat(),
            "scheduled_end": end_dt.isoformat(),
            "urgency_tier": urgency,
            "status": "booked",
            "reason_for_visit": reason
        }

        db.create_appointment(record)

        # Generate Google Calendar Link
        gcal_url = self.generate_google_calendar_link(
            title=f"Doctor Consultation — City Care Clinics",
            start_dt=slot_dt,
            end_dt=end_dt,
            details=f"Appointment Ref: {booking_ref}. Reason: {reason}",
            location="City Care Clinics"
        )

        # Generate confirmation message in UrduLish
        doc = db.get_practitioner_by_id(doctor_id)
        doc_name = doc["full_name"] if doc else "Doctor"
        doc_spec = doc["specialty"] if doc else "Specialist"
        doc_fee = doc["consultation_fee"] if doc else 2000

        urdulish_msg = (
            f"✅ Mubarak ho! Aap ki appointment confirm ho chuki hai:\n"
            f"• Doctor: {doc_name} ({doc_spec})\n"
            f"• Waqt: {slot_dt.strftime('%A, %d %B %Y - %I:%M %p')}\n"
            f"• Consultation Fee: PKR {doc_fee:,}\n"
            f"• Booking Reference: #{booking_ref}\n\n"
            f"Baraye meharbani waqt se 10 minute pehle tashreef layein. Allah aap ko kamil sehat ata farmaye!"
        )

        return {
            "success": True,
            "appointment_id": app_id,
            "booking_reference": booking_ref,
            "doctor_name": doc_name,
            "specialty": doc_spec,
            "fee": doc_fee,
            "start_time": slot_dt.isoformat(),
            "google_calendar_url": gcal_url,
            "confirmation_urdulish": urdulish_msg
        }

    def generate_google_calendar_link(self, title: str, start_dt: datetime, end_dt: datetime, details: str, location: str) -> str:
        """Generates standard direct Google Calendar event creation URL."""
        fmt = "%Y%m%dT%H%M%SZ"
        s_str = start_dt.strftime(fmt)
        e_str = end_dt.strftime(fmt)
        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": f"{s_str}/{e_str}",
            "details": details,
            "location": location
        }
        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

    def cancel_appointment(self, appointment_id: str, reason: str = "Patient request") -> Dict[str, Any]:
        """Cancels an existing appointment."""
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            UPDATE appointments
            SET status = 'cancelled'
            WHERE id = ?
            """, (appointment_id,))
            conn.commit()
            if cur.rowcount == 0:
                return {"success": False, "error": f"Appointment {appointment_id} not found."}
        
        return {
            "success": True,
            "appointment_id": appointment_id,
            "status": "cancelled",
            "message_urdulish": f"Aap ki appointment (ID: {appointment_id[:8]}) mansookh (cancel) kar di gayi hai. Agar dobara appointment chahiye ho toh batayein."
        }

    def reschedule_appointment(self, appointment_id: str, new_slot_iso: str) -> Dict[str, Any]:
        """Reschedules an existing appointment to a new slot with temporal and anti-collision checks."""
        slot_dt = datetime.fromisoformat(new_slot_iso.replace("Z", "+00:00"))
        now_utc = datetime.now(timezone.utc)
        if slot_dt <= now_utc:
            return {"success": False, "error": "Cannot reschedule into the past."}
            
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT practitioner_id FROM appointments WHERE id = ?", (appointment_id,))
            row = cur.fetchone()
            if not row:
                return {"success": False, "error": f"Appointment {appointment_id} not found."}
            doc_id = row[0]
            
            # Check collision
            cur.execute("""
            SELECT id FROM appointments
            WHERE practitioner_id = ? AND scheduled_start = ? AND status != 'cancelled' AND id != ?
            """, (doc_id, slot_dt.isoformat(), appointment_id))
            if cur.fetchone():
                return {"success": False, "error": "New slot is already occupied."}
                
            end_dt = slot_dt + timedelta(minutes=20)
            cur.execute("""
            UPDATE appointments
            SET scheduled_start = ?, scheduled_end = ?, status = 'rescheduled'
            WHERE id = ?
            """, (slot_dt.isoformat(), end_dt.isoformat(), appointment_id))
            conn.commit()

        return {
            "success": True,
            "appointment_id": appointment_id,
            "new_start_time": slot_dt.isoformat(),
            "status": "rescheduled",
            "message_urdulish": f"Aap ki appointment nayi tareeq {slot_dt.strftime('%A, %d %B %Y - %I:%M %p')} par tabdeel (reschedule) kar di gayi hai."
        }


# Singleton instance
scheduling_agent = SchedulingAgent()

if __name__ == "__main__":
    print("Testing Scheduling Agent...")
    spec = scheduling_agent.map_symptoms_to_specialty("Bache ko bukhar aur ulti hai", patient_relation="child")
    print("Mapped Specialty:", spec)

    docs = scheduling_agent.find_doctors(specialty=spec, branch_city="Lahore")
    print(f"Found {len(docs)} matching doctors in Lahore.")
    if docs:
        first_doc = docs[0]
        print(f"Doctor: {first_doc['full_name']}, Branch: {first_doc['branch_name']}")
        
        # Test future slot check
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        slots = scheduling_agent.get_available_slots(first_doc["id"], tomorrow)
        print(f"Available slots for tomorrow ({tomorrow}): {len(slots)}")
        if slots:
            print("First slot:", slots[0]["display_time"])
