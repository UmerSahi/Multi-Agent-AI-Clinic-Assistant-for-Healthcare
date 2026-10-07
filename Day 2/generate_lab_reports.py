"""
Synthetic Lab Report Generator
Creates 30 realistic Pakistani clinical lab reports across CBC, LFT, Lipid, HbA1c, RFT, Urine R/E.
Includes normal, elevated, and borderline cases.
"""

import os
import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LAB_DIR = BASE_DIR / "lab_reports"
LAB_DIR.mkdir(parents=True, exist_ok=True)
GROUND_TRUTH_FILE = LAB_DIR / "ground_truth_30_reports.json"

PANEL_TEMPLATES = {
    "CBC": [
        {"test_name": "Haemoglobin (Hb)", "unit": "g/dL", "low": 12.0, "high": 17.0},
        {"test_name": "Total Leukocyte Count (WBC)", "unit": "/mcL", "low": 4000.0, "high": 11000.0},
        {"test_name": "Platelet Count", "unit": "/mcL", "low": 150000.0, "high": 450000.0},
        {"test_name": "Hematocrit (PCV)", "unit": "%", "low": 36.0, "high": 50.0}
    ],
    "LFT": [
        {"test_name": "Alanine Aminotransferase (ALT/SGPT)", "unit": "U/L", "low": 7.0, "high": 55.0},
        {"test_name": "Aspartate Aminotransferase (AST/SGOT)", "unit": "U/L", "low": 8.0, "high": 48.0},
        {"test_name": "Total Bilirubin", "unit": "mg/dL", "low": 0.2, "high": 1.2},
        {"test_name": "Alkaline Phosphatase (ALP)", "unit": "U/L", "low": 40.0, "high": 130.0}
    ],
    "LIPID": [
        {"test_name": "Total Cholesterol", "unit": "mg/dL", "low": 100.0, "high": 200.0},
        {"test_name": "Triglycerides", "unit": "mg/dL", "low": 50.0, "high": 150.0},
        {"test_name": "HDL Cholesterol (Good)", "unit": "mg/dL", "low": 40.0, "high": 60.0},
        {"test_name": "LDL Cholesterol (Bad)", "unit": "mg/dL", "low": 60.0, "high": 100.0}
    ],
    "HBA1C": [
        {"test_name": "HbA1c (Glycated Hemoglobin)", "unit": "%", "low": 4.0, "high": 5.6},
        {"test_name": "Estimated Average Glucose (eAG)", "unit": "mg/dL", "low": 70.0, "high": 114.0}
    ],
    "RFT": [
        {"test_name": "Serum Creatinine", "unit": "mg/dL", "low": 0.6, "high": 1.2},
        {"test_name": "Blood Urea Nitrogen (BUN)", "unit": "mg/dL", "low": 7.0, "high": 20.0},
        {"test_name": "Serum Uric Acid", "unit": "mg/dL", "low": 3.5, "high": 7.2}
    ],
    "URINE_RE": [
        {"test_name": "Urine Specific Gravity", "unit": "", "low": 1.005, "high": 1.030},
        {"test_name": "Urine pH", "unit": "", "low": 5.0, "high": 7.5},
        {"test_name": "Urine Pus Cells (WBC)", "unit": "/HPF", "low": 0.0, "high": 5.0}
    ]
}

def generate_reports():
    reports_meta = []
    panel_types = ["CBC"]*8 + ["LFT"]*6 + ["LIPID"]*6 + ["HBA1C"]*4 + ["RFT"]*3 + ["URINE_RE"]*3
    
    cities = ["Lahore", "Islamabad"]
    patient_names = [
        "Muhammad Tariq", "Fatima Bibi", "Ahmed Raza", "Zainab Malik", "Usman Sheikh",
        "Amna Chaudhry", "Bilal Ansari", "Sana Mir", "Hamza Javed", "Sadia Abbasi",
        "Khurram Shah", "Nida Qureshi", "Hassan Butt", "Iqra Dar", "Zubair Hashmi",
        "Rabia Gillani", "Omer Akram", "Bushra Iqbal", "Asad Ashraf", "Farah Tariq",
        "Faisal Rehman", "Mehwish Aziz", "Saad Saeed", "Hira Mahmood", "Waleed Riaz",
        "Zunaira Latif", "Haris Ghaffar", "Anum Afzal", "Zeeshan Hameed", "Maria Siddiqui"
    ]

    for i in range(1, 31):
        report_id = f"RPT-2026-{100 + i}"
        panel_key = panel_types[i - 1]
        patient_name = patient_names[i - 1]
        mrn = f"CCC-PK-{100000 + i}"
        city = cities[i % 2]
        tests = []
        is_abnormal = (i % 2 == 1) # Alternate normal and abnormal

        for param in PANEL_TEMPLATES[panel_key]:
            low = param["low"]
            high = param["high"]
            unit = param["unit"]
            name = param["test_name"]

            if is_abnormal and random.random() < 0.65:
                # generate abnormal value
                if random.choice([True, False]):
                    val = round(high * random.uniform(1.2, 1.8), 2 if low < 10 else 1)
                    flag = "HIGH"
                else:
                    val = round(low * random.uniform(0.5, 0.85), 2 if low < 10 else 1)
                    flag = "LOW"
            else:
                val = round(random.uniform(low, high), 2 if low < 10 else 1)
                flag = "NORMAL"

            tests.append({
                "test_name": name,
                "numeric_value": val,
                "unit": unit,
                "reference_range_low": low,
                "reference_range_high": high,
                "flag": flag
            })

        report_meta = {
            "report_id": report_id,
            "patient_name": patient_name,
            "mrn": mrn,
            "panel": panel_key,
            "city": city,
            "date": f"2026-10-0{random.randint(1, 7)}",
            "tests": tests
        }
        reports_meta.append(report_meta)

        # Generate formatted text document
        doc_text = f"""======================================================================
CITY CARE CLINICS DIAGNOSTIC LABORATORY — {city.upper()} BRANCH
Accredited Clinical Pathology & Biochemistry Division
======================================================================
Report Reference: {report_id}
Patient Name:     {patient_name}
MRN / Patient ID: {mrn}
Collection Date:  {report_meta['date']}
Panel Type:       {panel_key}
----------------------------------------------------------------------
INVESTIGATION                         RESULT       UNIT      REFERENCE RANGE   STATUS
----------------------------------------------------------------------\n"""
        for t in tests:
            ref_str = f"{t['reference_range_low']} - {t['reference_range_high']}"
            doc_text += f"{t['test_name']:<35} {str(t['numeric_value']):<12} {t['unit']:<9} {ref_str:<17} [{t['flag']}]\n"

        doc_text += """----------------------------------------------------------------------
Consultant Pathologist: Dr. Tariq Mahmood (MBBS, FCPS Pathology)
Note: Clinical correlation is required. Not valid for medico-legal purposes.
======================================================================"""

        doc_path = LAB_DIR / f"{report_id}.txt"
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(doc_text)

    with open(GROUND_TRUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(reports_meta, f, indent=2, ensure_ascii=False)

    print(f"Generated 30 synthetic lab report documents and saved ground truth to {GROUND_TRUTH_FILE.name}")

if __name__ == "__main__":
    generate_reports()
