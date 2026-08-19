import secrets
from datetime import datetime, timezone
from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    size = db.Column(db.String(20), nullable=False, default='Free Size', server_default='Free Size')
    color = db.Column(db.String(50), nullable=False)
    material = db.Column(db.String(150), nullable=True)
    gender = db.Column(db.String(20), nullable=False, default='Unisex', server_default='Unisex')
    sku = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, server_default='true', nullable=False)

    images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan', lazy=True)

    @staticmethod
    def generate_unique_sku() -> str:
        """Generates a random unique SKU code with prefix UQ-."""
        while True:
            sku_candidate = f"UQ-{secrets.token_hex(4).upper()}"
            if not Product.query.filter_by(sku=sku_candidate).first():
                return sku_candidate

    def to_detail_dict(self) -> dict:
        """Returns product representation including all associated image payloads."""
        d = self.to_dict()
        d['images'] = [img.to_dict() for img in self.images]
        return d

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price is not None else 0.0,
            'stock': self.stock,
            'size': self.size,
            'color': self.color,
            'material': self.material,
            'gender': self.gender,
            'sku': self.sku,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProductImage(db.Model):
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    image_base64 = db.Column(db.Text, nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'image_base64': self.image_base64,
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
