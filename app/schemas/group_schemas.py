from marshmallow import Schema, fields, validate, validates_schema, ValidationError


# ─── Groups ──────────────────────────────────────────────────────────────────

GROUP_TYPES = ["roommates", "travel", "project", "other"]
MEMBER_ROLES = ["admin", "member"]

class CreateGroupSchema(Schema):
    name        = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    description = fields.Str(load_default="", validate=validate.Length(max=300))
    groupType   = fields.Str(load_default="other", validate=validate.OneOf(GROUP_TYPES))


class AddMemberSchema(Schema):
    userId      = fields.Str(required=True)
    displayName = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    role        = fields.Str(load_default="member", validate=validate.OneOf(MEMBER_ROLES))


# ─── Shared Expenses ─────────────────────────────────────────────────────────

CATEGORIES   = ["food", "rent", "transport", "entertainment", "services", "other"]
CURRENCIES   = ["MXN", "USD"]

class SplitInputSchema(Schema):
    userId      = fields.Str(required=True)
    userName    = fields.Str(required=True)
    amountOwed  = fields.Float(required=True, validate=validate.Range(min=0.01))
    amountPaid  = fields.Float(load_default=0.0, validate=validate.Range(min=0))


class CreateExpenseSchema(Schema):
    concept     = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    totalAmount = fields.Float(required=True, validate=validate.Range(min=0.01))
    category    = fields.Str(load_default="other", validate=validate.OneOf(CATEGORIES))
    currency    = fields.Str(load_default="MXN", validate=validate.OneOf(CURRENCIES))
    expenseDate = fields.DateTime(load_default=None)
    splits      = fields.List(fields.Nested(SplitInputSchema), required=True, validate=validate.Length(min=1))

    @validates_schema
    def validate_splits_total(self, data, **kwargs):
        total = data.get("totalAmount", 0)
        splits_total = sum(s["amountOwed"] for s in data.get("splits", []))
        if abs(splits_total - total) > 0.01:
            raise ValidationError(
                f"La suma de splits ({splits_total}) no coincide con totalAmount ({total}).",
                field_name="splits",
            )


class SettleExpenseSchema(Schema):
    userId     = fields.Str(required=True)
    amountPaid = fields.Float(required=True, validate=validate.Range(min=0.01))


# ─── Personal Transactions ───────────────────────────────────────────────────

TRANSACTION_TYPES = ["income", "expense"]

class TransactionSchema(Schema):
    type            = fields.Str(required=True, validate=validate.OneOf(TRANSACTION_TYPES))
    amount          = fields.Float(required=True, validate=validate.Range(min=0.01))
    concept         = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    category        = fields.Str(load_default="other")
    currency        = fields.Str(load_default="MXN", validate=validate.OneOf(CURRENCIES))
    transactionDate = fields.DateTime(load_default=None)
    notes           = fields.Str(load_default=None, validate=validate.Length(max=500))
