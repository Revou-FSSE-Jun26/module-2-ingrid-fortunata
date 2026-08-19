from flask_smorest import Blueprint
from flask import jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.order import Order, order_items
from app.models.product import Product
from app.models.user import User
from app.auth import get_current_user
from app.errors import (
    error_response,
    not_found_response,
    unauthorized_response,
)
from app.validators import (
    validate_and_lock_order_items,
    validate_order_status_transition,
    validate_order_cancellation,
)
from app.schemas import (
    OrderCreateInputSchema,
    OrderResponseWrapperSchema,
    OrderListResponseSchema,
    OrderUpdateStatusSchema,
)
from app.utils.pagination import get_page_params

orders_bp = Blueprint('orders', __name__, description='Operations on orders')


def build_filtered_orders_query(user: User, args: dict):
    """Builds and applies role-based access and search/filter criteria on orders."""
    is_admin = user.role in ['superadmin', 'admin']
    query = Order.query if is_admin else Order.query.filter_by(user_id=user.id)

    # Optional status filter
    status = args.get('status')
    if status:
        query = query.filter(Order.status == status.strip().lower())

    # Categorized order tracking filters
    order_id = args.get('order_id', None, type=int)
    if order_id is not None:
        query = query.filter(Order.id == order_id)

    recipient_name = args.get('recipient_name')
    if recipient_name:
        query = query.filter(Order.recipient_name.ilike(f'%{recipient_name.strip()}%'))

    recipient_phone = args.get('recipient_phone')
    if recipient_phone:
        query = query.filter(Order.recipient_phone.ilike(f'%{recipient_phone.strip()}%'))

    shipping_address = args.get('shipping_address')
    if shipping_address:
        query = query.filter(Order.shipping_address.ilike(f'%{shipping_address.strip()}%'))

    customer_name = args.get('customer_name') or args.get('username')
    if customer_name and is_admin:
        query = query.join(User, Order.user_id == User.id).filter(
            db.or_(
                User.username.ilike(f'%{customer_name.strip()}%'),
                User.email.ilike(f'%{customer_name.strip()}%')
            )
        )

    # General search across all fields
    search = args.get('search')
    if search:
        search_term = f'%{search.strip()}%'
        search_filters = [
            Order.recipient_name.ilike(search_term),
            Order.recipient_phone.ilike(search_term),
            Order.shipping_address.ilike(search_term),
            db.cast(Order.id, db.String).ilike(search_term)
        ]
        if is_admin:
            query = query.join(User, Order.user_id == User.id)
            search_filters.extend([
                User.username.ilike(search_term),
                User.email.ilike(search_term)
            ])
        query = query.filter(db.or_(*search_filters))

    return query.order_by(Order.created_at.desc(), Order.id.desc())


@orders_bp.route('/orders', methods=['POST'])
@jwt_required()
@orders_bp.arguments(OrderCreateInputSchema, location='json')
@orders_bp.response(201, OrderResponseWrapperSchema)
def create_order(order_data):
    """Place a new order linked to the logged-in user."""
    user = get_current_user()
    if not user:
        return unauthorized_response("Authenticated user not found.")

    items = order_data.get('items', [])
    product_updates, total_amount, err = validate_and_lock_order_items(items)
    if err:
        return err

    try:
        new_order = Order(
            user_id=user.id,
            total_amount=float(total_amount),
            status='pending',
            shipping_address=order_data.get('shipping_address'),
            recipient_name=order_data.get('recipient_name'),
            recipient_phone=order_data.get('recipient_phone')
        )
        db.session.add(new_order)
        db.session.flush()

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

        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        return error_response("ORDER_DATABASE_ERROR", "An error occurred while placing the order.", 500)

    return jsonify({"data": new_order.to_detail_dict()}), 201


@orders_bp.route('/orders', methods=['GET'])
@jwt_required()
@orders_bp.response(200, OrderListResponseSchema)
def get_orders():
    """List orders.
    Admins/Superadmins see all orders; customers see only their own.
    Supports optional pagination via ?page=&per_page= (max per_page=100).
    """
    user = get_current_user()
    if not user:
        return unauthorized_response("Authenticated user not found.")

    query = build_filtered_orders_query(user, request.args)
    page, per_page = get_page_params()

    if page is not None:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "data": [o.to_dict() for o in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }), 200

    orders = query.all()
    return jsonify({
        "data": [o.to_dict() for o in orders]
    }), 200


