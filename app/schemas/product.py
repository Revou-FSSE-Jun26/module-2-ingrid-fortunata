from marshmallow import Schema, fields, validates, ValidationError, validates_schema, validate

VALID_SIZES = ["XS", "S", "M", "L", "XL", "XXL", "FREE", "Free Size"]
VALID_GENDERS = ["Men", "Women", "Unisex", "Kids"]

class ProductImageSchema(Schema):
    id = fields.Int(dump_only=True)
    image_base64 = fields.Str(required=True)
    is_primary = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

class ProductImageInputSchema(Schema):
    image_base64 = fields.Str(required=True)
    is_primary = fields.Bool(load_default=False)

    @validates("image_base64")
    def validate_image_size(self, value, **kwargs):
        # Limit size to ~1MB (Base64 length ~1.37M chars)
        if len(value) > 1500000:
            raise ValidationError("Image size exceeds the 1MB limit.")

class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    category_id = fields.Int(allow_none=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    price = fields.Float(required=True)
    stock = fields.Int(required=True)
    size = fields.Str()
    color = fields.Str()
    material = fields.Str(allow_none=True)
    gender = fields.Str()
    sku = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ProductCreateInputSchema(Schema):
    category_id = fields.Int(allow_none=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(allow_none=True)
    price = fields.Float(required=True)
    stock = fields.Int(required=True)
    size = fields.Str(load_default="Free Size", validate=validate.OneOf(VALID_SIZES))
    color = fields.Str(required=True, validate=validate.Length(min=1))
    material = fields.Str(allow_none=True)
    gender = fields.Str(load_default="Unisex", validate=validate.OneOf(VALID_GENDERS))
    sku = fields.Str(allow_none=True)
    is_active = fields.Bool(load_default=True)
    images = fields.List(fields.Nested(ProductImageInputSchema), load_default=list)

    @validates("price")
    def validate_price(self, value, **kwargs):
        if value <= 0:
            raise ValidationError("Price must be greater than zero.")

    @validates("stock")
    def validate_stock(self, value, **kwargs):
        if value < 0:
            raise ValidationError("Stock cannot be negative.")

    @validates_schema
    def validate_images(self, data, **kwargs):
        imgs = data.get("images", [])
        if len(imgs) > 3:
            raise ValidationError("A product can have at most 3 images.")
        
        # Count primaries
        primaries = sum(1 for img in imgs if img.get("is_primary"))
        if len(imgs) > 0 and primaries > 1:
            raise ValidationError("Exactly one image can be flagged as primary.")

class ProductUpdateInputSchema(Schema):
    category_id = fields.Int(allow_none=True)
    name = fields.Str(validate=validate.Length(min=1))
    description = fields.Str(allow_none=True)
    price = fields.Float()
    stock = fields.Int()
    size = fields.Str(validate=validate.OneOf(VALID_SIZES))
    color = fields.Str(validate=validate.Length(min=1))
    material = fields.Str(allow_none=True)
    gender = fields.Str(validate=validate.OneOf(VALID_GENDERS))
    sku = fields.Str(allow_none=True)
    is_active = fields.Bool()
    images = fields.List(fields.Nested(ProductImageInputSchema))

    @validates("price")
    def validate_price(self, value, **kwargs):
        if value <= 0:
            raise ValidationError("Price must be greater than zero.")

    @validates("stock")
    def validate_stock(self, value, **kwargs):
        if value < 0:
            raise ValidationError("Stock cannot be negative.")

    @validates_schema
    def validate_images(self, data, **kwargs):
        imgs = data.get("images")
        if imgs is not None:
            if len(imgs) > 3:
                raise ValidationError("A product can have at most 3 images.")
            primaries = sum(1 for img in imgs if img.get("is_primary"))
            if len(imgs) > 0 and primaries > 1:
                raise ValidationError("Exactly one image can be flagged as primary.")

class ProductListSchema(ProductSchema):
    primary_image = fields.Str(dump_only=True)

class ProductListResponseSchema(Schema):
    data = fields.List(fields.Nested(ProductListSchema), dump_only=True)

class ProductGetResponseSchema(Schema):
    data = fields.Nested(ProductSchema, dump_only=True)

class ProductDetailSchema(ProductSchema):
    images = fields.List(fields.Nested(ProductImageSchema), dump_only=True)

class ProductDetailResponseSchema(Schema):
    data = fields.Nested(ProductDetailSchema, dump_only=True)
