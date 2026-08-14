from marshmallow import Schema, fields

class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    category_id = fields.Int(allow_none=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    price = fields.Float(required=True)
    stock = fields.Int(required=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ProductListResponseSchema(Schema):
    success = fields.Bool(dump_only=True)
    data = fields.List(fields.Nested(ProductSchema), dump_only=True)
    count = fields.Int(dump_only=True)

class ProductGetResponseSchema(Schema):
    success = fields.Bool(dump_only=True)
    data = fields.Nested(ProductSchema, dump_only=True)
