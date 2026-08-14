from marshmallow import Schema, fields, ValidationError, validates_schema

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    role = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

class UserRegisterInputSchema(Schema):
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(load_only=True)
    password_hash = fields.Str(load_only=True)
    role = fields.Str(load_default="user")

    @validates_schema
    def validate_password_presence(self, data, **kwargs):
        if not data.get("password") and not data.get("password_hash"):
            raise ValidationError("Either 'password' or 'password_hash' must be provided.")

class UserRegisterResponseSchema(Schema):
    success = fields.Bool(dump_only=True)
    message = fields.Str(dump_only=True)
    data = fields.Nested(UserSchema, dump_only=True)

class UserLoginInputSchema(Schema):
    username = fields.Str()
    email = fields.Str()
    password = fields.Str(required=True)

    @validates_schema
    def validate_identity_presence(self, data, **kwargs):
        if not data.get("username") and not data.get("email"):
            raise ValidationError("Either 'username' or 'email' must be provided.")

class UserLoginResponseSchema(Schema):
    success = fields.Bool(dump_only=True)
    message = fields.Str(dump_only=True)
    data = fields.Nested(UserSchema, dump_only=True)

class UserGetResponseSchema(Schema):
    success = fields.Bool(dump_only=True)
    data = fields.Nested(UserSchema, dump_only=True)

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
