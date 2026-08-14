from marshmallow import Schema, fields, ValidationError, validates_schema, validate

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
    role = fields.Str(load_default="customer", validate=validate.OneOf(["superadmin", "admin", "seller", "customer"]))

    @validates_schema
    def validate_password_presence(self, data, **kwargs):
        if not data.get("password") and not data.get("password_hash"):
            raise ValidationError("Either 'password' or 'password_hash' must be provided.")

class UserRegisterResponseSchema(Schema):
    data = fields.Nested(UserSchema, dump_only=True)

class UserLoginInputSchema(Schema):
    username = fields.Str()
    email = fields.Str()
    password = fields.Str(required=True)

    @validates_schema
    def validate_identity_presence(self, data, **kwargs):
        if not data.get("username") and not data.get("email"):
            raise ValidationError("Either 'username' or 'email' must be provided.")

class UserGetResponseSchema(Schema):
    data = fields.Nested(UserSchema, dump_only=True)

class AuthLoginResponseDataSchema(Schema):
    token = fields.Str(dump_only=True)
    user = fields.Nested(UserSchema, dump_only=True)

class AuthLoginResponseSchema(Schema):
    data = fields.Nested(AuthLoginResponseDataSchema, dump_only=True)
