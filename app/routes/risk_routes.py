from flask import Blueprint
from app.controllers.risk_controller import RiskController
from app.utils.jwt_helper import jwt_required

risk_bp = Blueprint("risk", __name__, url_prefix="/api/risk")

# Todos los endpoints de riesgo requieren autenticación
risk_bp.post("/analyze")(jwt_required(RiskController.analyze))
risk_bp.get("/report")(jwt_required(RiskController.get_report))
