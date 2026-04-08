from flask import request
from marshmallow import ValidationError
from app.services.auth_service import AuthService
from app.schemas.auth_schemas import RegisterSchema, LoginSchema, FinanceProfileSchema, DebtSchema
from app.models.user_model import build_debt
from app.utils.responses import success_response, error_response

_register_schema        = RegisterSchema()
_login_schema           = LoginSchema()
_finance_schema         = FinanceProfileSchema()
_debt_schema            = DebtSchema()


class AuthController:

    @staticmethod
    def register():
        try:
            data = _register_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            result = AuthService.register(
                full_name=data["fullName"],
                email=data["email"],
                password=data["password"],
                phone=data.get("phone"),
            )
        except ValueError as e:
            return error_response(str(e), 409)
        return success_response(result, "Usuario registrado exitosamente", 201)

    @staticmethod
    def login():
        try:
            data = _login_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            result = AuthService.login(data["email"], data["password"])
        except ValueError as e:
            return error_response(str(e), 401)
        return success_response(result, "Login exitoso")

    @staticmethod
    def get_profile():
        try:
            user = AuthService.get_profile(request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(user)

    @staticmethod
    def update_finance():
        try:
            data = _finance_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            user = AuthService.update_finance_profile(request.current_user_id, data)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(user, "Perfil financiero actualizado")

    @staticmethod
    def add_debt():
        try:
            data = _debt_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        debt_doc = build_debt(
            creditor=data["creditor"],
            total_amount=data["totalAmount"],
            remaining_amount=data["remainingAmount"],
            monthly_payment=data["monthlyPayment"],
            debt_type=data.get("debtType", "other"),
            is_active=data.get("isActive", True),
        )

        try:
            user = AuthService.add_debt(request.current_user_id, debt_doc)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(user, "Deuda registrada", 201)
