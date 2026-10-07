"""
MCP Server: Drug Database & Clinical Safety
Exposes standardized MCP tools for Pakistani pharmaceutical lookup,
drug-drug interaction verification, dosage ceiling checks, and contraindication screening.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
from prescription_safety_engine import safety_engine
from mcp.server.mcpserver import MCPServer

server = MCPServer("drug-database")

@server.tool()
def lookup_drug(query: str) -> Dict[str, Any]:
    """
    Looks up pharmaceutical monograph details by Pakistani brand or generic name.
    Examples: Panadol, Brufen, Augmentin, Lipiget, Concor, Glucophage.
    """
    drug = safety_engine.lookup_drug(query)
    if not drug:
        return {"found": False, "error": f"Medicine '{query}' not found in the Pakistani drug formulary."}
    return {
        "found": True,
        "brand_name": drug["brand_name"],
        "generic_name": drug["generic_name"],
        "drug_class": drug["drug_class"],
        "common_dosage_mg": drug["common_dosage_mg"],
        "max_daily_dose_mg": drug["max_daily_dose_mg"],
        "pregnancy_category": drug["pregnancy_category"],
        "elderly_caution": drug.get("elderly_caution", False),
        "contraindications": drug.get("contraindications", []),
        "allergy_group": drug.get("allergy_group", "")
    }

@server.tool()
def check_drug_interactions(drugs: List[str]) -> List[Dict[str, str]]:
    """
    Checks pairwise clinical interactions among a list of proposed medicines.
    Returns list of interaction alerts with clinical rationale and severity.
    """
    return safety_engine.check_drug_drug_interactions(drugs)

@server.tool()
def check_dosage_limit(drug_name: str, dose_mg: float, frequency_per_day: int, age: int = 30) -> Dict[str, Any]:
    """
    Validates whether proposed single dose and frequency violate the 24-hour maximum clinical limit.
    """
    violation = safety_engine.check_maximum_daily_dose(drug_name, dose_mg, frequency_per_day, age)
    if violation:
        return {"is_safe": False, "details": violation}
    return {"is_safe": True, "message": f"Dose {dose_mg}mg x {frequency_per_day}/day is within clinical ceiling."}

@server.tool()
def check_contraindications(drug_name: str, condition: str, is_pregnant: bool = False, age: int = 30) -> Dict[str, Any]:
    """
    Screens a medicine against patient chronic conditions, pregnancy status, and age group.
    """
    drug = safety_engine.lookup_drug(drug_name)
    if not drug:
        return {"found": False, "error": f"Drug '{drug_name}' not found."}

    contraindications = drug.get("contraindications", [])
    matched = [c for c in contraindications if condition.lower() in c.lower()]

    special_alerts = safety_engine.check_special_populations([drug_name], age=age, is_pregnant=is_pregnant)

    return {
        "drug": drug["brand_name"],
        "condition_conflicts": matched,
        "special_population_alerts": special_alerts,
        "is_safe": len(matched) == 0 and not any(a["severity"] == "CRITICAL" for a in special_alerts)
    }

@server.tool()
def evaluate_full_prescription(proposed_drugs: List[str], patient_allergies: List[str],
                               age: int = 30, is_pregnant: bool = False) -> Dict[str, Any]:
    """
    Executes complete multi-rule prescription check (Allergies + Interactions + Duplicates + Special Populations).
    """
    return safety_engine.evaluate_prescription(
        proposed_drugs=proposed_drugs,
        patient_allergies=patient_allergies,
        age=age,
        is_pregnant=is_pregnant
    )

if __name__ == "__main__":
    import asyncio
    async def demo():
        tools = await server.list_tools()
        print(f"MCP Server '{server.name}' started. Registered tools: {[t.name for t in tools]}")
    asyncio.run(demo())
