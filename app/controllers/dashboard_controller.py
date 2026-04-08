"""
DashboardController – Maneja las peticiones HTTP del módulo de Visualización.
"""
from flask import request
from app.services.dashboard_service import DashboardService
from app.utils.responses import success_response, error_response


class DashboardController:

    @staticmethod
    def personal():
        """
        GET /api/dashboard/personal
        Retorna el panel financiero completo del usuario autenticado.
        """
        try:
            summary = DashboardService.personal_summary(request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        return success_response(summary)

    @staticmethod
    def group_summary(group_id: str):
        """
        GET /api/dashboard/group/<group_id>
        Retorna el panel de un grupo: balances, categorías y gastos recientes.
        """
        try:
            summary = DashboardService.group_summary(group_id, request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        except PermissionError as e:
            return error_response(str(e), 403)
        return success_response(summary)

    @staticmethod
    def group_analytics(group_id: str):
        """
        PUT /api/dashboard/group/<group_id>/analytics
        Recalcula y persiste el analytics del grupo.
        """
        try:
            analytics = DashboardService.recalculate_group_analytics(
                group_id, request.current_user_id
            )
        except ValueError as e:
            return error_response(str(e), 404)
        except PermissionError as e:
            return error_response(str(e), 403)
        return success_response(analytics, "Analytics del grupo actualizado")
