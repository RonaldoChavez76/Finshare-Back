from flask import Blueprint
from app.controllers.dashboard_controller import DashboardController
from app.utils.jwt_helper import jwt_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

dashboard_bp.get("/personal")(jwt_required(DashboardController.personal))
dashboard_bp.get("/group/<group_id>")(jwt_required(DashboardController.group_summary))
dashboard_bp.put("/group/<group_id>/analytics")(jwt_required(DashboardController.group_analytics))
