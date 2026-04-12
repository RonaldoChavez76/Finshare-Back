from datetime import datetime, timezone
from bson import ObjectId
from app.config.database import get_db
from app.models.expense_model import build_shared_expense, build_split, _compute_status
from app.models.transaction_model import build_transaction


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

        # Identificar quién pagó (quien tenga amountPaid > 0 en los splits)
        pagador_real_id = requester_id
        pagador_nombre = requester.get("fullName", "Usuario")
        
        for s in data["splits"]:
            if float(s.get("amountPaid", 0)) > 0:
                pagador_real_id = str(s["userId"])
                pagador_nombre = s.get("userName", pagador_nombre)
                break

        expense_doc = build_shared_expense(
            group_id=ObjectId(group_id),
            paid_by=ObjectId(pagador_real_id),
            paid_by_name=pagador_nombre,
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

        # Registro de Transacciones Automáticas -------------------------------
        # 1. Gasto para el que está pagando (Target User)
        payer_tx = build_transaction(
            user_id=ObjectId(target_user_id),
            transaction_type="expense",
            amount=amount_paid,
            concept=f"Saldar deuda: {expense['concept']}",
            category="deuda_grupal",
            transaction_date=datetime.now(timezone.utc)
        )
        db.transactions.insert_one(payer_tx)

        # 2. Ingreso para el que recibe el dinero (Original Payer)
        receiver_id = expense["paidBy"]
        receiver_tx = build_transaction(
            user_id=receiver_id,
            transaction_type="income",
            amount=amount_paid,
            concept=f"Cobro de deuda: {expense['concept']} (de {target_split.get('userName')})",
            category="deuda_grupal",
            transaction_date=datetime.now(timezone.utc)
        )
        db.transactions.insert_one(receiver_tx)

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
    
    @staticmethod
    def get_balances(group_id: str):
        db = get_db()
        group = db.groups.find_one({"_id": ObjectId(group_id)})
        if not group: return []
        
        members = group.get("members", [])
        gastos = list(db.shared_expenses.find({"groupId": ObjectId(group_id)}))
        
        saldos = {str(m["userId"]): {
            "userId": str(m["userId"]),
            "userName": m.get("displayName", "Usuario"),
            "totalPagado": 0.0,
            "totalAdeudado": 0.0,
            "balanceNeto": 0.0
        } for m in members if m.get("isActive")}
        
        for gasto in gastos:
            paid_by_id = str(gasto["paidBy"])
            for split in gasto.get("splits", []):
                u_id = str(split["userId"])
                if u_id not in saldos: continue
                
                remaining = float(split.get("amountOwed", 0)) - float(split.get("amountPaid", 0))
                
                # Estadísticas
                saldos[u_id]["totalAdeudado"] += float(split.get("amountOwed", 0))
                saldos[u_id]["totalPagado"] += float(split.get("amountPaid", 0))

                # Lógica de Balance Contable Simplificada:
                # Balance neto = Todo lo que el usuario ha pagado - Todo lo que debe
                saldos[u_id]["balanceNeto"] += float(split.get("amountPaid", 0))
                saldos[u_id]["balanceNeto"] -= float(split.get("amountOwed", 0))

        return [dict(s, balanceNeto=round(s["balanceNeto"], 2)) for s in saldos.values()]
    
    @staticmethod
    def update_expense(expense_id: str, requester_id: str, data: dict) -> dict:
        db = get_db()
        
        # 1. Verificar que el gasto exista
        expense = db.shared_expenses.find_one({"_id": ObjectId(expense_id)})
        if not expense:
            raise ValueError("Gasto no encontrado.")

        # 2. Seguridad: Solo quien lo pagó o un admin puede editarlo
        group = db.groups.find_one({"_id": expense["groupId"]})
        if str(expense["paidBy"]) != requester_id and not _is_admin(group, requester_id):
            raise PermissionError("No tienes permiso para editar este gasto.")

        # 3. Preparar los datos para actualizar
        # Convertimos los strings de IDs en ObjectIds para los splits
        if "splits" in data:
            for s in data["splits"]:
                s["userId"] = ObjectId(s["userId"])
                # Aseguramos que los montos sean float
                s["amountOwed"] = float(s["amountOwed"])
                s["amountPaid"] = float(s["amountPaid"])

        update_data = {
            "concept": data.get("concept", expense["concept"]),
            "totalAmount": float(data.get("totalAmount", expense["totalAmount"])),
            "category": data.get("category", expense["category"]),
            "splits": data.get("splits", expense["splits"]),
            "updatedAt": datetime.now(timezone.utc)
        }

        # 4. Ejecutar la actualización en MongoDB
        db.shared_expenses.update_one(
            {"_id": ObjectId(expense_id)},
            {"$set": update_data}
        )

        return db.shared_expenses.find_one({"_id": ObjectId(expense_id)})


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
