from marshmallow import Schema, fields, validates, ValidationError
from app.schemas.product import ProductSchema

class CategorySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

class CategoryWithProductsSchema(CategorySchema):
    products = fields.List(fields.Nested(ProductSchema), dump_only=True)

class CategoryCreateInputSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    is_active = fields.Bool(load_default=True)

class CategoryUpdateInputSchema(Schema):
    name = fields.Str()
    description = fields.Str(allow_none=True)
    is_active = fields.Bool()

class CategoryGetResponseSchema(Schema):
    data = fields.Nested(CategorySchema, dump_only=True)

class CategoryWithProductsResponseSchema(Schema):
    data = fields.Nested(CategoryWithProductsSchema, dump_only=True)

class CategoryListResponseSchema(Schema):
    data = fields.List(fields.Nested(CategorySchema), dump_only=True)
