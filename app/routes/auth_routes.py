from flask import Blueprint
from app.controllers.auth_controller import AuthController
from app.utils.jwt_helper import jwt_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
# Públicas
auth_bp.post("/register")(AuthController.register)
auth_bp.post("/login")(AuthController.login)

# Protegidas
auth_bp.get( "/profile")(jwt_required(AuthController.get_profile))
auth_bp.put( "/profile/finance")(jwt_required(AuthController.update_finance))
auth_bp.post("/profile/debts")(jwt_required(AuthController.add_debt))
