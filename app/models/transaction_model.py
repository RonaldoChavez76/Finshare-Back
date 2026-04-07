from datetime import datetime, timezone
from bson import ObjectId


def build_transaction(
    user_id: ObjectId,
    transaction_type: str,   # income | expense
    amount: float,
    concept: str,
    category: str = "other",
    currency: str = "MXN",
    transaction_date: datetime = None,
    notes: str = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "_id": ObjectId(),
        "userId": user_id,
        "type": transaction_type,
        "amount": amount,
        "concept": concept,
        "category": category,
        "currency": currency,
        "transactionDate": transaction_date or now,
        "notes": notes,
        "createdAt": now,
        "updatedAt": now,
    }
