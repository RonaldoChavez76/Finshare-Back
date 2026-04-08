"""
DashboardService – Módulo de Visualización de Riesgos y Grupos.

Consolida y agrega datos financieros para los tableros de control (dashboards).
No modifica registro de transacciones; sólo lectura + actualización de analytics.
"""
from datetime import datetime, timezone
from bson import ObjectId
from app.config.database import get_db


class DashboardService:

    # ── Panel Personal ─────────────────────────────────────────────────────────
    @staticmethod
    def personal_summary(user_id: str) -> dict:
        """
        Retorna el resumen financiero completo del usuario para el dashboard personal:
        - Perfil financiero (finance)
        - Deudas activas con totales
        - Último reporte de riesgo (lastRiskReport)
        - Resumen de gastos compartidos pendientes
        """
        db   = get_db()
        user = db.users.find_one(
            {"_id": ObjectId(user_id)},
            {"passwordHash": 0},
        )
        if not user:
            raise ValueError("Usuario no encontrado.")

        finance = user.get("finance") or {}
        debts   = [d for d in (user.get("debts") or []) if d.get("isActive", True)]

        # Totales de deudas activas
        total_debt_remaining = sum(float(d.get("remainingAmount", 0)) for d in debts)
        total_monthly_debt   = sum(float(d.get("monthlyPayment",  0)) for d in debts)

        # Gastos compartidos donde el usuario debe pagar (splits pendientes)
        pending_pipeline = [
            {"$unwind": "$splits"},
            {
                "$match": {
                    "splits.userId": ObjectId(user_id),
                    "splits.status": {"$in": ["pending", "partial"]},
                }
            },
            {
                "$group": {
                    "_id":          None,
                    "totalOwed":    {"$sum": "$splits.amountOwed"},
                    "totalPaid":    {"$sum": "$splits.amountPaid"},
                    "expenseCount": {"$sum": 1},
                }
            },
        ]
        pending_agg = list(db.shared_expenses.aggregate(pending_pipeline))
        pending_info = pending_agg[0] if pending_agg else {
            "totalOwed": 0, "totalPaid": 0, "expenseCount": 0}

        # Gastos del usuario por categoría (últimos 3 meses)
        category_pipeline = [
            {
                "$match": {
                    "paidBy": ObjectId(user_id),
                }
            },
            {
                "$group": {
                    "_id":         "$category",
                    "totalAmount": {"$sum": "$totalAmount"},
                    "count":       {"$sum": 1},
                }
            },
            {"$sort": {"totalAmount": -1}},
        ]
        by_category = list(db.shared_expenses.aggregate(category_pipeline))

        return {
            "user": {
                "_id":      str(user["_id"]),
                "fullName": user.get("fullName"),
                "email":    user.get("email"),
            },
            "finance": finance,
            "debtsSummary": {
                "activeDebts":        len(debts),
                "totalRemaining":     round(total_debt_remaining, 2),
                "totalMonthlyPayment":round(total_monthly_debt,   2),
                "debts":              debts,
            },
            "lastRiskReport": user.get("lastRiskReport"),
            "sharedExpensesPending": {
                "totalOwed":    round(float(pending_info.get("totalOwed", 0)), 2),
                "totalPaid":    round(float(pending_info.get("totalPaid", 0)), 2),
                "balance":      round(
                    float(pending_info.get("totalOwed", 0)) -
                    float(pending_info.get("totalPaid", 0)), 2),
                "expenseCount": pending_info.get("expenseCount", 0),
            },
            "spendingByCategory": [
                {
                    "category":    item["_id"],
                    "totalAmount": round(float(item["totalAmount"]), 2),
                    "count":       item["count"],
                }
                for item in by_category
            ],
        }

    # ── Panel de Grupo ─────────────────────────────────────────────────────────
    @staticmethod
    def group_summary(group_id: str, requester_id: str) -> dict:
        """
        Retorna el panel completo de un grupo:
        - Info básica del grupo + analytics
        - Balance por miembro (cuánto debe / cuánto ha pagado)
        - Gastos por categoría
        - Gastos recientes (últimos 10)
        """
        db = get_db()
        group = db.groups.find_one({"_id": ObjectId(group_id), "isActive": True})
        if not group:
            raise ValueError("Grupo no encontrado.")

        # Verificar que el solicitante es miembro
        _assert_member(group, requester_id)

        members = [m for m in group.get("members", []) if m.get("isActive")]

        # Balance por miembro ---------------------------------------------------
        balance_pipeline = [
            {"$match": {"groupId": ObjectId(group_id)}},
            {"$unwind": "$splits"},
            {
                "$group": {
                    "_id":        "$splits.userId",
                    "userName":   {"$first": "$splits.userName"},
                    "totalOwed":  {"$sum": "$splits.amountOwed"},
                    "totalPaid":  {"$sum": "$splits.amountPaid"},
                }
            },
        ]
        balance_by_member = list(db.shared_expenses.aggregate(balance_pipeline))
        for b in balance_by_member:
            b["balance"]  = round(float(b["totalOwed"]) - float(b["totalPaid"]), 2)
            b["totalOwed"]= round(float(b["totalOwed"]), 2)
            b["totalPaid"]= round(float(b["totalPaid"]), 2)

        # Gastos por categoría --------------------------------------------------
        category_pipeline = [
            {"$match": {"groupId": ObjectId(group_id)}},
            {
                "$group": {
                    "_id":         "$category",
                    "totalAmount": {"$sum": "$totalAmount"},
                    "count":       {"$sum": 1},
                }
            },
            {"$sort": {"totalAmount": -1}},
        ]
        by_category = list(db.shared_expenses.aggregate(category_pipeline))

        # Gastos recientes -------------------------------------------------------
        recent_expenses = list(
            db.shared_expenses.find({"groupId": ObjectId(group_id)})
            .sort("expenseDate", -1)
            .limit(10)
        )

        # Estadísticas generales ------------------------------------------------
        stats_pipeline = [
            {"$match": {"groupId": ObjectId(group_id)}},
            {
                "$group": {
                    "_id":         None,
                    "totalSpent":  {"$sum": "$totalAmount"},
                    "expenseCount":{"$sum": 1},
                }
            },
        ]
        stats_agg = list(db.shared_expenses.aggregate(stats_pipeline))
        stats = stats_agg[0] if stats_agg else {"totalSpent": 0, "expenseCount": 0}

        return {
            "group": {
                "_id":         str(group["_id"]),
                "name":        group.get("name"),
                "description": group.get("description"),
                "groupType":   group.get("groupType"),
                "memberCount": len(members),
                "analytics":   group.get("analytics"),
            },
            "stats": {
                "totalSpent":   round(float(stats.get("totalSpent", 0)), 2),
                "expenseCount": stats.get("expenseCount", 0),
            },
            "balanceByMember":  balance_by_member,
            "spendingByCategory": [
                {
                    "category":    item["_id"],
                    "totalAmount": round(float(item["totalAmount"]), 2),
                    "count":       item["count"],
                }
                for item in by_category
            ],
            "recentExpenses": recent_expenses,
        }

    # ── Recalcular analytics del grupo ─────────────────────────────────────────
    @staticmethod
    def recalculate_group_analytics(group_id: str, requester_id: str) -> dict:
        """
        Calcula y persiste groups.analytics:
        - stabilityIndex       (0-1): 1 = todos pagaron equitativamente
        - conflictRiskLevel    (low/medium/high)
        - contributionVariance : varianza de pagos entre miembros
        - dominantPayerId      : miembro con más gasto total
        """
        db = get_db()
        group = db.groups.find_one({"_id": ObjectId(group_id), "isActive": True})
        if not group:
            raise ValueError("Grupo no encontrado.")

        _assert_member(group, requester_id)

        members = [m for m in group.get("members", []) if m.get("isActive")]
        n = len(members)

        # Cuánto pagó cada miembro (paidBy, no splits)
        paid_pipeline = [
            {"$match": {"groupId": ObjectId(group_id)}},
            {
                "$group": {
                    "_id":      "$paidBy",
                    "totalPaid":{"$sum": "$totalAmount"},
                }
            },
        ]
        paid_agg = list(db.shared_expenses.aggregate(paid_pipeline))
        payments  = {str(p["_id"]): float(p["totalPaid"]) for p in paid_agg}
        total_all = sum(payments.values()) or 1.0
        mean_pay  = total_all / n if n else 0

        # Varianza de contribuciones
        all_pays = [payments.get(str(m["userId"]), 0.0) for m in members]
        variance = (sum((p - mean_pay) ** 2 for p in all_pays) / n) if n else 0

        # Stability index: 1 - coeficiente de variación (normalizado)
        cv = (variance ** 0.5) / mean_pay if mean_pay else 1.0
        stability_index = round(max(0.0, 1.0 - min(cv, 1.0)), 4)

        # Nivel de conflicto
        if stability_index >= 0.70:
            conflict_risk = "low"
        elif stability_index >= 0.40:
            conflict_risk = "medium"
        else:
            conflict_risk = "high"

        # Pagador dominante
        dominant_id = None
        if payments:
            dominant_key = max(payments, key=payments.get)
            dominant_id  = ObjectId(dominant_key)

        analytics = {
            "stabilityIndex":       stability_index,
            "conflictRiskLevel":    conflict_risk,
            "contributionVariance": round(variance, 4),
            "dominantPayerId":      dominant_id,
            "calculatedAt":         datetime.now(timezone.utc),
        }

        db.groups.update_one(
            {"_id": ObjectId(group_id)},
            {"$set": {"analytics": analytics, "updatedAt": datetime.now(timezone.utc)}},
        )

        return analytics


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _assert_member(group: dict, user_id: str):
    is_member = any(
        str(m["userId"]) == user_id and m.get("isActive")
        for m in group.get("members", [])
    )
    if not is_member:
        raise PermissionError("No eres miembro de este grupo.")
