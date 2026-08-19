from datetime import datetime, timezone
from app.extensions import db

# Association Table for Many-to-Many relationship between Orders and Products
order_items = db.Table(
    'order_items',
    db.metadata,
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id', ondelete='RESTRICT'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False, default=1),
    db.Column('price_at_purchase', db.Numeric(10, 2), nullable=False),
    db.Column('size', db.String(20), nullable=False, default='Free Size', server_default='Free Size'),
    db.Column('color', db.String(50), nullable=False)
)

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    status = db.Column(db.String(50), nullable=False, default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    recipient_name = db.Column(db.String(150), nullable=False)
    recipient_phone = db.Column(db.String(30), nullable=False)
    tracking_number = db.Column(db.String(100), nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


    # Many-to-Many relationship with Product
    products = db.relationship('Product', secondary=order_items, backref='orders', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount) if self.total_amount is not None else 0.0,
            'status': self.status,
            'shipping_address': self.shipping_address,
            'recipient_name': self.recipient_name,
            'recipient_phone': self.recipient_phone,
            'tracking_number': self.tracking_number,
            'cancellation_reason': self.cancellation_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
