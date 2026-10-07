"""
Lab Report Understanding & Extraction Pipeline
Parses lab report text, extracts structured test parameters into JSON,
evaluates out-of-range clinical flags, and produces safe, empathetic UrduLish summaries
WITHOUT diagnosing disease.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent

class LabReportExtractor:
    def __init__(self):
        pass

    def parse_report_text(self, text: str) -> Dict[str, Any]:
        """Extracts structured header and tabular test parameters from clinical report text."""
        header = self._extract_header(text)
        tests = self._extract_test_rows(text)
        
        # Evaluate flags deterministically
        for t in tests:
            val = t.get("numeric_value")
            low = t.get("reference_range_low")
            high = t.get("reference_range_high")
            if val is not None and low is not None and high is not None:
                if val > high:
                    t["flag"] = "CRITICAL_HIGH" if val > high * 2.0 else "HIGH"
                elif val < low:
                    t["flag"] = "CRITICAL_LOW" if val < low * 0.5 else "LOW"
                else:
                    t["flag"] = "NORMAL"

        urdulish_explanation = self.generate_urdulish_summary(header, tests)

        return {
            "report_id": header.get("report_id", "UNKNOWN"),
            "patient_name": header.get("patient_name", "Unknown Patient"),
            "mrn": header.get("mrn", "UNKNOWN"),
            "collection_date": header.get("date", "Unknown"),
            "panel": header.get("panel", "General"),
            "tests": tests,
            "abnormal_count": sum(1 for t in tests if t.get("flag") != "NORMAL"),
            "urdulish_summary": urdulish_explanation
        }

    def _extract_header(self, text: str) -> Dict[str, str]:
        header = {}
        m_id = re.search(r"Report Reference:\s*([A-Za-z0-9\-]+)", text)
        if m_id:
            header["report_id"] = m_id.group(1).strip()
        m_name = re.search(r"Patient Name:\s*([^\n\r]+)", text)
        if m_name:
            header["patient_name"] = m_name.group(1).strip()
        m_mrn = re.search(r"MRN / Patient ID:\s*([A-Za-z0-9\-]+)", text)
        if m_mrn:
            header["mrn"] = m_mrn.group(1).strip()
        m_date = re.search(r"Collection Date:\s*([^\n\r]+)", text)
        if m_date:
            header["date"] = m_date.group(1).strip()
        m_panel = re.search(r"Panel Type:\s*([A-Za-z0-9\_]+)", text)
        if m_panel:
            header["panel"] = m_panel.group(1).strip()
        return header

    def _extract_test_rows(self, text: str) -> List[Dict[str, Any]]:
        tests = []
        lines = text.splitlines()
        in_table = False

        for line in lines:
            line_str = line.strip()
            if "INVESTIGATION" in line_str and "STATUS" in line_str:
                in_table = True
                continue
            if in_table and line_str.startswith("---") and tests:
                break
            if in_table and not line_str.startswith("---") and line_str:
                # Match range at end: low - high [FLAG]
                # Example: Total Bilirubin                     0.11         mg/dL     0.2 - 1.2         [LOW]
                # Example: Urine Specific Gravity              1.018                  1.005 - 1.03      [NORMAL]
                m = re.search(
                    r"^(?P<name>.+?)\s+(?P<val>\d+(?:\.\d+)?)\s+(?:(?P<unit>[A-Za-z0-9/%/]+)\s+)?(?P<low>\d+(?:\.\d+)?)\s*-\s*(?P<high>\d+(?:\.\d+)?)\s*(?:\[(?P<flag>[A-Za-z_]+)\])?$",
                    line_str
                )
                if m:
                    name = m.group("name").strip()
                    val = float(m.group("val"))
                    unit = m.group("unit").strip() if m.group("unit") else ""
                    low = float(m.group("low"))
                    high = float(m.group("high"))
                    tests.append({
                        "test_name": name,
                        "numeric_value": val,
                        "unit": unit,
                        "reference_range_low": low,
                        "reference_range_high": high,
                        "flag": "NORMAL"
                    })
        return tests

    def generate_urdulish_summary(self, header: Dict[str, str], tests: List[Dict[str, Any]]) -> str:
        """
        Produces empathetic, clear UrduLish explanations strictly adhering to safety rules:
        NEVER DIAGNOSE. Explains values and prompts doctor consultation.
        """
        name = header.get("patient_name", "Mohtaram Mariz")
        panel = header.get("panel", "Lab Report")
        
        abnormals = [t for t in tests if t.get("flag") != "NORMAL"]
        normals = [t for t in tests if t.get("flag") == "NORMAL"]

        msg = f"Assalam o Alaikum {name} Sahab/Sahiba,\n"
        msg += f"Aap ki {panel} ki lab report ke nataij yeh hain:\n\n"

        if not abnormals:
            msg += "✅ Alhamdulillah, aap ke tamam test parameters normal range ke andar hain.\n"
            for t in normals:
                msg += f"• {t['test_name']}: {t['numeric_value']} {t['unit']} (Normal Range: {t['reference_range_low']} - {t['reference_range_high']})\n"
            msg += "\n⚠️ Zaroori Hidayat:\nPhir bhi agar tabiyat mein koi behtari mehsoos na ho rahi ho toh apne muallij doctor se ruju karein aur mashwara zaroor karein."
        else:
            msg += f"Report mein {len(normals)} parameters normal hain aur {len(abnormals)} parameters normal hadd se thora mukhtalif hain:\n\n"
            msg += "🔍 Mutasira Parameters (Outside Normal Range):\n"
            for t in abnormals:
                status_urdu = "Normal se zyada (High)" if "HIGH" in t['flag'] else "Normal se kam (Low)"
                msg += f"• {t['test_name']}: {t['numeric_value']} {t['unit']} — {status_urdu} (Normal Range: {t['reference_range_low']} - {t['reference_range_high']})\n"
            
            if normals:
                msg += "\n✅ Normal Parameters:\n"
                for t in normals:
                    msg += f"• {t['test_name']}: {t['numeric_value']} {t['unit']} (Normal)\n"

            msg += "\n⚠️ Zaroori Hidayat (Clinical Safety Notice):\n"
            msg += "Yeh AI assistant sirf lab ki values wazeh karne ke liye hai aur kisi bimari ki tashkhees (diagnosis) nahi kar sakta. "
            msg += "Values mein tabdeeli aam jismani stress ya mukhtalif wajohat se bhi ho sakti hai. "
            msg += "Sahi tashkhees aur munasib ilaj ke liye baraye meharbani apne muallij doctor se ruju karein."

        return msg


# Singleton instance
lab_extractor = LabReportExtractor()

if __name__ == "__main__":
    sample_file = BASE_DIR / "lab_reports" / "RPT-2026-101.txt"
    if sample_file.exists():
        with open(sample_file, "r", encoding="utf-8") as f:
            parsed = lab_extractor.parse_report_text(f.read())
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
