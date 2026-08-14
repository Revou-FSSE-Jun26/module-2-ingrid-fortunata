from flask_smorest import Blueprint
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.order import Order, order_items
from app.models.product import Product
from app.models.user import User
from app.schemas import (
    OrderCreateInputSchema,
    OrderResponseWrapperSchema,
    OrderListResponseSchema,
)

orders_bp = Blueprint('orders', __name__, description='Operations on orders')

@orders_bp.route('/orders', methods=['POST'])
@jwt_required()
@orders_bp.arguments(OrderCreateInputSchema, location='json')
@orders_bp.response(201, OrderResponseWrapperSchema)
def create_order(order_data):
    """Place a new order linked to the logged-in user."""
    user_id = int(get_jwt_identity())
    items = order_data.get('items', [])

    if not items:
        return jsonify({
            "error_code": "VALIDATION_ERROR",
            "message": "Order must contain at least one item."
        }), 400

    total_amount = 0.00
    product_updates = []

    # Validate stock and compute totals
    for item in items:
        prod_id = item.get('product_id')
        qty = item.get('quantity')
        if qty is None or qty <= 0:
            return jsonify({
                "error_code": "VALIDATION_ERROR",
                "message": "Quantity cannot be null, zero, or negative."
            }), 400

        product = db.session.get(Product, prod_id)
        if not product or not product.is_active:
            return jsonify({
                "error_code": "NOT_FOUND",
                "message": f"Product with ID {prod_id} not found."
            }), 404

        if product.price is None or float(product.price) <= 0:
            return jsonify({
                "error_code": "VALIDATION_ERROR",
                "message": f"Price at purchase for product '{product.name}' cannot be null, zero, or negative."
            }), 400

        if product.stock is None or product.stock < qty:
            return jsonify({
                "error_code": "BAD_REQUEST",
                "message": f"Insufficient stock for product '{product.name}'."
            }), 400

        # Decrement stock
        product.stock -= qty
        total_amount += float(product.price) * qty
        product_updates.append((product, qty))

    # Create order
    new_order = Order(
        user_id=user_id,
        total_amount=total_amount,
        status='pending'
    )
    db.session.add(new_order)
    db.session.commit()

    # Write order_items values
    for product, qty in product_updates:
        stmt = order_items.insert().values(
            order_id=new_order.id,
            product_id=product.id,
            quantity=qty,
            price_at_purchase=product.price
        )
        db.session.execute(stmt)

    db.session.commit()

    # Get detailed representation
    detailed_items = []
    for product, qty in product_updates:
        detailed_items.append({
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "quantity": qty,
            "price_at_purchase": float(product.price)
        })

    order_payload = new_order.to_dict()
    order_payload['items'] = detailed_items

    return jsonify({
        "data": order_payload
    }), 201

@orders_bp.route('/orders', methods=['GET'])
@jwt_required()
@orders_bp.response(200, OrderListResponseSchema)
def get_orders():
    """List all orders. Admins/Sellers/Superadmins see all orders, customers see only their own."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            "error_code": "UNAUTHORIZED",
            "message": "User not found."
        }), 401

    if user.role in ['superadmin', 'admin', 'seller']:
        orders = Order.query.all()
    else:
        orders = Order.query.filter_by(user_id=user_id).all()
        
    return jsonify({
        "data": [o.to_dict() for o in orders]
    }), 200

@orders_bp.route('/orders/<int:id>', methods=['GET'])
@jwt_required()
@orders_bp.response(200, OrderResponseWrapperSchema)
def get_order_by_id(id):
    """View a specific order. Admins/Sellers/Superadmins can view any order, customers only their own."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            "error_code": "UNAUTHORIZED",
            "message": "User not found."
        }), 401

    order = db.session.get(Order, id)
    if not order or (user.role == 'customer' and order.user_id != user_id):
        return jsonify({
            "error_code": "NOT_FOUND",
            "message": f"Order with ID {id} not found."
        }), 404

    # Retrieve order items joined with product info
    items_query = db.session.query(
        order_items.c.product_id,
        order_items.c.quantity,
        order_items.c.price_at_purchase,
        Product.name,
        Product.description
    ).join(
        Product, order_items.c.product_id == Product.id
    ).filter(
        order_items.c.order_id == id
    ).all()

    detailed_items = []
    for row in items_query:
        detailed_items.append({
            "product_id": row.product_id,
            "name": row.name,
            "description": row.description,
            "quantity": row.quantity,
            "price_at_purchase": float(row.price_at_purchase)
        })

    order_payload = order.to_dict()
    order_payload['items'] = detailed_items

    return jsonify({
        "data": order_payload
    }), 200

@orders_bp.route('/orders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_order(id):
    """Delete an order. Admins/Sellers/Superadmins can cancel any order, customers only their own."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            "error_code": "UNAUTHORIZED",
            "message": "User not found."
        }), 401

    order = db.session.get(Order, id)
    if not order or (user.role == 'customer' and order.user_id != user_id):
        return jsonify({
            "error_code": "NOT_FOUND",
            "message": f"Order with ID {id} not found."
        }), 404

    # Delete order_items first due to RESTRICT constraint
    db.session.execute(order_items.delete().where(order_items.c.order_id == id))
    db.session.delete(order)
    db.session.commit()

    return '', 204

