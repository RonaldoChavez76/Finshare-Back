"""
SimulationService – Módulo de Simulación de Escenarios Financieros.

Crea y ejecuta simulaciones sobre el perfil financiero del usuario
o sobre un grupo, proyectando el impacto en riesgo y estabilidad.
Los resultados se persisten en la colección 'simulations'.
"""
from datetime import datetime, timezone
from bson import ObjectId
from app.config.database import get_db
from app.models.simulation_model import build_simulation, build_simulation_result
from app.services.risk_service import RiskService


class SimulationService:

    # ── Crear y ejecutar simulación ───────────────────────────────────────────
    @staticmethod
    def run(user_id: str, data: dict, persist: bool = True) -> dict:
        """
        Calcula una simulación. Si persist=True, la guarda en la BD.
        """
        db = get_db()
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("Usuario no encontrado.")

        scenario_type  = data["scenarioType"]
        parameters     = data.get("parameters", {})
        description    = data.get("description", "")
        target_group_id= ObjectId(data["targetGroupId"]) if data.get("targetGroupId") else None

        # Validar que el grupo existe si se proporcionó
        if target_group_id:
            group = db.groups.find_one({"_id": target_group_id, "isActive": True})
            if not group:
                raise ValueError("Grupo no encontrado o inactivo.")
        else:
            group = None

        # Construir documento base
        sim_doc = build_simulation(
            created_by    = ObjectId(user_id),
            scenario_type = scenario_type,
            parameters    = parameters,
            description   = description,
            target_group_id = target_group_id,
        )

        # Obtener riesgo actual ANTES de simular (como baseline)
        finance = user.get("finance") or {}
        debts   = [d for d in (user.get("debts") or []) if d.get("isActive", True)]

        current_risk = _compute_current_risk(finance, debts)

        # Ejecutar motor de escenario
        result = _run_scenario(
            scenario_type = scenario_type,
            parameters    = parameters,
            finance       = finance,
            debts         = debts,
            group         = group,
            current_risk  = current_risk,
        )

        sim_doc["result"] = result
        if not persist:
            # Para vista previa, eliminamos IDs de objetos para serialización limpia
            sim_doc["_id"] = str(sim_doc["_id"])
            sim_doc["createdBy"] = str(sim_doc["createdBy"])
            if sim_doc.get("targetGroupId"):
                sim_doc["targetGroupId"] = str(sim_doc["targetGroupId"])
            return sim_doc

        # Persistir
        db.simulations.insert_one(sim_doc)
        # Convertir a string para retorno consistente
        sim_doc["_id"] = str(sim_doc["_id"])
        sim_doc["createdBy"] = str(sim_doc["createdBy"])
        if sim_doc.get("targetGroupId"):
            sim_doc["targetGroupId"] = str(sim_doc["targetGroupId"])
        return sim_doc

    # ── Consultas ─────────────────────────────────────────────────────────────
    @staticmethod
    def list_by_user(user_id: str, page: int = 1, per_page: int = 20) -> dict:
        db = get_db()
        query = {"createdBy": ObjectId(user_id)}
        total = db.simulations.count_documents(query)
        items = list(
            db.simulations.find(query)
            .sort("createdAt", -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        return {"items": items, "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def get(simulation_id: str, user_id: str) -> dict:
        db = get_db()
        sim = db.simulations.find_one({"_id": ObjectId(simulation_id)})
        if not sim:
            raise ValueError("Simulación no encontrada.")
        if str(sim["createdBy"]) != user_id:
            raise PermissionError("No tienes permiso para ver esta simulación.")
        return sim

    @staticmethod
    def delete(simulation_id: str, user_id: str) -> bool:
        db = get_db()
        sim = db.simulations.find_one({"_id": ObjectId(simulation_id)})
        if not sim:
            raise ValueError("Simulación no encontrada.")
        if str(sim["createdBy"]) != user_id:
            raise PermissionError("No tienes permiso para eliminar esta simulación.")
        db.simulations.delete_one({"_id": ObjectId(simulation_id)})
        return True


# ─── Motor de escenarios (funciones privadas) ──────────────────────────────────

def _compute_current_risk(finance: dict, debts: list) -> dict:
    """Calcula métricas de riesgo base sin tocar la BD."""
    monthly_income    = float(finance.get("monthlyIncome",    0))
    fixed_expenses    = float(finance.get("fixedExpenses",    0))
    variable_expenses = float(finance.get("variableExpenses", 0))
    savings           = float(finance.get("savings",          0))
    total_debt_payment= sum(float(d.get("monthlyPayment", 0)) for d in debts)

    debt_index    = RiskService._calc_debt_index(monthly_income, total_debt_payment)
    savings_cap   = RiskService._calc_savings_capacity(
                        monthly_income, fixed_expenses, variable_expenses, total_debt_payment)
    emergency     = RiskService._calc_emergency_fund(savings, fixed_expenses)
    risk_score    = RiskService._calc_risk_score(debt_index, savings_cap, emergency)

    return {
        "monthly_income":    monthly_income,
        "fixed_expenses":    fixed_expenses,
        "variable_expenses": variable_expenses,
        "savings":           savings,
        "total_debt":        total_debt_payment,
        "debt_index":        debt_index,
        "savings_cap":       savings_cap,
        "emergency":         emergency,
        "risk_score":        risk_score,
    }


def _run_scenario(
    scenario_type: str,
    parameters: dict,
    finance: dict,
    debts: list,
    group: dict,
    current_risk: dict,
) -> dict:
    """Despacha al motor correcto según el tipo de escenario."""
    handlers = {
        "job_loss":       _scenario_job_loss,
        "income_cut":     _scenario_income_cut,
        "rent_increase":  _scenario_rent_increase,
        "expense_spike":  _scenario_expense_spike,
        "member_default": _scenario_member_default,
    }
    handler = handlers.get(scenario_type)
    if not handler:
        raise ValueError(f"scenarioType '{scenario_type}' no soportado.")
    return handler(parameters, finance, debts, group, current_risk)


def _after_risk(new_income, new_fixed, new_variable, debts, savings, baseline):
    """Recalcula riesgo con valores modificados y retorna deltas."""
    total_debt = sum(float(d.get("monthlyPayment", 0)) for d in debts)
    di  = RiskService._calc_debt_index(new_income, total_debt)
    sc  = RiskService._calc_savings_capacity(new_income, new_fixed, new_variable, total_debt)
    ef  = RiskService._calc_emergency_fund(savings, new_fixed)
    rs  = RiskService._calc_risk_score(di, sc, ef)
    return {
        "risk_delta":       round(rs - baseline["risk_score"], 4),
        "stability_delta":  round(sc - baseline["savings_cap"], 4),
        "new_risk_score":   round(rs, 2),
        "new_savings_cap":  round(sc, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Handlers por escenario
# ─────────────────────────────────────────────────────────────────────────────

def _scenario_job_loss(parameters, finance, debts, group, baseline):
    """Simula pérdida total de ingresos."""
    new_income = 0.0
    r = _after_risk(new_income, baseline["fixed_expenses"],
                    baseline["variable_expenses"], debts, baseline["savings"], baseline)

    recommendation = (
        "Pérdida total de ingresos. Tu fondo de emergencia cubriría "
        f"{baseline['emergency']:.1f} mes(es). "
        "Se recomienda activar el fondo de emergencia, suspender gastos variables "
        "y renegociar deudas de inmediato."
    )
    return build_simulation_result(
        risk_delta           = r["risk_delta"],
        stability_delta      = r["stability_delta"],
        conflict_probability = _group_conflict_prob(group, 0.85),
        affected_members     = _all_member_ids(group),
        recommendation       = recommendation,
    )


def _scenario_income_cut(parameters, finance, debts, group, baseline):
    """Simula reducción porcentual de ingresos (parámetro: cut_percent 0-1)."""
    cut_pct    = float(parameters.get("cut_percent", 0.30))
    new_income = baseline["monthly_income"] * (1 - cut_pct)
    r = _after_risk(new_income, baseline["fixed_expenses"],
                    baseline["variable_expenses"], debts, baseline["savings"], baseline)

    pct_label = f"{cut_pct*100:.0f}%"
    recommendation = (
        f"Reducción del {pct_label} de ingresos. "
        f"Capacidad de ahorro proyectada: {r['new_savings_cap']*100:.1f}%. "
        "Considera reducir gastos variables y posponer compromisos financieros opcionales."
    )
    return build_simulation_result(
        risk_delta           = r["risk_delta"],
        stability_delta      = r["stability_delta"],
        conflict_probability = _group_conflict_prob(group, cut_pct * 0.6),
        affected_members     = _all_member_ids(group),
        recommendation       = recommendation,
    )


def _scenario_rent_increase(parameters, finance, debts, group, baseline):
    """Simula aumento en gastos fijos (parámetro: increase_amount o increase_percent)."""
    if "increase_amount" in parameters:
        added = float(parameters["increase_amount"])
    else:
        pct   = float(parameters.get("increase_percent", 0.15))
        added = baseline["fixed_expenses"] * pct

    new_fixed = baseline["fixed_expenses"] + added
    r = _after_risk(baseline["monthly_income"], new_fixed,
                    baseline["variable_expenses"], debts, baseline["savings"], baseline)

    recommendation = (
        f" Aumento de ${added:,.2f} en gastos fijos. "
        f"Nuevo risk score estimado: {r['new_risk_score']:.1f}/100. "
        "Evalúa renegociar el contrato o buscar un ingreso complementario."
    )
    return build_simulation_result(
        risk_delta           = r["risk_delta"],
        stability_delta      = r["stability_delta"],
        conflict_probability = _group_conflict_prob(group, 0.40),
        affected_members     = _all_member_ids(group),
        recommendation       = recommendation,
    )


def _scenario_expense_spike(parameters, finance, debts, group, baseline):
    """Simula un pico puntual de gasto variable (parámetro: spike_amount)."""
    spike = float(parameters.get("spike_amount", baseline["variable_expenses"] * 0.50))
    new_variable = baseline["variable_expenses"] + spike
    r = _after_risk(baseline["monthly_income"], baseline["fixed_expenses"],
                    new_variable, debts, baseline["savings"], baseline)

    recommendation = (
        f"Gasto extraordinario de ${spike:,.2f}. "
        "Utiliza el fondo de emergencia si está disponible. "
        "Reduce gastos variables en los próximos 2 meses para recuperar estabilidad."
    )
    return build_simulation_result(
        risk_delta           = r["risk_delta"],
        stability_delta      = r["stability_delta"],
        conflict_probability = _group_conflict_prob(group, 0.30),
        affected_members     = _all_member_ids(group),
        recommendation       = recommendation,
    )


def _scenario_member_default(parameters, finance, debts, group, baseline):
    """
    Simula que un miembro del grupo deja de pagar su parte.
    Requiere: targetGroupId y parámetro defaulting_member_id.
    """
    if group is None:
        raise ValueError("Este escenario requiere un grupo (targetGroupId).")

    members = [m for m in group.get("members", []) if m.get("isActive")]
    n_members = len(members) or 1

    # Monto promedio que absorbe el grupo
    db = get_db()
    pipeline = [
        {"$match": {"groupId": group["_id"], "status": {"$in": ["pending", "partial"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$totalAmount"}}},
    ]
    agg = list(db.shared_expenses.aggregate(pipeline))
    pending_total = float(agg[0]["total"]) if agg else 0.0
    extra_per_member = pending_total / n_members if n_members > 1 else pending_total

    # Estimación de conflicto según monto extra absorbido
    conflict_prob = min(0.30 + (extra_per_member / max(baseline["monthly_income"], 1)) * 2, 0.95)

    recommendation = (
        f"Un miembro podría no cubrir su parte (${extra_per_member:,.2f} pendiente por integrante). "
        f"Probabilidad de conflicto estimada: {conflict_prob*100:.0f}%. "
        "Se recomienda un acuerdo previo de garantía o un fondo grupal de contingencia."
    )

    defaulting_id = parameters.get("defaulting_member_id")
    affected = ([ObjectId(defaulting_id)] if defaulting_id else _all_member_ids(group))

    return build_simulation_result(
        risk_delta           = round(conflict_prob * 20, 4),
        stability_delta      = round(-extra_per_member / max(baseline["monthly_income"], 1), 4),
        conflict_probability = round(conflict_prob, 4),
        affected_members     = affected,
        recommendation       = recommendation,
    )


# ─── Utilidades internas ───────────────────────────────────────────────────────

def _group_conflict_prob(group, base_prob: float) -> float:
    """Ajusta la probabilidad de conflicto según el número de miembros activos."""
    if not group:
        return 0.0
    n = len([m for m in group.get("members", []) if m.get("isActive")])
    # Más miembros → menor probabilidad porque el riesgo se distribuye
    factor = max(0.5, 1.0 - (n - 1) * 0.05)
    return round(min(base_prob * factor, 0.99), 4)


def _all_member_ids(group) -> list:
    if not group:
        return []
    return [m["userId"] for m in group.get("members", []) if m.get("isActive")]
