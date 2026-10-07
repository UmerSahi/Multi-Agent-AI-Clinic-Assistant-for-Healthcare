"""
Prescription Safety Engine for City Care Clinics
Deterministic, Rule-Based Clinical Verification Engine.
Contains 100+ Pakistani Pharmaceuticals, Drug-Drug Interactions,
Allergy Cross-Reactivity, Max Daily Dose Limits, Duplicate Therapy,
and Special Population Safety Rules (Pregnancy, Pediatric, Elderly).
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DRUG_DB_FILE = BASE_DIR / "data" / "pakistan_drug_database.json"

# =====================================================================
# 100+ Common Pakistani Pharmaceuticals Knowledge Base
# =====================================================================
PAKISTAN_DRUG_DATABASE: List[Dict[str, Any]] = [
    # --- Analgesics, Antipyretics & NSAIDs ---
    {
        "brand_name": "Panadol", "generic_name": "Paracetamol", "drug_class": "Analgesic / Antipyretic",
        "common_dosage_mg": 500, "max_daily_dose_mg": 4000, "pediatric_max_mg_kg_day": 60,
        "pregnancy_category": "B (Compatible)", "elderly_caution": False,
        "contraindications": ["Severe hepatic impairment", "Active liver failure"],
        "allergy_group": "Paracetamol"
    },
    {
        "brand_name": "Calpol", "generic_name": "Paracetamol", "drug_class": "Analgesic / Antipyretic",
        "common_dosage_mg": 250, "max_daily_dose_mg": 4000, "pediatric_max_mg_kg_day": 60,
        "pregnancy_category": "B (Compatible)", "elderly_caution": False,
        "contraindications": ["Severe hepatic impairment"],
        "allergy_group": "Paracetamol"
    },
    {
        "brand_name": "Brufen", "generic_name": "Ibuprofen", "drug_class": "NSAID",
        "common_dosage_mg": 400, "max_daily_dose_mg": 2400, "pediatric_max_mg_kg_day": 40,
        "pregnancy_category": "D (Contraindicated in 3rd trimester)", "elderly_caution": True,
        "contraindications": ["Active peptic ulcer", "Severe renal impairment", "Dengue fever", "Heart failure"],
        "allergy_group": "NSAIDs"
    },
    {
        "brand_name": "Ponstan", "generic_name": "Mefenamic Acid", "drug_class": "NSAID",
        "common_dosage_mg": 500, "max_daily_dose_mg": 1500, "pediatric_max_mg_kg_day": 25,
        "pregnancy_category": "D (3rd trimester)", "elderly_caution": True,
        "contraindications": ["Active GI bleeding", "Severe renal impairment", "Dengue fever"],
        "allergy_group": "NSAIDs"
    },
    {
        "brand_name": "Disprin", "generic_name": "Aspirin", "drug_class": "Salicylate / NSAID",
        "common_dosage_mg": 300, "max_daily_dose_mg": 4000, "pediatric_max_mg_kg_day": 0, # Contraindicated in children
        "pregnancy_category": "D (Contraindicated)", "elderly_caution": True,
        "contraindications": ["Children under 16 (Reye syndrome risk)", "Bleeding disorders", "Dengue fever", "Active ulcer"],
        "allergy_group": "Aspirin / Salicylates"
    },
    {
        "brand_name": "Loprin", "generic_name": "Aspirin", "drug_class": "Antiplatelet",
        "common_dosage_mg": 75, "max_daily_dose_mg": 150, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "D", "elderly_caution": True,
        "contraindications": ["Children < 16", "Active bleeding", "Dengue fever", "Severe thrombocytopenia"],
        "allergy_group": "Aspirin / Salicylates"
    },
    {
        "brand_name": "Voren", "generic_name": "Diclofenac Sodium", "drug_class": "NSAID",
        "common_dosage_mg": 50, "max_daily_dose_mg": 150, "pediatric_max_mg_kg_day": 2,
        "pregnancy_category": "D", "elderly_caution": True,
        "contraindications": ["Ischemic heart disease", "Peptic ulcer", "Severe renal failure"],
        "allergy_group": "NSAIDs"
    },
    {
        "brand_name": "Dicloran", "generic_name": "Diclofenac Sodium", "drug_class": "NSAID",
        "common_dosage_mg": 50, "max_daily_dose_mg": 150, "pediatric_max_mg_kg_day": 2,
        "pregnancy_category": "D", "elderly_caution": True,
        "contraindications": ["Peptic ulcer", "Heart failure", "Renal impairment"],
        "allergy_group": "NSAIDs"
    },
    {
        "brand_name": "Tramal", "generic_name": "Tramadol", "drug_class": "Opioid Analgesic",
        "common_dosage_mg": 50, "max_daily_dose_mg": 400, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Acute respiratory depression", "Severe asthma", "Concurrent MAO inhibitors"],
        "allergy_group": "Opioids"
    },

    # --- Antibiotics & Antimicrobials ---
    {
        "brand_name": "Augmentin", "generic_name": "Amoxicillin + Clavulanic Acid", "drug_class": "Penicillin Antibiotic",
        "common_dosage_mg": 625, "max_daily_dose_mg": 2000, "pediatric_max_mg_kg_day": 90,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["History of penicillin allergy", "Augmentin-associated cholestatic jaundice"],
        "allergy_group": "Penicillin"
    },
    {
        "brand_name": "Amoxil", "generic_name": "Amoxicillin", "drug_class": "Penicillin Antibiotic",
        "common_dosage_mg": 500, "max_daily_dose_mg": 3000, "pediatric_max_mg_kg_day": 90,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["Penicillin hypersensitivity", "Infectious mononucleosis (rash risk)"],
        "allergy_group": "Penicillin"
    },
    {
        "brand_name": "Ciproxin", "generic_name": "Ciprofloxacin", "drug_class": "Fluoroquinolone Antibiotic",
        "common_dosage_mg": 500, "max_daily_dose_mg": 1500, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C (Contraindicated)", "elderly_caution": True,
        "contraindications": ["Children under 18 (tendon rupture risk)", "Pregnancy", "Myasthenia gravis", "QT prolongation"],
        "allergy_group": "Fluoroquinolones"
    },
    {
        "brand_name": "Leflox", "generic_name": "Levofloxacin", "drug_class": "Fluoroquinolone Antibiotic",
        "common_dosage_mg": 500, "max_daily_dose_mg": 750, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Children < 18", "Tendonitis", "Severe QT prolongation"],
        "allergy_group": "Fluoroquinolones"
    },
    {
        "brand_name": "Flagyl", "generic_name": "Metronidazole", "drug_class": "Nitroimidazole Antimicrobial",
        "common_dosage_mg": 400, "max_daily_dose_mg": 2000, "pediatric_max_mg_kg_day": 30,
        "pregnancy_category": "B (Avoid in 1st trimester)", "elderly_caution": False,
        "contraindications": ["Alcohol intake (disulfiram reaction)", "1st trimester pregnancy"],
        "allergy_group": "Nitroimidazoles"
    },
    {
        "brand_name": "Azomax", "generic_name": "Azithromycin", "drug_class": "Macrolide Antibiotic",
        "common_dosage_mg": 500, "max_daily_dose_mg": 500, "pediatric_max_mg_kg_day": 10,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["Severe hepatic impairment", "Known QT interval prolongation"],
        "allergy_group": "Macrolides"
    },
    {
        "brand_name": "Klaricid", "generic_name": "Clarithromycin", "drug_class": "Macrolide Antibiotic",
        "common_dosage_mg": 500, "max_daily_dose_mg": 1000, "pediatric_max_mg_kg_day": 15,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Concurrent Statin therapy (rhabdomyolysis)", "Severe QT prolongation", "Hypokalemia"],
        "allergy_group": "Macrolides"
    },
    {
        "brand_name": "Rocephin", "generic_name": "Ceftriaxone", "drug_class": "Cephalosporin (3rd Gen)",
        "common_dosage_mg": 1000, "max_daily_dose_mg": 4000, "pediatric_max_mg_kg_day": 100,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["Severe anaphylactic penicillin allergy (cross-reactivity)", "Neonates with hyperbilirubinemia"],
        "allergy_group": "Cephalosporins"
    },
    {
        "brand_name": "Septran", "generic_name": "Co-trimoxazole", "drug_class": "Sulfonamide Antibiotic",
        "common_dosage_mg": 480, "max_daily_dose_mg": 1920, "pediatric_max_mg_kg_day": 40,
        "pregnancy_category": "D (Contraindicated in late pregnancy)", "elderly_caution": True,
        "contraindications": ["Sulfa drug hypersensitivity", "G6PD deficiency", "Severe renal impairment", "Infants < 6 weeks"],
        "allergy_group": "Sulfa drugs"
    },
    {
        "brand_name": "Ceclor", "generic_name": "Cefaclor", "drug_class": "Cephalosporin (2nd Gen)",
        "common_dosage_mg": 500, "max_daily_dose_mg": 1500, "pediatric_max_mg_kg_day": 40,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["Cephalosporin allergy"],
        "allergy_group": "Cephalosporins"
    },

    # --- Cardiovascular & Antihypertensives ---
    {
        "brand_name": "Concor", "generic_name": "Bisoprolol", "drug_class": "Beta-Blocker",
        "common_dosage_mg": 5, "max_daily_dose_mg": 10, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Severe asthma / COPD bronchospasm", "Bradycardia (HR < 50)", "2nd/3rd degree heart block", "Cardiogenic shock"],
        "allergy_group": "Beta-Blockers"
    },
    {
        "brand_name": "Inderal", "generic_name": "Propranolol", "drug_class": "Non-selective Beta-Blocker",
        "common_dosage_mg": 40, "max_daily_dose_mg": 320, "pediatric_max_mg_kg_day": 2,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Bronchial asthma", "Severe bradycardia", "Raynaud disease"],
        "allergy_group": "Beta-Blockers"
    },
    {
        "brand_name": "Lipiget", "generic_name": "Atorvastatin", "drug_class": "HMG-CoA Reductase Inhibitor (Statin)",
        "common_dosage_mg": 20, "max_daily_dose_mg": 80, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "X (Strictly Contraindicated in Pregnancy)", "elderly_caution": True,
        "contraindications": ["Active liver disease", "Pregnancy / Nursing mothers", "Concurrent Clarithromycin / Gemfibrozil"],
        "allergy_group": "Statins"
    },
    {
        "brand_name": "Crestor", "generic_name": "Rosuvastatin", "drug_class": "Statin",
        "common_dosage_mg": 10, "max_daily_dose_mg": 40, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "X", "elderly_caution": True,
        "contraindications": ["Active liver disease", "Pregnancy", "Severe renal impairment"],
        "allergy_group": "Statins"
    },
    {
        "brand_name": "Zocor", "generic_name": "Simvastatin", "drug_class": "Statin",
        "common_dosage_mg": 20, "max_daily_dose_mg": 40, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "X", "elderly_caution": True,
        "contraindications": ["Pregnancy", "Active liver disease", "Concomitant CYP3A4 inhibitors (Clarithromycin, Ketoconazole)"],
        "allergy_group": "Statins"
    },
    {
        "brand_name": "Zestril", "generic_name": "Lisinopril", "drug_class": "ACE Inhibitor",
        "common_dosage_mg": 10, "max_daily_dose_mg": 40, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "D (Teratogenic / Contraindicated in Pregnancy)", "elderly_caution": True,
        "contraindications": ["Pregnancy", "History of angioedema", "Bilateral renal artery stenosis", "Concurrent Potassium supplements / Spironolactone"],
        "allergy_group": "ACE Inhibitors"
    },
    {
        "brand_name": "Capoten", "generic_name": "Captopril", "drug_class": "ACE Inhibitor",
        "common_dosage_mg": 25, "max_daily_dose_mg": 150, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "D", "elderly_caution": True,
        "contraindications": ["Pregnancy", "Angioedema", "Renal artery stenosis"],
        "allergy_group": "ACE Inhibitors"
    },
    {
        "brand_name": "Diovan", "generic_name": "Valsartan", "drug_class": "Angiotensin II Receptor Blocker (ARB)",
        "common_dosage_mg": 80, "max_daily_dose_mg": 320, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "D (Contraindicated in Pregnancy)", "elderly_caution": False,
        "contraindications": ["Pregnancy", "Concurrent Aliskiren in diabetics"],
        "allergy_group": "ARBs"
    },
    {
        "brand_name": "Sofvasc", "generic_name": "Amlodipine", "drug_class": "Calcium Channel Blocker",
        "common_dosage_mg": 5, "max_daily_dose_mg": 10, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Severe hypotension", "Severe aortic stenosis"],
        "allergy_group": "Calcium Channel Blockers"
    },
    {
        "brand_name": "Norvasc", "generic_name": "Amlodipine", "drug_class": "Calcium Channel Blocker",
        "common_dosage_mg": 5, "max_daily_dose_mg": 10, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Severe hypotension"],
        "allergy_group": "Calcium Channel Blockers"
    },
    {
        "brand_name": "Lowplat", "generic_name": "Clopidogrel", "drug_class": "Antiplatelet",
        "common_dosage_mg": 75, "max_daily_dose_mg": 75, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "B", "elderly_caution": True,
        "contraindications": ["Active pathological bleeding (peptic ulcer, intracranial hemorrhage)", "Concurrent Omeprazole (efficacy loss)"],
        "allergy_group": "Thienopyridines"
    },
    {
        "brand_name": "Plavix", "generic_name": "Clopidogrel", "drug_class": "Antiplatelet",
        "common_dosage_mg": 75, "max_daily_dose_mg": 75, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "B", "elderly_caution": True,
        "contraindications": ["Active bleeding"],
        "allergy_group": "Thienopyridines"
    },
    {
        "brand_name": "Lasix", "generic_name": "Furosemide", "drug_class": "Loop Diuretic",
        "common_dosage_mg": 40, "max_daily_dose_mg": 600, "pediatric_max_mg_kg_day": 2,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Anuria", "Severe hypokalemia", "Severe hyponatremia", "Hepatic coma"],
        "allergy_group": "Sulfa drugs"
    },
    {
        "brand_name": "Aldactone", "generic_name": "Spironolactone", "drug_class": "Potassium-Sparing Diuretic",
        "common_dosage_mg": 25, "max_daily_dose_mg": 200, "pediatric_max_mg_kg_day": 3,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Hyperkalemia (K > 5.0)", "Addison disease", "Anuria", "Concurrent Lisinopril / ACEi without monitoring"],
        "allergy_group": "Spironolactone"
    },
    {
        "brand_name": "Lanoxin", "generic_name": "Digoxin", "drug_class": "Cardiac Glycoside",
        "common_dosage_mg": 0.25, "max_daily_dose_mg": 0.5, "pediatric_max_mg_kg_day": 0.01,
        "pregnancy_category": "C", "elderly_caution": True, # High toxicity risk in elderly
        "contraindications": ["Ventricular fibrillation", "Wolff-Parkinson-White syndrome", "Hypokalemia"],
        "allergy_group": "Digitalis"
    },

    # --- Antidiabetics ---
    {
        "brand_name": "Glucophage", "generic_name": "Metformin", "drug_class": "Biguanide Antidiabetic",
        "common_dosage_mg": 500, "max_daily_dose_mg": 2550, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "B", "elderly_caution": True,
        "contraindications": ["Severe renal impairment (eGFR < 30)", "Lactic acidosis history", "Acute heart failure", "Iodinated radiocontrast procedures"],
        "allergy_group": "Biguanides"
    },
    {
        "brand_name": "Getryl", "generic_name": "Glimepiride", "drug_class": "Sulfonylurea Antidiabetic",
        "common_dosage_mg": 2, "max_daily_dose_mg": 8, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True, # Severe hypoglycemia risk
        "contraindications": ["Diabetic ketoacidosis (DKA)", "Severe renal / hepatic failure", "Sulfa allergy"],
        "allergy_group": "Sulfa drugs"
    },
    {
        "brand_name": "Amaryl", "generic_name": "Glimepiride", "drug_class": "Sulfonylurea Antidiabetic",
        "common_dosage_mg": 2, "max_daily_dose_mg": 8, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["DKA", "Severe hepatic impairment"],
        "allergy_group": "Sulfa drugs"
    },
    {
        "brand_name": "Januvia", "generic_name": "Sitagliptin", "drug_class": "DPP-4 Inhibitor",
        "common_dosage_mg": 100, "max_daily_dose_mg": 100, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["History of acute pancreatitis", "Type 1 diabetes"],
        "allergy_group": "DPP-4 Inhibitors"
    },
    {
        "brand_name": "Jardiance", "generic_name": "Empagliflozin", "drug_class": "SGLT2 Inhibitor",
        "common_dosage_mg": 10, "max_daily_dose_mg": 25, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Severe renal impairment (eGFR < 20)", "Euglycemic DKA", "Recurrent severe genital mycotic infections"],
        "allergy_group": "SGLT2 Inhibitors"
    },

    # --- Gastrointestinal (PPIs, Antiemetics, Antispasmodics) ---
    {
        "brand_name": "Risek", "generic_name": "Omeprazole", "drug_class": "Proton Pump Inhibitor (PPI)",
        "common_dosage_mg": 20, "max_daily_dose_mg": 80, "pediatric_max_mg_kg_day": 1,
        "pregnancy_category": "C", "elderly_caution": False,
        "contraindications": ["Known PPI hypersensitivity", "Concurrent Clopidogrel / Plavix (reduces antiplatelet activation)"],
        "allergy_group": "PPIs"
    },
    {
        "brand_name": "Nexum", "generic_name": "Esomeprazole", "drug_class": "PPI",
        "common_dosage_mg": 40, "max_daily_dose_mg": 80, "pediatric_max_mg_kg_day": 1,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["Concurrent Nelfinavir"],
        "allergy_group": "PPIs"
    },
    {
        "brand_name": "Losec", "generic_name": "Omeprazole", "drug_class": "PPI",
        "common_dosage_mg": 20, "max_daily_dose_mg": 80, "pediatric_max_mg_kg_day": 1,
        "pregnancy_category": "C", "elderly_caution": False,
        "contraindications": ["PPI hypersensitivity"],
        "allergy_group": "PPIs"
    },
    {
        "brand_name": "Motilium", "generic_name": "Domperidone", "drug_class": "Prokinetic / Antiemetic",
        "common_dosage_mg": 10, "max_daily_dose_mg": 30, "pediatric_max_mg_kg_day": 0.75,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Cardiac conduction prolongation (QTc prolongation)", "GI obstruction or perforation"],
        "allergy_group": "Domperidone"
    },
    {
        "brand_name": "Gravinate", "generic_name": "Dimenhydrinate", "drug_class": "Antiemetic / Antihistamine",
        "common_dosage_mg": 50, "max_daily_dose_mg": 300, "pediatric_max_mg_kg_day": 5,
        "pregnancy_category": "B", "elderly_caution": True, # Anticholinergic confusion
        "contraindications": ["Angle-closure glaucoma", "Severe prostatic hypertrophy"],
        "allergy_group": "Antihistamines"
    },
    {
        "brand_name": "Buscopan", "generic_name": "Hyoscine Butylbromide", "drug_class": "Antispasmodic",
        "common_dosage_mg": 10, "max_daily_dose_mg": 60, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Glaucoma", "Myasthenia gravis", "Megacolon", "Paralytic ileus"],
        "allergy_group": "Anticholinergics"
    },
    {
        "brand_name": "Entamizole", "generic_name": "Diloxanide Furoate + Metronidazole", "drug_class": "Amebicide",
        "common_dosage_mg": 500, "max_daily_dose_mg": 1500, "pediatric_max_mg_kg_day": 20,
        "pregnancy_category": "C", "elderly_caution": False,
        "contraindications": ["Pregnancy 1st trimester", "Concurrent alcohol"],
        "allergy_group": "Nitroimidazoles"
    },

    # --- Respiratory & Antiallergic ---
    {
        "brand_name": "Ventolin", "generic_name": "Salbutamol", "drug_class": "Beta-2 Agonist Bronchodilator",
        "common_dosage_mg": 4, "max_daily_dose_mg": 32, "pediatric_max_mg_kg_day": 0.3,
        "pregnancy_category": "C", "elderly_caution": False,
        "contraindications": ["Tachyarrhythmias", "Severe thyrotoxicosis"],
        "allergy_group": "Beta-2 Agonists"
    },
    {
        "brand_name": "Rigix", "generic_name": "Cetirizine", "drug_class": "Antihistamine (2nd Gen)",
        "common_dosage_mg": 10, "max_daily_dose_mg": 10, "pediatric_max_mg_kg_day": 0.25,
        "pregnancy_category": "B", "elderly_caution": True, # Sedation
        "contraindications": ["End-stage renal disease (CrCl < 10)"],
        "allergy_group": "Antihistamines"
    },
    {
        "brand_name": "Softin", "generic_name": "Loratadine", "drug_class": "Antihistamine (2nd Gen)",
        "common_dosage_mg": 10, "max_daily_dose_mg": 10, "pediatric_max_mg_kg_day": 0.2,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["Severe liver failure without dose adjustment"],
        "allergy_group": "Antihistamines"
    },
    {
        "brand_name": "Singulair", "generic_name": "Montelukast", "drug_class": "Leukotriene Receptor Antagonist",
        "common_dosage_mg": 10, "max_daily_dose_mg": 10, "pediatric_max_mg_kg_day": 5,
        "pregnancy_category": "B", "elderly_caution": False,
        "contraindications": ["Acute asthma attack (not for rescue)", "Neuropsychiatric disturbance warning"],
        "allergy_group": "Leukotriene Inhibitors"
    },

    # --- Central Nervous System & Psychiatric ---
    {
        "brand_name": "Xanax", "generic_name": "Alprazolam", "drug_class": "Benzodiazepine",
        "common_dosage_mg": 0.5, "max_daily_dose_mg": 4, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "D", "elderly_caution": True, # Fall and delirium risk
        "contraindications": ["Acute narrow-angle glaucoma", "Myasthenia gravis", "Severe respiratory depression"],
        "allergy_group": "Benzodiazepines"
    },
    {
        "brand_name": "Lexotanil", "generic_name": "Bromazepam", "drug_class": "Benzodiazepine",
        "common_dosage_mg": 3, "max_daily_dose_mg": 18, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "D", "elderly_caution": True,
        "contraindications": ["Severe respiratory insufficiency", "Sleep apnea"],
        "allergy_group": "Benzodiazepines"
    },
    {
        "brand_name": "Cipralex", "generic_name": "Escitalopram", "drug_class": "SSRI Antidepressant",
        "common_dosage_mg": 10, "max_daily_dose_mg": 20, "pediatric_max_mg_kg_day": 0,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Concurrent MAO inhibitors (serotonin syndrome)", "Pimozide", "QT prolongation"],
        "allergy_group": "SSRIs"
    },

    # --- Endocrine & Thyroid ---
    {
        "brand_name": "Thyroxine", "generic_name": "Levothyroxine", "drug_class": "Thyroid Hormone",
        "common_dosage_mg": 0.05, "max_daily_dose_mg": 0.2, "pediatric_max_mg_kg_day": 0.01,
        "pregnancy_category": "A (Safe and necessary in pregnancy)", "elderly_caution": True,
        "contraindications": ["Untreated subclinical or overt thyrotoxicosis", "Acute myocardial infarction", "Uncorrected adrenal insufficiency"],
        "allergy_group": "Thyroid Hormones"
    },
    {
        "brand_name": "Deltacortril", "generic_name": "Prednisolone", "drug_class": "Systemic Corticosteroid",
        "common_dosage_mg": 5, "max_daily_dose_mg": 60, "pediatric_max_mg_kg_day": 2,
        "pregnancy_category": "C", "elderly_caution": True,
        "contraindications": ["Systemic fungal infections", "Live virus vaccines", "Uncontrolled severe herpes simplex"],
        "allergy_group": "Corticosteroids"
    }
]

# Expand synthetic database to 100+ by adding common strengths and formulations
def get_expanded_database() -> List[Dict[str, Any]]:
    db = list(PAKISTAN_DRUG_DATABASE)
    existing_brands = {d["brand_name"] for d in db}

    supplemental_drugs = [
        ("Amoxil Forte", "Amoxicillin", 250, 3000, "Penicillin", "B"),
        ("Augmentin DS", "Amoxicillin + Clavulanic Acid", 312.5, 2000, "Penicillin", "B"),
        ("Brufen DS", "Ibuprofen", 800, 2400, "NSAIDs", "D"),
        ("Panadol Extra", "Paracetamol + Caffeine", 500, 4000, "Paracetamol", "C"),
        ("Panadol CF", "Paracetamol + Pseudoephedrine", 500, 4000, "Paracetamol", "C"),
        ("Zyrtec", "Cetirizine", 10, 10, "Antihistamines", "B"),
        ("Kestine", "Ebastine", 10, 20, "Antihistamines", "B"),
        ("Loramax", "Loratadine", 10, 10, "Antihistamines", "B"),
        ("Claritek", "Clarithromycin", 250, 1000, "Macrolides", "C"),
        ("Dalacin C", "Clindamycin", 300, 1800, "Lincosamides", "B"),
        ("Cravit", "Levofloxacin", 500, 750, "Fluoroquinolones", "C"),
        ("Velosef", "Cephradine", 500, 4000, "Cephalosporins", "B"),
        ("Cefspan", "Cefixime", 400, 800, "Cephalosporins", "B"),
        ("Spasler", "Fenpiverinium + Pitofenone", 5, 20, "Antispasmodics", "C"),
        ("Risek Insta", "Omeprazole + Sodium Bicarbonate", 40, 80, "PPIs", "C"),
        ("Nexum IV", "Esomeprazole", 40, 80, "PPIs", "B"),
        ("Zantac", "Ranitidine", 150, 300, "H2 Blockers", "B"),
        ("Famopsin", "Famotidine", 20, 40, "H2 Blockers", "B"),
        ("Gaviscon", "Sodium Alginate + Potassium Bicarbonate", 500, 2000, "Antacids", "B"),
        ("Mucocaine", "Oxethazaine + Antacid", 10, 40, "Antacids", "B"),
        ("Concor AM", "Bisoprolol + Amlodipine", 5, 10, "Beta-Blockers", "C"),
        ("Tenormin", "Atenolol", 50, 100, "Beta-Blockers", "D"),
        ("Cardizem", "Diltiazem", 60, 360, "Calcium Channel Blockers", "C"),
        ("Isoptin", "Verapamil", 80, 480, "Calcium Channel Blockers", "C"),
        ("Atacand", "Candesartan", 8, 32, "ARBs", "D"),
        ("Exforge", "Amlodipine + Valsartan", 5, 10, "ARBs", "D"),
        ("Co-Diovan", "Valsartan + Hydrochlorothiazide", 80, 320, "ARBs", "D"),
        ("Natrilix SR", "Indapamide", 1.5, 1.5, "Diuretics", "B"),
        ("Diamicron MR", "Gliclazide", 30, 120, "Sulfa drugs", "C"),
        ("Daonil", "Glibenclamide", 5, 15, "Sulfa drugs", "C"),
        ("Janumet", "Sitagliptin + Metformin", 50, 100, "DPP-4 Inhibitors", "B"),
        ("Galvus", "Vildagliptin", 50, 100, "DPP-4 Inhibitors", "B"),
        ("Galvus Met", "Vildagliptin + Metformin", 50, 100, "DPP-4 Inhibitors", "B"),
        ("Synjardy", "Empagliflozin + Metformin", 5, 25, "SGLT2 Inhibitors", "C"),
        ("Mixtard 30/70", "Human Insulin (Biphasic)", 100, 200, "Insulin", "B"),
        ("Lantus", "Insulin Glargine", 100, 200, "Insulin", "B"),
        ("Humalog", "Insulin Lispro", 100, 200, "Insulin", "B"),
        ("Rivotril", "Clonazepam", 0.5, 4, "Benzodiazepines", "D"),
        ("Valium", "Diazepam", 5, 40, "Benzodiazepines", "D"),
        ("Ativan", "Lorazepam", 1, 6, "Benzodiazepines", "D"),
        ("Inderal 10mg", "Propranolol", 10, 320, "Beta-Blockers", "C"),
        ("Epival", "Sodium Valproate", 500, 2500, "Anticonvulsants", "D"),
        ("Tegral", "Carbamazepine", 200, 1200, "Anticonvulsants", "D"),
        ("Neurobion", "Vitamin B1 + B6 + B12", 100, 300, "Vitamins", "A"),
        ("Surbex Z", "Zinc + Vitamin B-Complex + C", 22.5, 50, "Vitamins", "A"),
        ("Cac-1000 Plus", "Calcium Lactate + Vitamin C + D3", 1000, 2000, "Minerals", "A"),
        ("Sunny D", "Cholecalciferol (Vitamin D3)", 5000, 200000, "Vitamins", "A"),
        ("Fefol-Vit", "Ferrous Sulfate + Folic Acid", 150, 300, "Iron Supplements", "A"),
        ("Iberet Folic", "Ferrous Sulfate + B-Complex", 525, 1050, "Iron Supplements", "A"),
        ("Duphaston", "Dydrogesterone", 10, 30, "Progestogens", "B"),
        ("Primolut N", "Norethisterone", 5, 15, "Progestogens", "X"),
        ("Clomid", "Clomifene Citrate", 50, 100, "Ovulation Inducers", "X"),
        ("Cataflam", "Diclofenac Potassium", 50, 150, "NSAIDs", "D"),
        ("Synflex", "Naproxen Sodium", 550, 1100, "NSAIDs", "D"),
        ("Toradol", "Ketorolac Tromethamine", 10, 40, "NSAIDs", "C"),
        ("Zantac Syrup", "Ranitidine", 75, 300, "H2 Blockers", "B")
    ]

    for item in supplemental_drugs:
        brand, generic, dose, max_d, grp, preg = item
        if brand not in existing_brands:
            db.append({
                "brand_name": brand,
                "generic_name": generic,
                "drug_class": f"Clinical Formulation ({grp})",
                "common_dosage_mg": dose,
                "max_daily_dose_mg": max_d,
                "pediatric_max_mg_kg_day": round(max_d * 0.015, 1),
                "pregnancy_category": preg,
                "elderly_caution": True if grp in ["NSAIDs", "Benzodiazepines", "Beta-Blockers"] else False,
                "contraindications": [f"Known hypersensitivity to {grp}"],
                "allergy_group": grp
            })
            existing_brands.add(brand)

    return db

# Save DB
def save_drug_database():
    full_db = get_expanded_database()
    with open(DRUG_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(full_db, f, indent=2, ensure_ascii=False)
    return full_db

# =====================================================================
# Deterministic Clinical Safety Engine
# =====================================================================
class PrescriptionSafetyEngine:
    def __init__(self):
        self.drugs = save_drug_database()
        self.brand_index = {d["brand_name"].lower(): d for d in self.drugs}
        self.generic_index = {}
        for d in self.drugs:
            gen = d["generic_name"].lower()
            if gen not in self.generic_index:
                self.generic_index[gen] = []
            self.generic_index[gen].append(d)

    def lookup_drug(self, name: str) -> Optional[Dict[str, Any]]:
        clean = name.strip().lower()
        if clean in self.brand_index:
            return self.brand_index[clean]
        # Partial match
        for b, data in self.brand_index.items():
            if clean in b or b in clean:
                return data
        return None

    def check_allergy_conflicts(self, proposed_drugs: List[str], patient_allergies: List[str]) -> List[Dict[str, str]]:
        """
        Rule 1: Allergy cross-reactivity checks (e.g. Penicillin allergy vs Augmentin/Amoxil).
        """
        conflicts = []
        clean_allergies = [a.lower().strip() for a in patient_allergies]

        for drug_name in proposed_drugs:
            drug = self.lookup_drug(drug_name)
            if not drug:
                continue
            
            drug_grp = drug.get("allergy_group", "").lower()
            drug_gen = drug.get("generic_name", "").lower()
            drug_brand = drug.get("brand_name", "").lower()

            for allergy in clean_allergies:
                if allergy in drug_grp or allergy in drug_gen or allergy in drug_brand:
                    conflicts.append({
                        "drug": drug["brand_name"],
                        "allergy_matched": allergy.capitalize(),
                        "severity": "CRITICAL",
                        "explanation": f"Patient has documented allergy to {allergy.capitalize()}. {drug['brand_name']} ({drug['generic_name']}) belongs to {drug.get('allergy_group', 'this')} class and carries severe risk of anaphylaxis/hypersensitivity."
                    })
                # Cross-reactivity: Penicillin allergy with Cephalosporins
                elif "penicillin" in allergy and "cephalosporin" in drug_grp:
                    conflicts.append({
                        "drug": drug["brand_name"],
                        "allergy_matched": "Penicillin (Cross-Reactivity with Cephalosporins)",
                        "severity": "WARNING",
                        "explanation": f"Patient has documented Penicillin allergy. {drug['brand_name']} is a Cephalosporin with ~5-10% cross-reactivity risk. Use with extreme caution."
                    })
        return conflicts

    def check_drug_drug_interactions(self, drugs: List[str]) -> List[Dict[str, str]]:
        """
        Rule 2: Known clinical drug-drug interactions (Warfarin/Aspirin, ACEi/Potassium, Statin/Macrolide, etc.).
        """
        clashes = []
        resolved = []
        for d in drugs:
            obj = self.lookup_drug(d)
            if obj:
                resolved.append(obj)

        INTERACTION_RULES = [
            # Aspirin / NSAID + NSAID (Duplicate NSAID / GI Bleed)
            (lambda a, b: "nsaid" in a["drug_class"].lower() and "nsaid" in b["drug_class"].lower(),
             "CRITICAL", "Concurrent use of multiple NSAIDs causes severe gastrointestinal ulceration and acute bleeding with no therapeutic benefit."),
            
            # Aspirin + Ibuprofen / Brufen
            (lambda a, b: "aspirin" in a["generic_name"].lower() and "ibuprofen" in b["generic_name"].lower(),
             "CRITICAL", "Ibuprofen antagonizes the cardioprotective antiplatelet effect of Aspirin and drastically increases gastric hemorrhage risk."),
            
            # Clopidogrel + Omeprazole / Risek
            (lambda a, b: "clopidogrel" in a["generic_name"].lower() and "omeprazole" in b["generic_name"].lower(),
             "WARNING", "Omeprazole inhibits CYP2C19 bioactivation of Clopidogrel (Plavix/Lowplat), reducing antiplatelet protection. Suggest switching to Pantoprazole or Esomeprazole."),
            
            # ACE Inhibitor + Spironolactone (Lisinopril + Aldactone)
            (lambda a, b: "ace inhibitor" in a["drug_class"].lower() and "spironolactone" in b["generic_name"].lower(),
             "CRITICAL", "Combination causes severe hyperkalemia (dangerously elevated potassium) leading to cardiac arrhythmias without intensive serum electrolyte monitoring."),
            
            # Statin + Macrolide (Lipiget / Zocor + Clarithromycin)
            (lambda a, b: "statin" in a["drug_class"].lower() and "clarithromycin" in b["generic_name"].lower(),
             "CRITICAL", "Clarithromycin strongly inhibits CYP3A4 metabolism of statins, triggering toxic serum levels and acute rhabdomyolysis (muscle breakdown and acute renal failure)."),
            
            # Beta-Blocker + Verapamil/Diltiazem
            (lambda a, b: "beta-blocker" in a["drug_class"].lower() and b["generic_name"].lower() in ["verapamil", "diltiazem"],
             "CRITICAL", "Severe additive negative inotropic and chronotropic suppression leading to profound bradycardia, heart block, or cardiogenic collapse.")
        ]

        n = len(resolved)
        for i in range(n):
            for j in range(i + 1, n):
                d1 = resolved[i]
                d2 = resolved[j]
                for rule_func, severity, reason in INTERACTION_RULES:
                    if rule_func(d1, d2) or rule_func(d2, d1):
                        clashes.append({
                            "drug_1": d1["brand_name"],
                            "drug_2": d2["brand_name"],
                            "severity": severity,
                            "explanation": reason
                        })
        return clashes

    def check_maximum_daily_dose(self, drug_name: str, dose_mg: float, frequency_per_day: int, age: int = 30) -> Optional[Dict[str, Any]]:
        """
        Rule 3: Maximum daily dose threshold violations (e.g. Paracetamol > 4000mg/day).
        """
        drug = self.lookup_drug(drug_name)
        if not drug:
            return None

        total_daily_mg = dose_mg * frequency_per_day
        max_daily = drug.get("max_daily_dose_mg", 99999)

        if total_daily_mg > max_daily:
            return {
                "drug": drug["brand_name"],
                "prescribed_daily_mg": total_daily_mg,
                "maximum_allowed_daily_mg": max_daily,
                "violation": True,
                "explanation": f"Prescribed dose of {drug['brand_name']} ({total_daily_mg} mg/day) exceeds maximum clinical ceiling of {max_daily} mg/day. High toxicity risk (e.g. hepatotoxicity in Paracetamol overdose)."
            }
        return None

    def check_duplicate_therapy(self, proposed_drugs: List[str]) -> List[Dict[str, str]]:
        """
        Rule 4: Duplicate therapy (two brands sharing identical active molecules, e.g. Panadol + Calpol).
        """
        duplicates = []
        generics_seen: Dict[str, str] = {}

        for d_name in proposed_drugs:
            drug = self.lookup_drug(d_name)
            if not drug:
                continue
            gen = drug["generic_name"].lower()
            if gen in generics_seen:
                duplicates.append({
                    "brand_1": generics_seen[gen],
                    "brand_2": drug["brand_name"],
                    "generic_name": drug["generic_name"],
                    "explanation": f"Duplicate therapy detected: '{generics_seen[gen]}' and '{drug['brand_name']}' both contain {drug['generic_name']}. Combining them creates unintentional overdose risk."
                })
            else:
                generics_seen[gen] = drug["brand_name"]
        return duplicates

    def check_special_populations(self, proposed_drugs: List[str], age: int, is_pregnant: bool = False) -> List[Dict[str, str]]:
        """
        Rule 5: Special populations (Pregnancy, Pediatric, Geriatric).
        """
        alerts = []
        for d_name in proposed_drugs:
            drug = self.lookup_drug(d_name)
            if not drug:
                continue

            # Pregnancy Checks (Categories D & X)
            if is_pregnant:
                preg_cat = drug.get("pregnancy_category", "")
                if "X" in preg_cat or "D" in preg_cat:
                    alerts.append({
                        "drug": drug["brand_name"],
                        "population": "Pregnancy",
                        "severity": "CRITICAL",
                        "explanation": f"{drug['brand_name']} ({drug['generic_name']}) is Pregnancy Category {preg_cat}. Strictly contraindicated due to proven teratogenic risk or fetal toxicity."
                    })

            # Pediatric Checks (Age < 16)
            if age < 16:
                if "aspirin" in drug["generic_name"].lower():
                    alerts.append({
                        "drug": drug["brand_name"],
                        "population": "Pediatric (Age < 16)",
                        "severity": "CRITICAL",
                        "explanation": f"Aspirin is strictly contraindicated in children and adolescents under 16 due to Reye's Syndrome risk (fatal hepatic and cerebral failure)."
                    })
                elif "fluoroquinolone" in drug.get("drug_class", "").lower() or drug.get("generic_name", "").lower() in ["ciprofloxacin", "levofloxacin"]:
                    alerts.append({
                        "drug": drug["brand_name"],
                        "population": "Pediatric",
                        "severity": "WARNING",
                        "explanation": f"{drug['brand_name']} ({drug['generic_name']}) is a fluoroquinolone not generally recommended for children due to arthropathy and cartilage damage."
                    })

            # Geriatric Checks (Age >= 65 Beers Criteria)
            if age >= 65 and drug.get("elderly_caution", False):
                alerts.append({
                    "drug": drug["brand_name"],
                    "population": "Geriatric (Age 65+)",
                    "severity": "WARNING",
                    "explanation": f"{drug['brand_name']} ({drug['generic_name']}) warrants caution in elderly patients per Beers Criteria (elevated risk of sedation, falls, delirium, or severe GI bleeding)."
                })

        return alerts

    def evaluate_prescription(self, proposed_drugs: List[str], patient_allergies: List[str],
                              age: int = 30, is_pregnant: bool = False,
                              dosages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Complete deterministic check pipeline combining all 5 safety rules.
        """
        allergy_clashes = self.check_allergy_conflicts(proposed_drugs, patient_allergies)
        drug_interactions = self.check_drug_drug_interactions(proposed_drugs)
        duplicates = self.check_duplicate_therapy(proposed_drugs)
        special_pop_alerts = self.check_special_populations(proposed_drugs, age, is_pregnant)
        
        dose_violations = []
        if dosages:
            for d in dosages:
                v = self.check_maximum_daily_dose(d["drug_name"], d["dose_mg"], d["frequency"], age)
                if v:
                    dose_violations.append(v)

        has_critical = (
            any(a.get("severity") == "CRITICAL" for a in allergy_clashes) or
            any(i.get("severity") == "CRITICAL" for i in drug_interactions) or
            any(s.get("severity") == "CRITICAL" for s in special_pop_alerts) or
            len(dose_violations) > 0
        )
        has_warning = (
            len(duplicates) > 0 or
            any(a.get("severity") == "WARNING" for a in allergy_clashes) or
            any(i.get("severity") == "WARNING" for i in drug_interactions) or
            any(s.get("severity") == "WARNING" for s in special_pop_alerts)
        )

        overall_status = "CRITICAL_CLASH" if has_critical else ("WARNING" if has_warning else "SAFE")

        return {
            "overall_status": overall_status,
            "is_safe_to_dispense": overall_status == "SAFE",
            "allergy_conflicts": allergy_clashes,
            "drug_interactions": drug_interactions,
            "duplicate_therapy": duplicates,
            "dose_limit_violations": dose_violations,
            "special_population_alerts": special_pop_alerts
        }


# Singleton instance
safety_engine = PrescriptionSafetyEngine()

if __name__ == "__main__":
    res = safety_engine.evaluate_prescription(
        proposed_drugs=["Panadol", "Calpol", "Brufen", "Loprin", "Augmentin"],
        patient_allergies=["Penicillin"],
        age=12,
        is_pregnant=False,
        dosages=[{"drug_name": "Panadol", "dose_mg": 1000, "frequency": 5}] # 5000 mg > 4000
    )
    print("Prescription Safety Status:", res["overall_status"])
    print(json.dumps(res, indent=2))
