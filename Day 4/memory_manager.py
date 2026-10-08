"""
Memory Manager Module for City Care Clinics
Handles:
1. Short-term conversational memory checkpointing
2. Long-term patient memory across outpatient visits (preferences, past complaints, preferred doctor, language)
3. Privacy-preserving storage (scrubs unnecessary PII, retains clinical continuity facts)
4. Returning patient detection and empathetic personalized UrduLish greetings
"""

import sys
import re
import uuid
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Ensure paths
DAY4_DIR = Path(__file__).resolve().parent
ROOT_DIR = DAY4_DIR.parent
DATA_DIR = DAY4_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_FILE = DATA_DIR / "patient_long_term_memory.json"


class MemoryManager:
    """Manages short-term conversation state and long-term clinical memory."""

    def __init__(self):
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._load_memory()

    def _load_memory(self):
        """Loads long-term memory store; seeds initial profiles from synthetic database if empty."""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    self._memory_cache = json.load(f)
                    return
            except Exception as e:
                print(f"[Memory Warning] Could not parse memory file: {e}. Reinitializing.")

        self._seed_default_memory()

    def _seed_default_memory(self):
        """Seeds realistic initial long-term memory for returning patients."""
        default_memories = {
            "p1": {
                "patient_id": "p1",
                "patient_name": "Ahmed Raza",
                "phone": "+923001234567",
                "mrn": "CCC-PK-100001",
                "preferred_doctor_id": "doc1",
                "preferred_doctor_name": "Dr. Bilal Saeed",
                "preferred_specialty": "General Medicine",
                "preferred_branch": "Gulberg Lahore",
                "preferred_language": "UrduLish",
                "known_allergies": ["Penicillin"],
                "chronic_conditions": ["Hypertension"],
                "past_complaints": ["High blood pressure routine check", "Seenay mein jalan aur tez acid"],
                "last_visit_date": "2026-09-06",
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "p2": {
                "patient_id": "p2",
                "patient_name": "Fatima Bibi",
                "phone": "+923219876543",
                "mrn": "CCC-PK-100002",
                "preferred_doctor_id": "doc2",
                "preferred_doctor_name": "Dr. Ayesha Tariq",
                "preferred_specialty": "Gynaecology",
                "preferred_branch": "DHA Lahore",
                "preferred_language": "UrduLish",
                "known_allergies": ["Sulfa drugs"],
                "chronic_conditions": ["PCOD"],
                "past_complaints": ["Mahwari mein bayqaidgi", "Pelvic scan review"],
                "last_visit_date": "2026-08-18",
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "p3": {
                "patient_id": "p3",
                "patient_name": "Hamza Abbasi",
                "phone": "+923334567890",
                "mrn": "CCC-PK-100003",
                "preferred_doctor_id": "doc3",
                "preferred_doctor_name": "Dr. Usman Sheikh",
                "preferred_specialty": "Paediatrics",
                "preferred_branch": "F-8 Markaz Islamabad",
                "preferred_language": "UrduLish",
                "known_allergies": [],
                "chronic_conditions": ["Bronchial Asthma"],
                "past_complaints": ["Raat ko khansi aur seeti ki awaz", "Vaccination schedule"],
                "last_visit_date": "2026-09-22",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
        self._memory_cache = default_memories
        self._save_memory()

    def _save_memory(self):
        """Persists long-term patient memories to disk."""
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._memory_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Memory Error] Could not save memory: {e}")

    def sanitize_for_privacy(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Privacy-Respecting Filter:
        Retains only clinically relevant information (specialty, doctor, branch,
        allergies, chronic illnesses, and medical complaint summaries).
        Removes payment data, arbitrary non-clinical text, and extraneous PII.
        """
        allowed_keys = {
            "patient_id", "patient_name", "phone", "mrn",
            "preferred_doctor_id", "preferred_doctor_name", "preferred_specialty",
            "preferred_branch", "preferred_language", "known_allergies",
            "chronic_conditions", "past_complaints", "last_visit_date"
        }
        sanitized = {k: v for k, v in raw_data.items() if k in allowed_keys}
        # Keep past complaints concise (last 5 complaints only)
        if "past_complaints" in sanitized and isinstance(sanitized["past_complaints"], list):
            sanitized["past_complaints"] = sanitized["past_complaints"][-5:]
        return sanitized

    def find_patient_memory(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Looks up patient by patient_id, phone, MRN, or patient name.
        """
        if not identifier:
            return None
        clean_id = identifier.strip().lower()
        # Direct key match
        if clean_id in self._memory_cache:
            return self._memory_cache[clean_id]

        digits_id = re.sub(r"\D", "", clean_id)

        # Attribute search
        for mem in self._memory_cache.values():
            if mem.get("patient_id", "").lower() == clean_id:
                return mem
            if mem.get("mrn", "").lower() == clean_id:
                return mem
            if clean_id in mem.get("patient_name", "").lower():
                return mem
            
            # Match phone number (e.g. comparing last 9-10 digits)
            mem_phone = mem.get("phone", "")
            mem_digits = re.sub(r"\D", "", mem_phone)
            if digits_id and mem_digits:
                if len(digits_id) >= 7 and (digits_id in mem_digits or mem_digits.endswith(digits_id[-9:])):
                    return mem
            if clean_id in mem_phone.lower():
                return mem

        return None

    def update_patient_memory(self, patient_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates long-term patient memory with sanitized clinical details.
        """
        existing = self._memory_cache.get(patient_id, {
            "patient_id": patient_id,
            "patient_name": updates.get("patient_name", "Valued Patient"),
            "known_allergies": [],
            "chronic_conditions": [],
            "past_complaints": []
        })

        # Merge updates
        for key, val in updates.items():
            if key == "past_complaints" and isinstance(val, (str, list)):
                current = existing.get("past_complaints", [])
                new_items = [val] if isinstance(val, str) else val
                for item in new_items:
                    if item and item not in current:
                        current.append(item)
                existing["past_complaints"] = current[-5:]
            elif key == "known_allergies" and isinstance(val, list):
                curr_allg = set(existing.get("known_allergies", []))
                curr_allg.update(val)
                existing["known_allergies"] = list(curr_allg)
            else:
                existing[key] = val

        existing["last_updated"] = datetime.now(timezone.utc).isoformat()
        sanitized = self.sanitize_for_privacy(existing)
        self._memory_cache[patient_id] = sanitized
        self._save_memory()
        return sanitized

    def register_patient(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registers a new patient, generates unique MRN, and saves long-term memory.
        """
        existing_count = len(self._memory_cache) + 1
        new_id = f"p{existing_count}_{uuid.uuid4().hex[:4]}"
        mrn = f"CCC-PK-1000{existing_count:02d}"

        # Clean allergies and conditions
        allergies = data.get("known_allergies", [])
        if isinstance(allergies, str):
            allergies = [a.strip() for a in allergies.split(",") if a.strip() and a.strip().lower() != "none"]

        conditions = data.get("chronic_conditions", [])
        if isinstance(conditions, str):
            conditions = [c.strip() for c in conditions.split(",") if c.strip() and c.strip().lower() != "none"]

        patient_record = {
            "patient_id": new_id,
            "patient_name": data.get("patient_name") or data.get("name") or "New Patient",
            "phone": data.get("phone", ""),
            "mrn": mrn,
            "gender": data.get("gender", "Unspecified"),
            "age": int(data.get("age", 30)) if str(data.get("age", "")).isdigit() else 30,
            "preferred_doctor_id": data.get("preferred_doctor_id", "doc1"),
            "preferred_doctor_name": data.get("preferred_doctor_name", "Dr. Bilal Saeed"),
            "preferred_specialty": data.get("preferred_specialty", "General Medicine"),
            "preferred_branch": data.get("preferred_branch", "Gulberg Lahore"),
            "preferred_language": data.get("preferred_language", "English"),
            "known_allergies": allergies,
            "chronic_conditions": conditions,
            "past_complaints": [data.get("initial_complaint")] if data.get("initial_complaint") else ["General Consultation"],
            "last_visit_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        sanitized = self.sanitize_for_privacy(patient_record)
        self._memory_cache[new_id] = sanitized
        self._save_memory()
        return sanitized

    def generate_returning_patient_greeting(self, memory: Dict[str, Any], language: str = "Urdu") -> str:
        """
        Generates personalized, empathetic greeting using long-term memory in English or UrduLish.
        """
        full_name = memory.get("patient_name", "Sahib")
        first_name = full_name.split()[0] if full_name else "Sahib"
        doc_name = memory.get("preferred_doctor_name", "Doctor Sahab")
        branch = memory.get("preferred_branch", "clinic")
        last_date = memory.get("last_visit_date")

        if language and language.lower() in ("english", "en"):
            greeting = (
                f"Hello {first_name}! Welcome to City Care Clinics.\n"
                f"Our records show that on your last visit {f'({last_date}) ' if last_date else ''}"
                f"you consulted **{doc_name}** at our {branch} branch.\n\n"
                f"Would you like to schedule an appointment with **{doc_name}**, or do you have a new medical concern today?"
            )
        else:
            greeting = (
                f"Assalam-o-Alaikum {first_name} sahib! City Care Clinics mein khush-amdeed.\n"
                f"Record ke mutabiq aap pichli dafa {f'({last_date}) ' if last_date else ''}"
                f"**{doc_name}** ko dikhaye thay ({branch} branch mein).\n\n"
                f"Kya aap dobara **{doc_name}** ke saath appointment book karna chahte hain, ya koi nayi takleef ke liye doosray specialist se mashwara chahiye?"
            )
        return greeting


# Singleton instance
memory_manager = MemoryManager()

if __name__ == "__main__":
    print("Testing Memory Manager...")
    mem = memory_manager.find_patient_memory("Ahmed Raza")
    if mem:
        print("Found Patient Memory:", mem["patient_name"])
        print("\nGenerated Personalized Greeting:\n", memory_manager.generate_returning_patient_greeting(mem))
