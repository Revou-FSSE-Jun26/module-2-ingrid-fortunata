from flask_smorest import Blueprint
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.order import Order, order_items
from app.models.product import Product
from app.models.user import User
from app.schemas import (
    OrderCreateInputSchema,
    OrderResponseWrapperSchema,
    OrderListResponseSchema,
    OrderUpdateStatusSchema,
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
            "error_code": "ORDER_VALIDATION_ERROR",
            "message": "Order must contain at least one item."
        }), 400

    total_amount = 0.00
    product_updates = []

    # Validate stock and compute totals
    for item in items:
        prod_id = item.get('product_id')
        qty = item.get('quantity')
        item_size = item.get('size')
        item_color = item.get('color')

        if qty is None or qty <= 0:
            return jsonify({
                "error_code": "ORDER_VALIDATION_ERROR",
                "message": "Quantity cannot be null, zero, or negative."
            }), 400

        product = db.session.get(Product, prod_id)
        if not product or not product.is_active:
            return jsonify({
                "error_code": "PRODUCT_NOT_FOUND",
                "message": f"Product with ID {prod_id} not found."
            }), 404

        if product.price is None or float(product.price) <= 0:
            return jsonify({
                "error_code": "PRODUCT_PRICE_VALIDATION_ERROR",
                "message": f"Price at purchase for product '{product.name}' cannot be null, zero, or negative."
            }), 400

        if product.stock is None or product.stock < qty:
            return jsonify({
                "error_code": "PRODUCT_STOCK_VALIDATION_ERROR",
                "message": f"Insufficient stock for product '{product.name}'."
            }), 400

        # Decrement stock
        product.stock -= qty
        total_amount += float(product.price) * qty
        product_updates.append((product, qty, item_size, item_color))

    try:
        # Create order
        new_order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status='pending',
            shipping_address=order_data.get('shipping_address'),
            recipient_name=order_data.get('recipient_name'),
            recipient_phone=order_data.get('recipient_phone')
        )
        db.session.add(new_order)
        db.session.flush()  # Dapatkan new_order.id tanpa commit dulu

        # Write order_items values
        for product, qty, item_size, item_color in product_updates:
            stmt = order_items.insert().values(
                order_id=new_order.id,
                product_id=product.id,
                quantity=qty,
                price_at_purchase=product.price,
                size=item_size,
                color=item_color
            )
            db.session.execute(stmt)

        db.session.commit()  # 1 commit atomik untuk order + items + stock

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "ORDER_DATABASE_ERROR",
            "message": "An error occurred while placing the order."
        }), 500

    # Get detailed representation
    detailed_items = []
    for product, qty, item_size, item_color in product_updates:
        detailed_items.append({
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "quantity": qty,
            "price_at_purchase": float(product.price),
            "size": item_size,
            "color": item_color
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
    """List orders. Admins/Sellers/Superadmins see all orders, customers see only their own.
    Supports optional pagination via ?page=&per_page= query params.
    If no pagination params are provided, all matching orders are returned.
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            "error_code": "USER_NOT_FOUND",
            "message": "User not found."
        }), 401

    if user.role in ['superadmin', 'admin', 'seller']:
        query = Order.query
    else:
        query = Order.query.filter_by(user_id=user_id)

    page = request.args.get('page', None, type=int)
    per_page = request.args.get('per_page', None, type=int)

    # Paginate only if at least one pagination param is explicitly provided
    if page is not None or per_page is not None:
        page = page or 1
        per_page = per_page or 10
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "data": [o.to_dict() for o in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }), 200

    # Default: fetch all
    orders = query.all()
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
            "error_code": "USER_NOT_FOUND",
            "message": "User not found."
        }), 401

    order = db.session.get(Order, id)
    is_admin = user.role in ['superadmin', 'admin', 'seller']
    if not order or (not is_admin and order.user_id != user_id):
        return jsonify({
            "error_code": "ORDER_NOT_FOUND",
            "message": f"Order with ID {id} not found."
        }), 404

    # Retrieve order items joined with product info
    items_query = db.session.query(
        order_items.c.product_id,
        order_items.c.quantity,
        order_items.c.price_at_purchase,
        order_items.c.size,
        order_items.c.color,
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
            "price_at_purchase": float(row.price_at_purchase),
            "size": row.size,
            "color": row.color
        })

    order_payload = order.to_dict()
    order_payload['items'] = detailed_items

    return jsonify({
        "data": order_payload
    }), 200

# Valid status transitions for each current status
STATUS_TRANSITIONS = {
    'pending':    ['paid', 'cancelled'],
    'paid':       ['processing', 'cancelled'],
    'processing': ['shipped'],
    'shipped':    ['delivered'],
    'delivered':  [],
    'cancelled':  [],
}

# Statuses that customers are allowed to trigger themselves
CUSTOMER_ALLOWED_TRANSITIONS = {
    'pending': ['paid', 'cancelled'],
    'paid':    ['cancelled'],
}

@orders_bp.route('/orders/<int:id>', methods=['PATCH'])
@jwt_required()
@orders_bp.arguments(OrderUpdateStatusSchema, location='json')
@orders_bp.response(200, OrderResponseWrapperSchema)
def update_order_status(update_data, id):
    """Update the status of an order with valid transition enforcement.
    
    Status lifecycle: pending → paid → processing → shipped → delivered
    Cancellation (→ cancelled) is only allowed from 'pending' or 'paid'.
    Customers can only transition: pending→paid, pending→cancelled, paid→cancelled.
    Admins/Sellers/Superadmins can perform any valid transition.
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            "error_code": "USER_NOT_FOUND",
            "message": "User not found."
        }), 401

    order = db.session.get(Order, id)
    is_admin = user.role in ['superadmin', 'admin', 'seller']
    if not order or (not is_admin and order.user_id != user_id):
        return jsonify({
            "error_code": "ORDER_NOT_FOUND",
            "message": f"Order with ID {id} not found."
        }), 404

    new_status = update_data['status']
    current_status = order.status

    # No-op: already on requested status
    if current_status == new_status:
        return jsonify({
            "error_code": "ORDER_STATUS_NO_CHANGE",
            "message": f"Order is already in '{current_status}' status."
        }), 409

    # Check if the transition is globally valid
    allowed_next = STATUS_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        return jsonify({
            "error_code": "ORDER_INVALID_TRANSITION",
            "message": f"Cannot transition order from '{current_status}' to '{new_status}'. "
                       f"Allowed next status(es): {allowed_next if allowed_next else 'none'}."
        }), 409

    # Role-based restriction: customers have limited transitions
    if not is_admin:
        customer_allowed = CUSTOMER_ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in customer_allowed:
            return jsonify({
                "error_code": "ORDER_FORBIDDEN_TRANSITION",
                "message": f"Customers cannot change order status from '{current_status}' to '{new_status}'."
            }), 403

    try:
        # If transitioning to cancelled, restore stock for all items first
        if new_status == 'cancelled':
            items_to_restore = db.session.execute(
                order_items.select().where(order_items.c.order_id == id)
            ).fetchall()
            for item in items_to_restore:
                product = db.session.get(Product, item.product_id)
                if product:
                    product.stock += item.quantity

        order.status = new_status
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "ORDER_DATABASE_ERROR",
            "message": "An error occurred while updating the order status."
        }), 500

    # Build response with items
    items_query = db.session.query(
        order_items.c.product_id,
        order_items.c.quantity,
        order_items.c.price_at_purchase,
        order_items.c.size,
        order_items.c.color,
        Product.name,
        Product.description
    ).join(
        Product, order_items.c.product_id == Product.id
    ).filter(
        order_items.c.order_id == id
    ).all()

    detailed_items = [{
        "product_id": row.product_id,
        "name": row.name,
        "description": row.description,
        "quantity": row.quantity,
        "price_at_purchase": float(row.price_at_purchase),
        "size": row.size,
        "color": row.color
    } for row in items_query]

    order_payload = order.to_dict()
    order_payload['items'] = detailed_items

    return jsonify({"data": order_payload}), 200

