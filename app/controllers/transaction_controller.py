from flask import request
from marshmallow import ValidationError
from app.services.transaction_service import TransactionService
from app.schemas.group_schemas import TransactionSchema
from app.utils.responses import success_response, error_response, paginated_response

_tx_schema = TransactionSchema()


class TransactionController:

    @staticmethod
    def create():
        try:
            data = _tx_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            tx = TransactionService.create(request.current_user_id, data)
        except Exception as e:
            return error_response(str(e), 400)
        return success_response(tx, "Transacción registrada", 201)

    @staticmethod
    def list_all():
        page     = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        tx_type  = request.args.get("type")          # income | expense
        result   = TransactionService.get_all(request.current_user_id, tx_type, page, per_page)
        return paginated_response(result["items"], result["total"], result["page"], result["per_page"])

    @staticmethod
    def get(tx_id: str):
        try:
            tx = TransactionService.get_one(tx_id, request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(tx)

    @staticmethod
    def update(tx_id: str):
        try:
            data = _tx_schema.load(request.get_json() or {}, partial=True)
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            tx = TransactionService.update(tx_id, request.current_user_id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(tx, "Transacción actualizada")

    @staticmethod
    def delete(tx_id: str):
        try:
            TransactionService.delete(tx_id, request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(message="Transacción eliminada")

    @staticmethod
    def summary():
        data = TransactionService.get_summary(request.current_user_id)
        return success_response(data)
