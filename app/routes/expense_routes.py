from flask import Blueprint
from app.controllers.expense_controller import ExpenseController
from app.utils.jwt_helper import jwt_required

expenses_bp = Blueprint("expenses", __name__, url_prefix="/api")

# Gastos por grupo
expenses_bp.post("/groups/<group_id>/expenses")(jwt_required(ExpenseController.create))
expenses_bp.get("/groups/<group_id>/expenses")(jwt_required(ExpenseController.list_group))
expenses_bp.get("/groups/<group_id>/balances")(jwt_required(ExpenseController.get_balances))
expenses_bp.patch("/expenses/<expense_id>")(jwt_required(ExpenseController.update))

# Operaciones sobre un gasto individual
expenses_bp.get("/expenses/<expense_id>")(jwt_required(ExpenseController.get))
expenses_bp.post("/expenses/<expense_id>/settle")(jwt_required(ExpenseController.settle))
expenses_bp.delete("/expenses/<expense_id>")(jwt_required(ExpenseController.delete))
