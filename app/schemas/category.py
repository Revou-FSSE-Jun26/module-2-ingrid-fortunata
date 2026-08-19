from marshmallow import Schema, fields, ValidationError, validates, validates_schema, validate
from app.schemas.product import ProductSchema


def not_blank(value):
    """Reject strings that are empty or whitespace-only."""
    if not value or not value.strip():
        raise ValidationError("Field cannot be blank or whitespace only.")


class CategorySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)


class CategoryWithProductsSchema(CategorySchema):
    products = fields.List(fields.Nested(ProductSchema), dump_only=True)


class CategoryCreateInputSchema(Schema):
    name = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=100), not_blank]
    )
    description = fields.Str(allow_none=True)
    is_active = fields.Bool(load_default=True)


class CategoryUpdateInputSchema(Schema):
    name = fields.Str(validate=[validate.Length(min=1, max=100), not_blank])
    description = fields.Str(allow_none=True)
    is_active = fields.Bool()

    @validates_schema
    def validate_not_empty(self, data, **kwargs):
        """Reject empty update bodies — at least one field must be provided."""
        if not data:
            raise ValidationError(
                {"_schema": ["At least one field must be provided to update."]}
            )


class CategoryGetResponseSchema(Schema):
    data = fields.Nested(CategorySchema, dump_only=True)


class CategoryWithProductsResponseSchema(Schema):
    data = fields.Nested(CategoryWithProductsSchema, dump_only=True)


class CategoryListResponseSchema(Schema):
    data = fields.List(fields.Nested(CategorySchema), dump_only=True)
