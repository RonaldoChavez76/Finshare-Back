from datetime import datetime, timezone
from bson import ObjectId
from app.config.database import get_db
from app.models.expense_model import build_shared_expense, build_split, _compute_status


class ExpenseService:

    @staticmethod
    def create_expense(group_id: str, requester_id: str, data: dict) -> dict:
        db = get_db()
        group = db.groups.find_one({"_id": ObjectId(group_id), "isActive": True})
        if not group:
            raise ValueError("Grupo no encontrado.")
        _assert_member(group, requester_id)

        requester = db.users.find_one({"_id": ObjectId(requester_id)}, {"fullName": 1})

        splits = [
            build_split(
                user_id=ObjectId(s["userId"]),
                user_name=s["userName"],
                amount_owed=s["amountOwed"],
                amount_paid=s.get("amountPaid", 0.0),
            )
            for s in data["splits"]
        ]

        expense_doc = build_shared_expense(
            group_id=ObjectId(group_id),
            paid_by=ObjectId(requester_id),
            paid_by_name=requester["fullName"],
            concept=data["concept"],
            total_amount=data["totalAmount"],
            splits=splits,
            category=data.get("category", "other"),
            currency=data.get("currency", "MXN"),
            expense_date=data.get("expenseDate"),
        )
        db.shared_expenses.insert_one(expense_doc)
        return expense_doc

    @staticmethod
    def get_group_expenses(group_id: str, requester_id: str, page: int = 1, per_page: int = 20) -> dict:
        db = get_db()
        group = db.groups.find_one({"_id": ObjectId(group_id), "isActive": True})
        if not group:
            raise ValueError("Grupo no encontrado.")
        _assert_member(group, requester_id)

        skip = (page - 1) * per_page
        query = {"groupId": ObjectId(group_id)}
        total = db.shared_expenses.count_documents(query)
        expenses = list(
            db.shared_expenses.find(query)
            .sort("expenseDate", -1)
            .skip(skip)
            .limit(per_page)
        )
        return {"items": expenses, "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def get_expense(expense_id: str, requester_id: str) -> dict:
        db = get_db()
        expense = db.shared_expenses.find_one({"_id": ObjectId(expense_id)})
        if not expense:
            raise ValueError("Gasto no encontrado.")
        group = db.groups.find_one({"_id": expense["groupId"]})
        _assert_member(group, requester_id)
        return expense

    @staticmethod
    def settle_split(expense_id: str, requester_id: str, target_user_id: str, amount_paid: float) -> dict:
        """Registra un pago parcial o total de un split."""
        db = get_db()
        expense = db.shared_expenses.find_one({"_id": ObjectId(expense_id)})
        if not expense:
            raise ValueError("Gasto no encontrado.")

        group = db.groups.find_one({"_id": expense["groupId"]})
        _assert_member(group, requester_id)

        # Solo el propio usuario o un admin puede registrar el pago
        is_self = requester_id == target_user_id
        is_admin = _is_admin(group, requester_id)
        if not (is_self or is_admin):
            raise PermissionError("No tienes permiso para registrar este pago.")

        # Buscar el split
        target_split = next(
            (s for s in expense["splits"] if str(s["userId"]) == target_user_id), None
        )
        if not target_split:
            raise ValueError("Split no encontrado para ese usuario.")

        new_paid = min(target_split["amountPaid"] + amount_paid, target_split["amountOwed"])
        new_status = "settled" if new_paid >= target_split["amountOwed"] else "partial"
        settled_at = datetime.now(timezone.utc) if new_status == "settled" else target_split.get("settledAt")

        # Actualizar el split específico con arrayFilters
        db.shared_expenses.update_one(
            {"_id": ObjectId(expense_id)},
            {
                "$set": {
                    "splits.$[elem].amountPaid": new_paid,
                    "splits.$[elem].status": new_status,
                    "splits.$[elem].settledAt": settled_at,
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
            array_filters=[{"elem.userId": ObjectId(target_user_id)}],
        )

        # Recalcular status global del gasto
        updated = db.shared_expenses.find_one({"_id": ObjectId(expense_id)})
        new_global_status = _compute_status(updated["splits"])
        db.shared_expenses.update_one(
            {"_id": ObjectId(expense_id)},
            {"$set": {"status": new_global_status}},
        )

        return db.shared_expenses.find_one({"_id": ObjectId(expense_id)})

    @staticmethod
    def delete_expense(expense_id: str, requester_id: str) -> bool:
        db = get_db()
        expense = db.shared_expenses.find_one({"_id": ObjectId(expense_id)})
        if not expense:
            raise ValueError("Gasto no encontrado.")
        group = db.groups.find_one({"_id": expense["groupId"]})
        # Solo quien pagó o un admin puede eliminar
        if str(expense["paidBy"]) != requester_id and not _is_admin(group, requester_id):
            raise PermissionError("No tienes permiso para eliminar este gasto.")
        db.shared_expenses.delete_one({"_id": ObjectId(expense_id)})
        return True


# ─── Helpers (misma lógica que en group_service, extraída aquí también) ──────

def _is_member(group: dict, user_id: str) -> bool:
    return any(
        str(m["userId"]) == user_id and m.get("isActive")
        for m in group.get("members", [])
    )


def _is_admin(group: dict, user_id: str) -> bool:
    return any(
        str(m["userId"]) == user_id and m.get("role") == "admin" and m.get("isActive")
        for m in group.get("members", [])
    ) or str(group.get("ownerId")) == user_id


def _assert_member(group: dict, user_id: str):
    if not _is_member(group, user_id):
        raise PermissionError("No eres miembro de este grupo.")