# Statuses that are still cancellable
CANCELLABLE_STATUSES = {'pending', 'paid'}

@orders_bp.route('/orders/<int:id>', methods=['DELETE'])
@jwt_required()
@orders_bp.response(200, OrderResponseWrapperSchema)
def delete_order(id):
    """Soft-cancel an order. Only orders with status 'pending' or 'paid' can be cancelled.
    Admins/Sellers/Superadmins can cancel any eligible order, customers only their own.
    Cancelled orders will have their product stock restored. Order history is preserved.
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({
            "error_code": "USER_NOT_FOUND",
            "message": "User not found."
        }), 401

    order = db.session.get(Order, id)
    is_admin = user.role in ['superadmin', 'admin', 'seller']
    if not order or (not is_admin and order.user_id != user_id):
        return jsonify({
            "error_code": "ORDER_NOT_FOUND",
            "message": f"Order with ID {id} not found."
        }), 404

    # Validate order status before cancellation
    if order.status not in CANCELLABLE_STATUSES:
        return jsonify({
            "error_code": "ORDER_CANNOT_BE_CANCELLED",
            "message": f"Order with status '{order.status}' cannot be cancelled. "
                       f"Only orders with status 'pending' or 'paid' can be cancelled."
        }), 409

    try:
        # Restore stock for each item in the order
        items_to_restore = db.session.execute(
            order_items.select().where(order_items.c.order_id == id)
        ).fetchall()

        for item in items_to_restore:
            product = db.session.get(Product, item.product_id)
            if product:
                product.stock += item.quantity

        # Soft-cancel: mark as cancelled, preserve the row and all history
        order.status = 'cancelled'
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "ORDER_DATABASE_ERROR",
            "message": "An error occurred while cancelling the order."
        }), 500

    # Build response with items
    items_query = db.session.query(
        order_items.c.product_id,
        order_items.c.quantity,
        order_items.c.price_at_purchase,
        order_items.c.size,
        order_items.c.color,
        Product.name,
        Product.description
    ).join(
        Product, order_items.c.product_id == Product.id
    ).filter(
        order_items.c.order_id == id
    ).all()

    detailed_items = [{
        "product_id": row.product_id,
        "name": row.name,
        "description": row.description,
        "quantity": row.quantity,
        "price_at_purchase": float(row.price_at_purchase),
        "size": row.size,
        "color": row.color
    } for row in items_query]

    order_payload = order.to_dict()
    order_payload['items'] = detailed_items

    return jsonify({"data": order_payload}), 200
