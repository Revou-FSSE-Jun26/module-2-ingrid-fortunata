from marshmallow import Schema, fields, validates, validates_schema, ValidationError, validate
import re

VALID_STATUSES = {'pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled'}

# Reuse product size enum for order item validation
VALID_SIZES = ["XS", "S", "M", "L", "XL", "XXL", "FREE", "Free Size"]

# Basic international phone regex: optional leading +, then digits, spaces, dashes, parens
PHONE_REGEX = re.compile(r'^\+?[\d\s\-().]{7,20}$')


def not_blank(value):
    """Reject strings that are empty or whitespace-only."""
    if not value or not value.strip():
        raise ValidationError("Field cannot be blank or whitespace only.")


class OrderItemInputSchema(Schema):
    product_id = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="product_id must be a positive integer.")
    )
    quantity = fields.Int(required=True)
    # size and color are optional overrides; validated if provided
    size = fields.Str(allow_none=True, validate=validate.OneOf(
        VALID_SIZES,
        error="Invalid size. Must be one of: XS, S, M, L, XL, XXL, FREE, Free Size."
    ))
    color = fields.Str(allow_none=True, validate=[validate.Length(min=1, max=50), not_blank])

    @validates("quantity")
    def validate_quantity(self, value, **kwargs):
        if value <= 0:
            raise ValidationError("Quantity must be a positive integer (>= 1).")


class OrderCreateInputSchema(Schema):
    items = fields.List(fields.Nested(OrderItemInputSchema), required=True)
    shipping_address = fields.Str(
        required=True,
        validate=[validate.Length(min=5, max=500), not_blank]
    )
    recipient_name = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=150), not_blank]
    )
    recipient_phone = fields.Str(
        required=True,
        validate=[validate.Length(min=7, max=20), not_blank]
    )

    @validates("items")
    def validate_items(self, value, **kwargs):
        if not value:
            raise ValidationError("Order must contain at least one item.")
        
        seen_product_ids = set()
        for item in value:
            prod_id = item.get("product_id")
            if prod_id in seen_product_ids:
                raise ValidationError(
                    f"Duplicate product_id {prod_id} found. Please consolidate quantities into a single item."
                )
            seen_product_ids.add(prod_id)

    @validates("recipient_phone")
    def validate_phone_format(self, value, **kwargs):
        if not PHONE_REGEX.match(value.strip()):
            raise ValidationError(
                "Invalid phone number format. Use digits, spaces, dashes, or parentheses "
                "(e.g. +62 812-3456-7890)."
            )


class OrderResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    total_amount = fields.Float(dump_only=True)
    status = fields.Str(dump_only=True)
    shipping_address = fields.Str(dump_only=True)
    recipient_name = fields.Str(dump_only=True)
    recipient_phone = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class OrderDetailItemSchema(Schema):
    product_id = fields.Int()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    quantity = fields.Int()
    price_at_purchase = fields.Float()
    size = fields.Str()
    color = fields.Str()


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
