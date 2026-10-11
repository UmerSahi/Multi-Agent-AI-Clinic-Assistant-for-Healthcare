"""
Lab Report Vision & Multimodal Extraction Pipeline (Week 9 - Day 5)
Handles:
1. Multi-format ingestion: PDF documents (digital & scanned) and lab report images (PNG, JPG, WEBP).
2. Vision LLM extraction via Gemini (gemini-3.5-flash-lite) + native PDF text parsing (pypdf/pymupdf).
3. Deterministic clinical parameter extraction into strict JSON (test name, value, unit, reference range).
4. Deterministic clinical flag engine (NORMAL, LOW, HIGH, CRITICAL_LOW, CRITICAL_HIGH).
5. Empathetic, simple UrduLish explanations strictly adhering to non-diagnostic safety guardrails.
"""

import os
import re
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import io
import dotenv
from PIL import Image

# Load environment
dotenv.load_dotenv()
DAY5_DIR = Path(__file__).resolve().parent
ROOT_DIR = DAY5_DIR.parent

# Try imports
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None

try:
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
except Exception:
    genai = None


class LabVisionExtractor:
    """End-to-end multimodal pipeline for clinical lab reports."""

    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        self.model_name = os.getenv("GEMINI_MODEL", model_name)
        if "2.5-flash" in self.model_name:
            self.model_name = "gemini-3.5-flash-lite"
        self._init_model()

    def _init_model(self):
        self.model = None
        if genai and os.getenv("GEMINI_API_KEY"):
            try:
                self.model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                print(f"[LabVisionExtractor Model Init Warning]: {e}")

    def extract_from_file(self, file_bytes_or_path: Union[str, Path, bytes], filename: str = "") -> Dict[str, Any]:
        """
        Dispatches extraction based on file extension (PDF vs Image).
        Supports file path or raw bytes in memory.
        """
        filename_lower = filename.lower()
        if isinstance(file_bytes_or_path, (str, Path)):
            path = Path(file_bytes_or_path)
            filename_lower = path.name.lower()
            with open(path, "rb") as f:
                data = f.read()
        else:
            data = file_bytes_or_path

        if filename_lower.endswith(".pdf"):
            return self.extract_from_pdf(data, filename)
        elif any(filename_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            return self.extract_from_image(data, filename)
        elif filename_lower.endswith(".txt"):
            text = data.decode("utf-8", errors="ignore")
            return self.extract_from_text(text)
        else:
            # Fallback: try PDF first, then image
            try:
                return self.extract_from_pdf(data, filename)
            except Exception:
                return self.extract_from_image(data, filename)

    def extract_from_pdf(self, pdf_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        """
        Extracts lab data from PDF. First checks for digital text.
        If digital text is present and structured, parses deterministically.
        If scanned/sparse, renders first page to PNG and processes via Vision LLM.
        """
        text = ""
        # 1. Try PyMuPDF text extraction
        if fitz:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page in doc:
                    text += page.get_text() + "\n"
            except Exception as e:
                print(f"[PyMuPDF Text Extract Note]: {e}")

        # 2. Try pypdf text extraction fallback
        if not text.strip() and pypdf:
            try:
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            except Exception as e:
                print(f"[pypdf Extract Note]: {e}")

        # If clean tabular text found, use deterministic high-precision regex parser
        if len(text.strip()) > 80 and ("INVESTIGATION" in text or "Reference Range" in text or "mg/dL" in text or "STATUS" in text):
            parsed = self.extract_from_text(text)
            if parsed.get("tests"):
                return parsed

        # Otherwise render page 1 to image and use Vision LLM
        if fitz:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                if len(doc) > 0:
                    page = doc[0]
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    return self.extract_from_image(img_bytes, filename=f"{filename}.png")
            except Exception as e:
                print(f"[PDF-to-Image Rendering Note]: {e}")

        # Fallback to text parsing
        return self.extract_from_text(text)

    def extract_from_image(self, image_bytes: bytes, filename: str = "") -> Dict[str, Any]:
        """
        Processes lab report image using Gemini Vision (gemini-3.5-flash-lite).
        Prompt instructs strict JSON output with all tabular test parameters.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to decode image: {e}",
                "tests": []
            }

        prompt = """
You are an expert Clinical Laboratory Document Information Extraction engine.
Analyze this medical laboratory report image and extract all test results into valid JSON only.

STRICT JSON OUTPUT FORMAT (Return ONLY raw JSON, without markdown formatting or backticks):
{
  "report_id": "string (e.g. RPT-2026-101)",
  "patient_name": "string (e.g. Ahmed Raza)",
  "mrn": "string (e.g. CCC-PK-100001)",
  "collection_date": "string (YYYY-MM-DD or as shown)",
  "panel": "string (e.g. Complete Blood Count (CBC), Liver Function Test (LFT), Lipid Profile, etc.)",
  "tests": [
    {
      "test_name": "string (e.g. Hemoglobin, ALT, Serum Creatinine)",
      "numeric_value": float (numeric value, e.g. 14.5),
      "unit": "string (e.g. g/dL, U/L, mg/dL)",
      "reference_range_low": float (lower limit, e.g. 13.0),
      "reference_range_high": float (upper limit, e.g. 17.0),
      "reference_range_str": "string (e.g. 13.0 - 17.0)"
    }
  ]
}

Rules:
1. Extract ALL test rows visible in the table.
2. Numeric values must be parsed as numbers (float). If not available, set reference_range_low/high to null.
3. Do not invent data. Extract exactly what is printed.
"""

        if self.model:
            try:
                response = self.model.generate_content([prompt, image])
                raw_out = response.text.strip()
                # Clean markdown fencing if model included it
                if raw_out.startswith("```"):
                    raw_out = re.sub(r"^```(?:json)?\s*", "", raw_out)
                    raw_out = re.sub(r"\s*```$", "", raw_out)
                
                data = json.loads(raw_out)
                header = {
                    "report_id": data.get("report_id", "UNKNOWN"),
                    "patient_name": data.get("patient_name", "Valued Patient"),
                    "mrn": data.get("mrn", "UNKNOWN"),
                    "collection_date": data.get("collection_date", "Unknown"),
                    "panel": data.get("panel", "Clinical Laboratory Report")
                }
                tests = data.get("tests", [])
                
                # Apply deterministic flag calculations
                tests = self.evaluate_flags(tests)
                urdulish_summary = self.generate_urdulish_summary(header, tests)

                return {
                    "success": True,
                    "report_id": header["report_id"],
                    "patient_name": header["patient_name"],
                    "mrn": header["mrn"],
                    "collection_date": header["collection_date"],
                    "panel": header["panel"],
                    "tests": tests,
                    "abnormal_count": sum(1 for t in tests if t.get("flag") != "NORMAL"),
                    "urdulish_summary": urdulish_summary,
                    "extraction_method": "Gemini Vision Multimodal LLM"
                }
            except Exception as e:
                print(f"[Vision LLM Processing Note]: {e}. Falling back to OCR/heuristic.")

        return {
            "success": False,
            "error": "Vision LLM extraction was unable to parse the report image.",
            "tests": []
        }

    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        High-precision deterministic extraction for digital text & structured clinic reports.
        """
        header = self._extract_header(text)
        tests = self._extract_test_rows(text)
        tests = self.evaluate_flags(tests)
        urdulish_summary = self.generate_urdulish_summary(header, tests)

        return {
            "success": True,
            "report_id": header.get("report_id", "UNKNOWN"),
            "patient_name": header.get("patient_name", "Valued Patient"),
            "mrn": header.get("mrn", "UNKNOWN"),
            "collection_date": header.get("date", "Unknown"),
            "panel": header.get("panel", "Clinical Lab Report"),
            "tests": tests,
            "abnormal_count": sum(1 for t in tests if t.get("flag") != "NORMAL"),
            "urdulish_summary": urdulish_summary,
            "extraction_method": "Deterministic Clinical Regex Parser"
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
        m_panel = re.search(r"Panel Type:\s*([A-Za-z0-9\_\-\s]+)", text)
        if m_panel:
            header["panel"] = m_panel.group(1).strip()
        return header

    def _extract_test_rows(self, text: str) -> List[Dict[str, Any]]:
        tests = []
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # 1. Single-line row parser (standard clinic printout & txt format)
        in_table = False
        for line_str in lines:
            if "INVESTIGATION" in line_str and ("STATUS" in line_str or "RANGE" in line_str):
                in_table = True
                continue
            if in_table and line_str.startswith("---") and tests:
                break
            if in_table and not line_str.startswith("---") and line_str:
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
                        "reference_range_str": f"{low} - {high}"
                    })

        if tests:
            return tests

        # 2. Multi-line sequential table cell parser (from PDF table layout streams)
        i = 0
        while i < len(lines):
            line = lines[i]
            m_range = re.match(r"^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$", line)
            if m_range:
                low = float(m_range.group(1))
                high = float(m_range.group(2))

                val = None
                unit = ""
                name = ""

                prev1 = lines[i - 1] if i >= 1 else ""
                prev2 = lines[i - 2] if i >= 2 else ""
                prev3 = lines[i - 3] if i >= 3 else ""

                if re.match(r"^\d+(?:\.\d+)?$", prev1):
                    val = float(prev1)
                    name = prev2
                elif re.match(r"^\d+(?:\.\d+)?$", prev2):
                    unit = prev1
                    val = float(prev2)
                    name = prev3

                if val is not None and name and "INVESTIGATION" not in name and "STATUS" not in name:
                    tests.append({
                        "test_name": name,
                        "numeric_value": val,
                        "unit": unit,
                        "reference_range_low": low,
                        "reference_range_high": high,
                        "reference_range_str": f"{low} - {high}"
                    })
            i += 1

        return tests

    def evaluate_flags(self, tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determines clinical flags: NORMAL, LOW, HIGH, CRITICAL_LOW, CRITICAL_HIGH.
        """
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
            else:
                t["flag"] = "NORMAL"

            if not t.get("reference_range_str") and low is not None and high is not None:
                t["reference_range_str"] = f"{low} - {high}"

        return tests

    def generate_urdulish_summary(self, header: Dict[str, str], tests: List[Dict[str, Any]]) -> str:
        """
        Produces empathetic, clear UrduLish explanation strictly adhering to safety rules:
        NEVER DIAGNOSE. Explains values and prompts doctor consultation.
        """
        name = header.get("patient_name", "Mohtaram Mariz")
        panel = header.get("panel", "Lab Report")

        abnormals = [t for t in tests if t.get("flag") != "NORMAL"]
        normals = [t for t in tests if t.get("flag") == "NORMAL"]

        msg = f"Assalam-o-Alaikum {name} Sahab/Sahiba,\n"
        msg += f"Aap ki **{panel}** ki lab report ka tajziya darj-zel hai:\n\n"

        if not abnormals:
            msg += "✅ **Tamam Parameters Normal Hain:**\n"
            msg += "Alhamdulillah, aap ke report mein shamil tamam test parameters standard reference range ke mutabiq normal hain.\n\n"
            for t in normals:
                msg += f"• **{t['test_name']}**: {t['numeric_value']} {t.get('unit', '')} *(Normal Hadd: {t.get('reference_range_str', '')})*\n"
            msg += "\n⚠️ **Zaroori Hidayat:**\n"
            msg += "Agar aap ko koi jismani takleef ya alamat mehsoos ho rahi hain toh apne muallij doctor se ruju zaroor karein."
        else:
            msg += f"Aap ki report mein **{len(normals)}** parameters normal hain aur **{len(abnormals)}** parameters normal hadd se mukhtalif hain:\n\n"
            msg += "🔍 **Mutasira Parameters (Outside Normal Range):**\n"
            for t in abnormals:
                flag = t.get("flag", "")
                if "HIGH" in flag:
                    status_urdu = "Normal hadd se zyada (High)"
                else:
                    status_urdu = "Normal hadd se kam (Low)"
                msg += f"• **{t['test_name']}**: `{t['numeric_value']} {t.get('unit', '')}` — **{status_urdu}** *(Normal: {t.get('reference_range_str', '')})*\n"

            if normals:
                msg += "\n✅ **Normal Parameters:**\n"
                for t in normals[:4]:  # Show top 4 normals to keep concise
                    msg += f"• {t['test_name']}: {t['numeric_value']} {t.get('unit', '')} (Normal)\n"
                if len(normals) > 4:
                    msg += f"• *(aur {len(normals) - 4} mazeed test parameters normal hain)*\n"

            msg += "\n🛡️ **Zaroori Clinical Safety Notice (Non-Diagnostic Disclaimer):**\n"
            msg += "Yeh AI assistant sirf lab values ki wazahat ke liye hai aur kisi bimari ki tashkhees (diagnosis) nahi karta. "
            msg += "Lab values mein tabdeeli aam jismani stress, khorak, ya deegar wajohat se bhi ho sakti hai. "
            msg += "Sahi tashkhees aur munasib ilaj ke liye baraye meharbani apne **muallij doctor** se ruju karein."

        return msg


# Global singleton instance
lab_vision_extractor = LabVisionExtractor()
lab_extractor = lab_vision_extractor
