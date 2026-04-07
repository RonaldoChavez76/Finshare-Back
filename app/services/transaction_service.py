from datetime import datetime, timezone
from bson import ObjectId
from app.config.database import get_db
from app.models.transaction_model import build_transaction


class TransactionService:

    @staticmethod
    def create(user_id: str, data: dict) -> dict:
        db = get_db()
        doc = build_transaction(
            user_id=ObjectId(user_id),
            transaction_type=data["type"],
            amount=data["amount"],
            concept=data["concept"],
            category=data.get("category", "other"),
            currency=data.get("currency", "MXN"),
            transaction_date=data.get("transactionDate"),
            notes=data.get("notes"),
        )
        db.transactions.insert_one(doc)
        return doc

    @staticmethod
    def get_all(user_id: str, tx_type: str = None, page: int = 1, per_page: int = 20) -> dict:
        db = get_db()
        query = {"userId": ObjectId(user_id)}
        if tx_type in ("income", "expense"):
            query["type"] = tx_type

        total = db.transactions.count_documents(query)
        items = list(
            db.transactions.find(query)
            .sort("transactionDate", -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        return {"items": items, "total": total, "page": page, "per_page": per_page}

    @staticmethod
    def get_one(tx_id: str, user_id: str) -> dict:
        db = get_db()
        doc = db.transactions.find_one({"_id": ObjectId(tx_id), "userId": ObjectId(user_id)})
        if not doc:
            raise ValueError("Transacción no encontrada.")
        return doc

    @staticmethod
    def update(tx_id: str, user_id: str, data: dict) -> dict:
        db = get_db()
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields["updatedAt"] = datetime.now(timezone.utc)

        doc = db.transactions.find_one_and_update(
            {"_id": ObjectId(tx_id), "userId": ObjectId(user_id)},
            {"$set": update_fields},
            return_document=True,
        )
        if not doc:
            raise ValueError("Transacción no encontrada.")
        return doc

    @staticmethod
    def delete(tx_id: str, user_id: str) -> bool:
        db = get_db()
        result = db.transactions.delete_one(
            {"_id": ObjectId(tx_id), "userId": ObjectId(user_id)}
        )
        if result.deleted_count == 0:
            raise ValueError("Transacción no encontrada.")
        return True

    @staticmethod
    def get_summary(user_id: str) -> dict:
        """Resumen mensual: total ingresos, egresos y balance."""
        db = get_db()
        pipeline = [
            {"$match": {"userId": ObjectId(user_id)}},
            {"$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1},
            }},
        ]
        results = {r["_id"]: r for r in db.transactions.aggregate(pipeline)}
        income  = results.get("income",  {"total": 0, "count": 0})
        expense = results.get("expense", {"total": 0, "count": 0})
        return {
            "totalIncome":   income["total"],
            "incomeCount":   income["count"],
            "totalExpenses": expense["total"],
            "expenseCount":  expense["count"],
            "balance":       income["total"] - expense["total"],
        }
