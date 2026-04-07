from flask import request
from marshmallow import ValidationError
from app.services.expense_service import ExpenseService
from app.schemas.group_schemas import CreateExpenseSchema, SettleExpenseSchema
from app.utils.responses import success_response, error_response, paginated_response

_create_schema = CreateExpenseSchema()
_settle_schema = SettleExpenseSchema()


class ExpenseController:

    @staticmethod
    def create(group_id: str):
        try:
            data = _create_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            expense = ExpenseService.create_expense(group_id, request.current_user_id, data)
        except (ValueError, PermissionError) as e:
            status = 403 if isinstance(e, PermissionError) else 400
            return error_response(str(e), status)
        return success_response(expense, "Gasto registrado", 201)

    @staticmethod
    def list_group(group_id: str):
        page     = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        try:
            result = ExpenseService.get_group_expenses(
                group_id, request.current_user_id, page, per_page
            )
        except (ValueError, PermissionError) as e:
            status = 403 if isinstance(e, PermissionError) else 404
            return error_response(str(e), status)
        return paginated_response(result["items"], result["total"], result["page"], result["per_page"])

    @staticmethod
    def get(expense_id: str):
        try:
            expense = ExpenseService.get_expense(expense_id, request.current_user_id)
        except (ValueError, PermissionError) as e:
            status = 403 if isinstance(e, PermissionError) else 404
            return error_response(str(e), status)
        return success_response(expense)

    @staticmethod
    def settle(expense_id: str):
        try:
            data = _settle_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            expense = ExpenseService.settle_split(
                expense_id=expense_id,
                requester_id=request.current_user_id,
                target_user_id=data["userId"],
                amount_paid=data["amountPaid"],
            )
        except (ValueError, PermissionError) as e:
            status = 403 if isinstance(e, PermissionError) else 400
            return error_response(str(e), status)
        return success_response(expense, "Pago registrado")

    @staticmethod
    def delete(expense_id: str):
        try:
            ExpenseService.delete_expense(expense_id, request.current_user_id)
        except (ValueError, PermissionError) as e:
            status = 403 if isinstance(e, PermissionError) else 404
            return error_response(str(e), status)
        return success_response(message="Gasto eliminado")
