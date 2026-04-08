"""
RiskController – Maneja las peticiones HTTP del módulo de Análisis de Estabilidad.
Patrón idéntico al resto del proyecto (AuthController, ExpenseController, etc.)
"""
from flask import request
from app.services.risk_service import RiskService
from app.utils.responses import success_response, error_response


class RiskController:

    @staticmethod
    def analyze():
        """
        POST /api/risk/analyze
        Calcula el riesgo financiero del usuario autenticado y
        persiste el resultado en users.lastRiskReport.
        """
        try:
            report = RiskService.analyze(request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(report, "Análisis de riesgo completado")

    @staticmethod
    def get_report():
        """
        GET /api/risk/report
        Retorna el último reporte de riesgo guardado sin recalcular.
        """
        try:
            report = RiskService.get_report(request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(report)
