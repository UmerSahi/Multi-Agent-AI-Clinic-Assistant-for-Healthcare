"""
MCP Server: Patient Records
Exposes standardized MCP tools for accessing patient profiles, allergies,
active medications, past visit encounters, and diagnostic lab observations.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from db_client import db
from mcp.server.mcpserver import MCPServer

# Initialize MCP Server
server = MCPServer("patient-records")

@server.tool()
def get_patient_profile(identifier: str) -> Dict[str, Any]:
    """
    Retrieves demographic and baseline clinical data for a patient by Phone Number or MRN.
    Returns sanitized patient profile or error dictionary.
    """
    # Try finding by MRN
    p = db.find_patient_by_mrn(identifier)
    if not p:
        p = db.find_patient_by_phone(identifier)
    if not p:
        return {"found": False, "error": f"No patient record found matching identifier '{identifier}'"}

    # Audit log
    db.log_audit(
        actor_id="SYSTEM_AGENT",
        actor_role="SYSTEM_AGENT",
        action_type="GET_PATIENT_PROFILE",
        resource_accessed="patients",
        patient_id=p["id"],
        tool_name="get_patient_profile"
    )

    return {
        "found": True,
        "patient_id": p["id"],
        "mrn": p["mrn"],
        "full_name": p["full_name"],
        "gender": p["gender"],
        "date_of_birth": p["date_of_birth"],
        "city": p["city"],
        "known_allergies": p.get("known_allergies", []),
        "chronic_conditions": p.get("chronic_conditions", []),
        "current_medications": p.get("current_medications", [])
    }

@server.tool()
def get_patient_allergies(patient_id: str) -> List[str]:
    """
    Returns the verified list of drug and environmental allergies for a patient.
    """
    p = db.find_patient_by_id(patient_id)
    if not p:
        return []
    return p.get("known_allergies", [])

@server.tool()
def get_patient_medications(patient_id: str) -> List[Dict[str, Any]]:
    """
    Returns the active and recent medication requests / prescriptions for a patient.
    """
    meds = db.get_patient_medications(patient_id)
    return [
        {
            "drug_name": m["drug_name"],
            "generic_name": m["generic_name"],
            "dosage_mg": m["dosage_mg"],
            "frequency_per_day": m["frequency_per_day"],
            "duration_days": m["duration_days"],
            "instructions": m.get("instructions", ""),
            "safety_check_status": m.get("safety_check_status", "SAFE")
        }
        for m in meds
    ]

@server.tool()
def get_patient_history(patient_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches past clinical visit consultations, chief complaints, and SOAP notes.
    """
    encounters = db.get_patient_encounters(patient_id)
    return [
        {
            "encounter_id": e["id"],
            "date": e["encounter_date"],
            "doctor_name": e.get("doctor_name", "Attending Physician"),
            "doctor_specialty": e.get("doctor_specialty", "General Medicine"),
            "chief_complaint": e["chief_complaint"],
            "assessment": e.get("soap_assessment", ""),
            "plan": e.get("soap_plan", "")
        }
        for e in encounters[:limit]
    ]

@server.tool()
def get_patient_lab_results(patient_id: str, test_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Queries past lab observations and diagnostic tests (CBC, LFT, Lipid, HbA1c) for a patient.
    """
    obs = db.get_patient_observations(patient_id, test_code=test_code)
    return [
        {
            "test_code": o["test_code"],
            "test_name": o["test_name"],
            "numeric_value": o["numeric_value"],
            "unit": o["unit"],
            "reference_range": f"{o['reference_range_low']} - {o['reference_range_high']}",
            "flag": o["flag"],
            "date": o["issued_at"]
        }
        for o in obs
    ]

if __name__ == "__main__":
    import asyncio
    async def demo():
        tools = await server.list_tools()
        print(f"MCP Server '{server.name}' started. Registered tools: {[t.name for t in tools]}")
    asyncio.run(demo())
