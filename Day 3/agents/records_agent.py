"""
Records Agent for City Care Clinics
Answers clinical questions from the patient's electronic health record (EHR)
and laboratory observations file.
Enforces strict medical privacy, accurate factual retrieval,
and patient-friendly UrduLish communication.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "Day 2"))

from db_client import db  # type: ignore
from llm_factory import get_llm  # type: ignore

class RecordsAgent:
    def __init__(self):
        self.llm = get_llm()

    def get_patient_summary(self, patient_identifier: str) -> Optional[Dict[str, Any]]:
        """Finds patient by MRN or phone and aggregates medical chart."""
        p = db.find_patient_by_mrn(patient_identifier) or db.find_patient_by_phone(patient_identifier)
        if not p:
            return None

        patient_id = p["id"]
        encounters = db.get_patient_encounters(patient_id)
        labs = db.get_patient_observations(patient_id)
        meds = db.get_patient_medications(patient_id)

        return {
            "patient": p,
            "encounters": encounters,
            "observations": labs,
            "medications": meds
        }

    def answer_patient_query(self, patient_identifier: str, query: str) -> Dict[str, Any]:
        """
        Answers a specific inquiry from the patient's file (e.g. past labs, past medications, allergies).
        """
        data = self.get_patient_summary(patient_identifier)
        if not data:
            return {
                "success": False,
                "answer": f"Maaf kijiye, '{patient_identifier}' ke mutabiq koi mariz record dastyab nahi hai. Baraye meharbani apna durust Phone ya MRN number batayein."
            }

        p = data["patient"]
        recent_encounters = data["encounters"][:3]
        recent_labs = data["observations"][:6]
        recent_meds = data["medications"][:5]

        context = {
            "name": p["full_name"],
            "age_dob": p["date_of_birth"],
            "known_allergies": p.get("known_allergies", []),
            "chronic_conditions": p.get("chronic_conditions", []),
            "past_encounters": [
                {
                    "date": e["encounter_date"][:10],
                    "doctor": e.get("doctor_name", "Doctor"),
                    "complaint": e["chief_complaint"],
                    "assessment": e.get("soap_assessment", "")
                }
                for e in recent_encounters
            ],
            "past_lab_results": [
                {
                    "test": o["test_name"],
                    "value": f"{o['numeric_value']} {o['unit']}",
                    "flag": o["flag"],
                    "date": o["issued_at"][:10]
                }
                for o in recent_labs
            ],
            "past_medications": [
                {
                    "drug": m["drug_name"],
                    "dosage": f"{m['dosage_mg']} mg",
                    "instructions": m.get("instructions", "")
                }
                for m in recent_meds
            ]
        }

        prompt = f"""You are the Records Agent at City Care Clinics.
A patient has asked a question regarding their past medical file and lab reports.

Patient File Context:
{json.dumps(context, indent=2)}

Patient's Question:
"{query}"

Answer the patient's question clearly, accurately, and politely in UrduLish (Roman Urdu + English).
RULES:
1. Only state facts directly present in the patient record context.
2. If the user asks about an abnormal lab value, explain what the value is without diagnosing them with a new disease, and advise them to consult their doctor.
3. Be respectful and warm."""

        try:
            response = self.llm.invoke(prompt)
            # Handle text extraction
            ans_text = response.content
            if isinstance(ans_text, list):
                ans_text = " ".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in ans_text])

            return {
                "success": True,
                "patient_name": p["full_name"],
                "answer": ans_text.strip(),
                "records_consulted": {
                    "encounters_count": len(recent_encounters),
                    "labs_count": len(recent_labs),
                    "meds_count": len(recent_meds)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "answer": "Record daryaft karne mein masla pesh aaya. Baraye meharbani kuch der baad koshish karein."
            }


# Singleton instance
records_agent = RecordsAgent()

if __name__ == "__main__":
    print("Testing Records Agent...")
    res = records_agent.answer_patient_query("CCC-PK-100001", "Mera aakhri lab test konsa tha aur kya result tha?")
    print("Patient:", res.get("patient_name"))
    print("Answer:\n", res.get("answer"))
