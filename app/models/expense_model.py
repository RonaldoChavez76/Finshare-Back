from datetime import datetime, timezone
from bson import ObjectId
from typing import List


def build_shared_expense(
    group_id: ObjectId,
    paid_by: ObjectId,
    paid_by_name: str,
    concept: str,
    total_amount: float,
    splits: List[dict],
    category: str = "other",
    currency: str = "MXN",
    expense_date: datetime = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "_id": ObjectId(),
        "groupId": group_id,
        "paidBy": paid_by,
        "paidByName": paid_by_name,
        "concept": concept,
        "totalAmount": total_amount,
        "currency": currency,        # MXN | USD
        "category": category,        # food | rent | transport | entertainment | services | other
        "expenseDate": expense_date or now,
        "status": _compute_status(splits),
        "createdAt": now,
        "updatedAt": now,
        "splits": splits,
    }


def build_split(
    user_id: ObjectId,
    user_name: str,
    amount_owed: float,
    amount_paid: float = 0.0,
) -> dict:
    status = _split_status(amount_owed, amount_paid)
    return {
        "userId": user_id,
        "userName": user_name,
        "amountOwed": amount_owed,
        "amountPaid": amount_paid,
        "status": status,            # pending | partial | settled
        "settledAt": datetime.now(timezone.utc) if status == "settled" else None,
    }


def _split_status(owed: float, paid: float) -> str:
    if paid <= 0:
        return "pending"
    if paid >= owed:
        return "settled"
    return "partial"


def _compute_status(splits: List[dict]) -> str:
    statuses = {s["status"] for s in splits}
    if statuses == {"settled"}:
        return "settled"
    if "settled" in statuses or "partial" in statuses:
        return "partial"
    return "pending"
