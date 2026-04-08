"""
Schemas de validación para el módulo de riesgo y simulaciones.
Usa Marshmallow, consistente con el resto del proyecto.
"""
from marshmallow import Schema, fields, validate, validates, ValidationError


SCENARIO_TYPES = ["job_loss", "rent_increase", "member_default", "expense_spike", "income_cut"]


class SimulationSchema(Schema):
    """Schema para crear y ejecutar una simulación."""
    scenarioType  = fields.Str(
        required=True,
        validate=validate.OneOf(SCENARIO_TYPES),
        error_messages={"required": "scenarioType es obligatorio."},
    )
    description   = fields.Str(load_default="")
    targetGroupId = fields.Str(load_default=None, allow_none=True)
    parameters    = fields.Dict(load_default={})
