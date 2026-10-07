"""
Test Suite for Prescription Safety Engine
Evaluates deterministic clinical rules across:
1. Allergy conflicts
2. Drug-drug interactions
3. Maximum daily dose ceiling
4. Duplicate generic therapy
5. Special populations (Pregnancy, Pediatric, Geriatric)
"""

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from prescription_safety_engine import safety_engine

class TestPrescriptionSafetyEngine(unittest.TestCase):

    def test_01_allergy_conflict(self):
        """Rule 1: Penicillin allergy conflicting with Augmentin."""
        res = safety_engine.check_allergy_conflicts(["Augmentin"], ["Penicillin"])
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]["severity"], "CRITICAL")
        self.assertIn("Penicillin", res[0]["allergy_matched"])

    def test_02_allergy_cross_reactivity(self):
        """Rule 1: Penicillin allergy cross-reactivity with Cephalosporins (Rocephin)."""
        res = safety_engine.check_allergy_conflicts(["Rocephin"], ["Penicillin"])
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]["severity"], "WARNING")

    def test_03_drug_drug_interaction_nsaid(self):
        """Rule 2: Ibuprofen (Brufen) + Aspirin (Loprin) interaction."""
        res = safety_engine.check_drug_drug_interactions(["Brufen", "Loprin"])
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]["severity"], "CRITICAL")
        self.assertIn("antiplatelet", res[0]["explanation"].lower())

    def test_04_drug_drug_interaction_hyperkalemia(self):
        """Rule 2: ACE Inhibitor (Zestril) + Spironolactone (Aldactone)."""
        res = safety_engine.check_drug_drug_interactions(["Zestril", "Aldactone"])
        self.assertTrue(len(res) > 0)
        self.assertEqual(res[0]["severity"], "CRITICAL")
        self.assertIn("hyperkalemia", res[0]["explanation"].lower())

    def test_05_max_daily_dose_violation(self):
        """Rule 3: Paracetamol (Panadol) exceeding 4000mg/day."""
        violation = safety_engine.check_maximum_daily_dose("Panadol", dose_mg=1000, frequency_per_day=5)
        self.assertIsNotNone(violation)
        self.assertTrue(violation["violation"])
        self.assertEqual(violation["prescribed_daily_mg"], 5000)
        self.assertEqual(violation["maximum_allowed_daily_mg"], 4000)

    def test_06_max_daily_dose_safe(self):
        """Rule 3: Paracetamol (Panadol) within 4000mg/day."""
        violation = safety_engine.check_maximum_daily_dose("Panadol", dose_mg=500, frequency_per_day=3)
        self.assertIsNone(violation)

    def test_07_duplicate_therapy(self):
        """Rule 4: Panadol and Calpol (both Paracetamol)."""
        dups = safety_engine.check_duplicate_therapy(["Panadol", "Calpol"])
        self.assertTrue(len(dups) > 0)
        self.assertEqual(dups[0]["generic_name"].lower(), "paracetamol")

    def test_08_pregnancy_contraindication(self):
        """Rule 5: Atorvastatin (Lipiget) in pregnancy (Category X)."""
        alerts = safety_engine.check_special_populations(["Lipiget"], age=28, is_pregnant=True)
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0]["severity"], "CRITICAL")
        self.assertIn("Pregnancy Category X", alerts[0]["explanation"])

    def test_09_pediatric_aspirin_reye_syndrome(self):
        """Rule 5: Aspirin (Disprin) in child age 8 (Reye's syndrome risk)."""
        alerts = safety_engine.check_special_populations(["Disprin"], age=8, is_pregnant=False)
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0]["severity"], "CRITICAL")
        self.assertIn("Reye's Syndrome", alerts[0]["explanation"])

    def test_10_elderly_beers_criteria(self):
        """Rule 5: Benzodiazepine (Xanax) in age 75."""
        alerts = safety_engine.check_special_populations(["Xanax"], age=75, is_pregnant=False)
        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0]["severity"], "WARNING")
        self.assertIn("Beers Criteria", alerts[0]["explanation"])

    def test_11_full_prescription_safe_case(self):
        """Complete evaluation of a normal safe prescription."""
        eval_res = safety_engine.evaluate_prescription(
            proposed_drugs=["Panadol", "Risek"],
            patient_allergies=["Sulfa"],
            age=35,
            is_pregnant=False,
            dosages=[
                {"drug_name": "Panadol", "dose_mg": 500, "frequency": 3},
                {"drug_name": "Risek", "dose_mg": 20, "frequency": 1}
            ]
        )
        self.assertEqual(eval_res["overall_status"], "SAFE")
        self.assertTrue(eval_res["is_safe_to_dispense"])

if __name__ == "__main__":
    unittest.main()
