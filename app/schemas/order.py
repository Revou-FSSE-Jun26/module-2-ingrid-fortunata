from marshmallow import Schema, fields, validates, ValidationError, validate

VALID_STATUSES = {'pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled'}

class OrderItemInputSchema(Schema):
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    size = fields.Str(allow_none=True)
    color = fields.Str(allow_none=True)

    @validates("quantity")
    def validate_quantity(self, value, **kwargs):
        if value is None or value <= 0:
            raise ValidationError("Quantity cannot be null, zero, or negative.")

class OrderCreateInputSchema(Schema):
    items = fields.List(fields.Nested(OrderItemInputSchema), required=True)

    @validates("items")
    def validate_items(self, value, **kwargs):
        if not value:
            raise ValidationError("Order must contain at least one item.")

class OrderResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    total_amount = fields.Float(dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class OrderDetailItemSchema(Schema):
    product_id = fields.Int()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    quantity = fields.Int()
    price_at_purchase = fields.Float()
    size = fields.Str(allow_none=True)
    color = fields.Str(allow_none=True)

class OrderDetailSchema(OrderResponseSchema):
    items = fields.List(fields.Nested(OrderDetailItemSchema), dump_only=True)

class OrderResponseWrapperSchema(Schema):
    data = fields.Nested(OrderDetailSchema, dump_only=True)

class OrderListResponseSchema(Schema):
    data = fields.List(fields.Nested(OrderResponseSchema), dump_only=True)

class OrderUpdateStatusSchema(Schema):
    status = fields.Str(
        required=True,
        validate=validate.OneOf(
            list(VALID_STATUSES),
            error="Invalid status. Must be one of: pending, paid, processing, shipped, delivered, cancelled."
        )
    )
