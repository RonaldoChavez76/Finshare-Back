from flask import Blueprint
from app.controllers.simulation_controller import SimulationController
from app.utils.jwt_helper import jwt_required

simulations_bp = Blueprint("simulations", __name__, url_prefix="/api/simulations")

simulations_bp.post("/")(jwt_required(SimulationController.create))
simulations_bp.post("/preview")(jwt_required(SimulationController.preview))
simulations_bp.get("/")(jwt_required(SimulationController.list_simulations))
simulations_bp.get("/<simulation_id>")(jwt_required(SimulationController.get_simulation))
simulations_bp.delete("/<simulation_id>")(jwt_required(SimulationController.delete_simulation))
