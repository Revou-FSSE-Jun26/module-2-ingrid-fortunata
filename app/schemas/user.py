from marshmallow import Schema, fields, ValidationError, validates, validates_schema, validate


def not_blank(value):
    """Reject strings that are empty or whitespace-only."""
    if not value or not value.strip():
        raise ValidationError("Field cannot be blank or whitespace only.")


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    role = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class UserRegisterInputSchema(Schema):
    username = fields.Str(required=True, validate=[validate.Length(min=1, max=50), not_blank])
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=[validate.Length(min=6), not_blank]
    )
    # role is intentionally NOT exposed — all public registrations default to 'customer'
    # role assignment is a privileged operation done separately by admins

    @validates("username")
    def validate_username_no_spaces(self, value, **kwargs):
        if " " in value:
            raise ValidationError("Username cannot contain spaces.")


class UserRegisterResponseSchema(Schema):
    data = fields.Nested(UserSchema, dump_only=True)


class UserLoginInputSchema(Schema):
    # Accept either username or email — use Str for username, Email for email
    username = fields.Str(validate=[validate.Length(min=1), not_blank])
    email = fields.Email()
    password = fields.Str(required=True, load_only=True, validate=[validate.Length(min=1), not_blank])

    @validates_schema
    def validate_identity_presence(self, data, **kwargs):
        if not data.get("username") and not data.get("email"):
            raise ValidationError(
                {"identity": ["Either 'username' or 'email' must be provided."]}
            )


class UserGetResponseSchema(Schema):
    data = fields.Nested(UserSchema, dump_only=True)


class AuthLoginResponseDataSchema(Schema):
    token = fields.Str(dump_only=True)
    user = fields.Nested(UserSchema, dump_only=True)


class AuthLoginResponseSchema(Schema):
    data = fields.Nested(AuthLoginResponseDataSchema, dump_only=True)
