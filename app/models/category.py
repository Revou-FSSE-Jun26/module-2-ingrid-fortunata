from datetime import datetime, timezone
from app.extensions import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, server_default='true', nullable=False)


    # Relationship to Product
    products = db.relationship('Product', backref='category', lazy=True)

    def to_with_products_dict(self, is_admin: bool = False) -> dict:
        """Returns category dictionary including its products (filtered by active status for non-admins)."""
        d = self.to_dict()
        products = self.products if is_admin else [p for p in self.products if p.is_active]
        d['products'] = [p.to_dict() for p in products]
        return d

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

