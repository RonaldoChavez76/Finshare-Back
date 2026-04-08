"""
SimulationController – Maneja las peticiones HTTP del módulo de Simulación.
"""
from flask import request
from marshmallow import ValidationError
from app.services.simulation_service import SimulationService
from app.schemas.simulation_schemas import SimulationSchema
from app.utils.responses import success_response, error_response, paginated_response

_simulation_schema = SimulationSchema()


class SimulationController:

    @staticmethod
    def create():
        """
        POST /api/simulations/
        Crea y ejecuta una simulación financiera.
        """
        try:
            data = _simulation_schema.load(request.get_json() or {})
        except ValidationError as e:
            return error_response("Datos inválidos", 422, e.messages)
        try:
            sim = SimulationService.run(request.current_user_id, data)
        except (ValueError, PermissionError) as e:
            status = 403 if isinstance(e, PermissionError) else 400
            return error_response(str(e), status)
        return success_response(sim, "Simulación ejecutada exitosamente", 201)

    @staticmethod
    def list_simulations():
        """
        GET /api/simulations/
        Lista las simulaciones del usuario autenticado (paginado).
        """
        page     = int(request.args.get("page",     1))
        per_page = int(request.args.get("per_page", 20))
        result   = SimulationService.list_by_user(request.current_user_id, page, per_page)
        return paginated_response(result["items"], result["total"], result["page"], result["per_page"])

    @staticmethod
    def get_simulation(simulation_id: str):
        """
        GET /api/simulations/<simulation_id>
        Retorna el detalle de una simulación específica.
        """
        try:
            sim = SimulationService.get(simulation_id, request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        except PermissionError as e:
            return error_response(str(e), 403)
        return success_response(sim)

    @staticmethod
    def delete_simulation(simulation_id: str):
        """
        DELETE /api/simulations/<simulation_id>
        Elimina una simulación propia.
        """
        try:
            SimulationService.delete(simulation_id, request.current_user_id)
        except ValueError as e:
            return error_response(str(e), 404)
        except PermissionError as e:
            return error_response(str(e), 403)
        return success_response(None, "Simulación eliminada")
