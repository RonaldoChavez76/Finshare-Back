"""
RiskService – Módulo de Análisis de Estabilidad Financiera.

Calcula las métricas de riesgo personal del usuario y las persiste
en users.lastRiskReport. Todas las fórmulas operan sobre el subdocumento
'finance' y el array 'debts' del usuario, según el schema de finshare_db.
"""
from datetime import datetime, timezone
from bson import ObjectId
from app.config.database import get_db


# ─── Constantes de ponderación ────────────────────────────────────────────────
# Pesos que determinan la contribución de cada sub-indicador al risk_score (0-100).
_W_DEBT_INDEX   = 0.45   # Índice de deuda      → mayor peso
_W_SAVINGS_CAP  = 0.35   # Capacidad de ahorro
_W_EMERGENCY    = 0.20   # Fondo de emergencia


class RiskService:
    """Motor de cálculo de estabilidad financiera y nivel de riesgo."""

    # ── Método principal ──────────────────────────────────────────────────────
    @staticmethod
    def analyze(user_id: str) -> dict:
        """
        Obtiene el perfil del usuario, calcula las métricas de riesgo
        y persiste el reporte en users.lastRiskReport.

        Returns:
            dict con el reporte {debtIndex, savingsCapacity,
                                  emergencyFundMonths, riskScore, riskLevel}
        """
        db   = get_db()
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("Usuario no encontrado.")

        finance = user.get("finance") or {}
        debts   = [d for d in (user.get("debts") or []) if d.get("isActive", True)]

        # ── Valores base ──────────────────────────────────────────────────────
        monthly_income   = float(finance.get("monthlyIncome",    0))
        fixed_expenses   = float(finance.get("fixedExpenses",    0))
        variable_expenses= float(finance.get("variableExpenses", 0))
        savings          = float(finance.get("savings",          0))

        total_monthly_debt = sum(float(d.get("monthlyPayment", 0)) for d in debts)

        # ── Cálculo de métricas ───────────────────────────────────────────────
        debt_index           = RiskService._calc_debt_index(monthly_income, total_monthly_debt)
        savings_capacity     = RiskService._calc_savings_capacity(
                                    monthly_income, fixed_expenses,
                                    variable_expenses, total_monthly_debt)
        emergency_fund_months= RiskService._calc_emergency_fund(savings, fixed_expenses)
        risk_score           = RiskService._calc_risk_score(
                                    debt_index, savings_capacity, emergency_fund_months)
        risk_level           = RiskService._classify_risk(risk_score)

        report = {
            "debtIndex":           round(debt_index,            4),
            "savingsCapacity":     round(savings_capacity,      4),
            "emergencyFundMonths": round(emergency_fund_months, 2),
            "riskScore":           round(risk_score,            2),
            "riskLevel":           risk_level,
            "generatedAt":         datetime.now(timezone.utc),
        }

        # ── Persistir en users.lastRiskReport ─────────────────────────────────
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "lastRiskReport": report,
                "updatedAt":      datetime.now(timezone.utc),
            }},
        )

        return report

    @staticmethod
    def get_report(user_id: str) -> dict:
        """Retorna el último reporte de riesgo sin recalcular."""
        db   = get_db()
        user = db.users.find_one(
            {"_id": ObjectId(user_id)},
            {"lastRiskReport": 1, "finance": 1, "_id": 0},
        )
        if not user:
            raise ValueError("Usuario no encontrado.")
        if not user.get("lastRiskReport"):
            raise ValueError("Aún no se ha generado un análisis de riesgo. "
                             "Llama a POST /api/risk/analyze primero.")
        return user["lastRiskReport"]

    # ── Fórmulas / métricas ───────────────────────────────────────────────────
    @staticmethod
    def _calc_debt_index(monthly_income: float, total_monthly_debt: float) -> float:
        """
        Índice de Deuda = Σ(pagos_mensuales_deuda) / ingresos_mensuales
        Rango ideal: < 0.30 (30 % del ingreso destinado a deudas)
        """
        if monthly_income <= 0:
            return 1.0  # Sin ingresos declarados → máximo riesgo
        return min(total_monthly_debt / monthly_income, 1.0)

    @staticmethod
    def _calc_savings_capacity(
        monthly_income: float,
        fixed_expenses: float,
        variable_expenses: float,
        total_monthly_debt: float,
    ) -> float:
        """
        Capacidad de Ahorro = (ingresos - fijos - variables - deudas) / ingresos
        Rango ideal: > 0.20 (al menos 20 % de ahorro)
        Negativo significa déficit mensual.
        """
        if monthly_income <= 0:
            return -1.0
        disposable = monthly_income - fixed_expenses - variable_expenses - total_monthly_debt
        return max(disposable / monthly_income, -1.0)

    @staticmethod
    def _calc_emergency_fund(savings: float, fixed_expenses: float) -> float:
        """
        Meses de Fondo de Emergencia = ahorros / gastos_fijos
        Rango ideal: >= 3 meses
        """
        if fixed_expenses <= 0:
            return 6.0 if savings > 0 else 0.0   # Sin gastos fijos declarados
        return savings / fixed_expenses

    @staticmethod
    def _calc_risk_score(
        debt_index: float,
        savings_capacity: float,
        emergency_fund_months: float,
    ) -> float:
        """
        Risk Score (0–100) ponderado de los 3 indicadores.
        100 = riesgo máximo, 0 = sin riesgo.
        """
        # Normalizar cada indicador a riesgo 0-1
        debt_risk     = debt_index                                            # ya 0-1
        savings_risk  = max(0.0, -savings_capacity)                           # déficit → riesgo
        # emergencia: 0 meses → riesgo=1; 6+ meses → riesgo=0
        emergency_risk= max(0.0, 1.0 - (emergency_fund_months / 6.0))

        weighted = (
            debt_risk     * _W_DEBT_INDEX  +
            savings_risk  * _W_SAVINGS_CAP +
            emergency_risk* _W_EMERGENCY
        )
        return min(weighted * 100, 100.0)

    @staticmethod
    def _classify_risk(risk_score: float) -> str:
        if risk_score < 35:
            return "low"
        elif risk_score < 65:
            return "medium"
        return "high"
