from flask import Blueprint
from app.controllers.transaction_controller import TransactionController
from app.utils.jwt_helper import jwt_required

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")

transactions_bp.post("/")(jwt_required(TransactionController.create))
transactions_bp.get("/")(jwt_required(TransactionController.list_all))
transactions_bp.get("/summary")(jwt_required(TransactionController.summary))
transactions_bp.get("/<tx_id>")(jwt_required(TransactionController.get))
transactions_bp.put("/<tx_id>")(jwt_required(TransactionController.update))
transactions_bp.delete("/<tx_id>")(jwt_required(TransactionController.delete))
