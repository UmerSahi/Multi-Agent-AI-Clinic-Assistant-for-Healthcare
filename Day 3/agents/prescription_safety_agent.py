"""
Prescription Safety Agent for City Care Clinics
Intercepts doctor draft prescriptions and validates against deterministic clinical rules:
- Allergy Conflicts & Cross-Reactivity
- Drug-Drug Interactions
- Maximum Daily Dose Thresholds
- Duplicate Generic Therapy
- Special Population Contraindications (Pregnancy, Pediatric, Beers Geriatric)
Produces bilingual clinical warnings with physician-directed explanations in UrduLish & English.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "Day 2"))

from prescription_safety_engine import safety_engine
from llm_factory import get_llm

class PrescriptionCheckReport(BaseModel):
    is_safe: bool
    safety_tier: str # SAFE, WARNING, CRITICAL_CLASH
    doctor_alert_banner: str
    detailed_warnings: List[Dict[str, str]]
    recommended_doctor_actions: List[str]
    patient_friendly_summary_urdulish: str

class PrescriptionSafetyAgent:
    def __init__(self):
        self.llm = get_llm()

    def review_draft_prescription(self, proposed_drugs: List[str], patient_allergies: List[str],
                                  patient_age: int = 30, is_pregnant: bool = False,
                                  dosages: Optional[List[Dict[str, Any]]] = None) -> PrescriptionCheckReport:
        """
        Runs deterministic safety engine and compiles formatted clinical warnings.
        """
        raw_eval = safety_engine.evaluate_prescription(
            proposed_drugs=proposed_drugs,
            patient_allergies=patient_allergies,
            age=patient_age,
            is_pregnant=is_pregnant,
            dosages=dosages
        )

        overall_status = raw_eval["overall_status"]
        is_safe = raw_eval["is_safe_to_dispense"]

        # Compile warnings
        warnings = []
        # Allergies
        for a in raw_eval.get("allergy_conflicts", []):
            warnings.append({
                "type": "ALLERGY_CONFLICT",
                "severity": a.get("severity", "CRITICAL"),
                "drug": a.get("drug", ""),
                "description": f"⚠️ Patient ko {a.get('allergy_matched','')} se allergy hai — {a.get('drug','')} contraindicated hai. ({a.get('explanation','')})"
            })
        # Drug interactions
        for d in raw_eval.get("drug_interactions", []):
            warnings.append({
                "type": "DRUG_INTERACTION",
                "severity": d.get("severity", "CRITICAL"),
                "drug": f"{d.get('drug_1','')} + {d.get('drug_2','')}",
                "description": f"⚠️ Drug Clash: {d.get('drug_1','')} aur {d.get('drug_2','')} ko ek sath dena mehfooz nahi hai. {d.get('explanation','')}"
            })
        # Dose violations
        for v in raw_eval.get("dose_limit_violations", []):
            warnings.append({
                "type": "DOSE_CEILING_EXCEEDED",
                "severity": "CRITICAL",
                "drug": v.get("drug", ""),
                "description": f"⚠️ Max Daily Dose Alert: {v.get('drug','')} ki prescribed dose ({v.get('prescribed_daily_mg',0)}mg/day) maximum safe limit ({v.get('maximum_allowed_daily_mg',0)}mg/day) se zyada hai."
            })
        # Duplicate therapy
        for dup in raw_eval.get("duplicate_therapy", []):
            warnings.append({
                "type": "DUPLICATE_THERAPY",
                "severity": "WARNING",
                "drug": f"{dup.get('brand_1','')} + {dup.get('brand_2','')}",
                "description": f"⚠️ Duplicate Generic: '{dup.get('brand_1','')}' aur '{dup.get('brand_2','')}' dono mein same generic ({dup.get('generic_name','')}) mojood hai."
            })
        # Special populations
        for sp in raw_eval.get("special_population_alerts", []):
            warnings.append({
                "type": f"SPECIAL_POPULATION_{sp.get('population','').upper()}",
                "severity": sp.get("severity", "WARNING"),
                "drug": sp.get("drug", ""),
                "description": f"⚠️ {sp.get('population','')}: {sp.get('explanation','')}"
            })

        # Banner & Actions
        if overall_status == "CRITICAL_CLASH":
            banner = "🚨 CRITICAL PRESCRIPTION SAFETY ALERT — DOCTOR INTERVENTION REQUIRED"
            actions = [
                "Discontinue or replace the clashing medicine with a safe alternative.",
                "Review documented patient allergies and confirm tolerance.",
                "Adjust dosage within maximum daily therapeutic ceiling."
            ]
            urdu_summary = "⚠️ Is nuskha (prescription) mein ahem dawayi clash ya allergy ka khatra paya gaya hai. Baraye meharbani doctor se tabdeeli ka mashwara lein."
        elif overall_status == "WARNING":
            banner = "⚠️ PRESCRIPTION SAFETY WARNING — REVIEW ADVISED"
            actions = [
                "Verify dosing interval and patient renal/hepatic function.",
                "Counsel patient on potential mild interactions and monitoring signs."
            ]
            urdu_summary = "⚠️ Dawaayein lete waqt ehtiyat zaroori hai. Doctor ki hidayat ke mutabiq auqaat ka khas khayal rakhein."
        else:
            banner = "✅ PRESCRIPTION VERIFIED SAFE — ZERO CLASHES DETECTED"
            actions = ["Approved for standard pharmacy dispensing."]
            urdu_summary = "✅ Tamam tajweez karda dawaayein aap ki record shuda tareekh ke mutabiq mehfooz hain."

        return PrescriptionCheckReport(
            is_safe=is_safe,
            safety_tier=overall_status,
            doctor_alert_banner=banner,
            detailed_warnings=warnings,
            recommended_doctor_actions=actions,
            patient_friendly_summary_urdulish=urdu_summary
        )


# Singleton instance
prescription_safety_agent = PrescriptionSafetyAgent()

if __name__ == "__main__":
    print("Testing Prescription Safety Agent...")
    res = prescription_safety_agent.review_draft_prescription(
        proposed_drugs=["Augmentin 625mg", "Brufen 400mg", "Loprin 75mg"],
        patient_allergies=["Penicillin"],
        patient_age=32,
        is_pregnant=False
    )
    print("\nBanner:", res.doctor_alert_banner)
    print("Status:", res.safety_tier)
    print("Warnings count:", len(res.detailed_warnings))
    for w in res.detailed_warnings:
        print(" -", w["description"])