@orders_bp.route('/orders/<int:id>', methods=['GET'])
@jwt_required()
@orders_bp.response(200, OrderResponseWrapperSchema)
def get_order_by_id(id):
    """View a specific order. Admins/Superadmins can view any order; customers only their own."""
    user = get_current_user()
    if not user:
        return unauthorized_response("Authenticated user not found.")

    order = db.session.get(Order, id)
    is_admin = user.role in ['superadmin', 'admin']
    if not order or (not is_admin and order.user_id != user.id):
        return not_found_response("Order", id)

    return jsonify({"data": order.to_detail_dict()}), 200


@orders_bp.route('/orders/<int:id>', methods=['PATCH'])
@jwt_required()
@orders_bp.arguments(OrderUpdateStatusSchema, location='json')
@orders_bp.response(200, OrderResponseWrapperSchema)
def update_order_status(update_data, id):
    """Update the status of an order with valid transition enforcement.

    Status lifecycle: pending → paid → processing → shipped → delivered
    Cancellation (→ cancelled) is only allowed from 'pending' or 'paid'.
    Customers can only transition: pending→paid, pending→cancelled, paid→cancelled.
    Admins/Superadmins can perform any valid transition.
    """
    user = get_current_user()
    if not user:
        return unauthorized_response("Authenticated user not found.")

    order = db.session.get(Order, id)
    is_admin = user.role in ['superadmin', 'admin']
    if not order or (not is_admin and order.user_id != user.id):
        return not_found_response("Order", id)

    new_status = update_data['status']
    current_status = order.status

    err = validate_order_status_transition(current_status, new_status, is_admin)
    if err:
        return err

    try:
        if new_status == 'shipped':
            order.tracking_number = update_data['tracking_number'].strip()

        if new_status == 'cancelled':
            order.cancellation_reason = update_data['cancellation_reason'].strip()
            items_to_restore = db.session.execute(
                order_items.select().where(order_items.c.order_id == id)
            ).fetchall()
            for item in items_to_restore:
                product = Product.query.filter_by(id=item.product_id).with_for_update().first()
                if product:
                    product.stock += item.quantity

        order.status = new_status
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error_response("ORDER_DATABASE_ERROR", "An error occurred while updating the order status.", 500)

    return jsonify({"data": order.to_detail_dict()}), 200


@orders_bp.route('/orders/<int:id>', methods=['DELETE'])
@jwt_required()
@orders_bp.response(200, OrderResponseWrapperSchema)
def delete_order(id):
    """Soft-cancel an order.
    Only orders with status 'pending' or 'paid' can be cancelled.
    Admins/Superadmins can cancel any eligible order; customers only their own.
    Cancelled orders require a cancellation_reason (via JSON body or query param).
    Stock is restored and order history is preserved.
    """
    user = get_current_user()
    if not user:
        return unauthorized_response("Authenticated user not found.")

    order = db.session.get(Order, id)
    is_admin = user.role in ['superadmin', 'admin']
    if not order or (not is_admin and order.user_id != user.id):
        return not_found_response("Order", id)

    err = validate_order_cancellation(order.status)
    if err:
        return err

    body = request.get_json(silent=True) or {}
    cancellation_reason = body.get('cancellation_reason') or request.args.get('cancellation_reason')
    if not cancellation_reason or not str(cancellation_reason).strip():
        return jsonify({
            "error_code": "VALIDATION_ERROR",
            "message": "cancellation_reason is required when cancelling an order.",
            "details": {
                "cancellation_reason": ["cancellation_reason is required when cancelling an order."]
            }
        }), 422

    try:
        items_to_restore = db.session.execute(
            order_items.select().where(order_items.c.order_id == id)
        ).fetchall()

        for item in items_to_restore:
            product = Product.query.filter_by(id=item.product_id).with_for_update().first()
            if product:
                product.stock += item.quantity

        order.status = 'cancelled'
        order.cancellation_reason = str(cancellation_reason).strip()
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error_response("ORDER_DATABASE_ERROR", "An error occurred while cancelling the order.", 500)

    return jsonify({"data": order.to_detail_dict()}), 200
