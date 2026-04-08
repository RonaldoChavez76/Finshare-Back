"""
Modelo para la colección 'simulations'.
Constructor alineado con el schema de MongoDB definido en setup_db.py.
"""
from datetime import datetime, timezone
from bson import ObjectId

VALID_SCENARIO_TYPES = {"job_loss", "rent_increase", "member_default", "expense_spike", "income_cut"}


def build_simulation(
    created_by: ObjectId,
    scenario_type: str,
    parameters: dict,
    description: str = "",
    target_group_id: ObjectId = None,
) -> dict:
    """
    Construye el documento base de una simulación (sin resultado aún).
    El campo 'result' se añade después de ejecutar el motor de cálculo.
    """
    if scenario_type not in VALID_SCENARIO_TYPES:
        raise ValueError(f"scenarioType inválido. Valores permitidos: {VALID_SCENARIO_TYPES}")

    now = datetime.now(timezone.utc)
    return {
        "_id": ObjectId(),
        "createdBy": created_by,
        "targetGroupId": target_group_id,
        "scenarioType": scenario_type,
        "description": description,
        "parameters": parameters or {},
        "createdAt": now,
        "updatedAt": now,
        # 'result' se añade tras ejecutar simulate()
    }


def build_simulation_result(
    risk_delta: float,
    stability_delta: float,
    conflict_probability: float,
    affected_members: list,
    recommendation: str,
) -> dict:
    """
    Construye el subdocumento 'result' que se embebe en la simulación.
    """
    return {
        "riskDelta": round(risk_delta, 4),
        "stabilityDelta": round(stability_delta, 4),
        "conflictProbability": round(conflict_probability, 4),
        "affectedMembers": affected_members,
        "recommendation": recommendation,
        "generatedAt": datetime.now(timezone.utc),
    }
