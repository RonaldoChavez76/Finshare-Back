from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
import re


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterSchema(Schema):
    fullName  = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email     = fields.Email(required=True)
    password  = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    phone     = fields.Str(load_default=None, validate=validate.Length(max=20))

    @validates("password")
    def validate_password_strength(self, value, **kwargs):
        if not re.search(r"[A-Z]", value):
            raise ValidationError("Debe contener al menos una mayúscula.")
        if not re.search(r"\d", value):
            raise ValidationError("Debe contener al menos un número.")


class LoginSchema(Schema):
    email    = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


# ─── Finance Profile ─────────────────────────────────────────────────────────

INCOME_STABILITY = ["stable", "variable", "freelance"]

class FinanceProfileSchema(Schema):
    monthlyIncome     = fields.Float(load_default=0, validate=validate.Range(min=0))
    fixedExpenses     = fields.Float(load_default=0, validate=validate.Range(min=0))
    variableExpenses  = fields.Float(load_default=0, validate=validate.Range(min=0))
    savings           = fields.Float(load_default=0, validate=validate.Range(min=0))
    incomeStability   = fields.Str(
        load_default="stable",
        validate=validate.OneOf(INCOME_STABILITY),
    )


# ─── Debt ────────────────────────────────────────────────────────────────────

DEBT_TYPES = ["credit", "loan", "mortgage", "other"]

class DebtSchema(Schema):
    creditor        = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    totalAmount     = fields.Float(required=True, validate=validate.Range(min=0.01))
    remainingAmount = fields.Float(required=True, validate=validate.Range(min=0))
    monthlyPayment  = fields.Float(required=True, validate=validate.Range(min=0))
    debtType        = fields.Str(load_default="other", validate=validate.OneOf(DEBT_TYPES))
