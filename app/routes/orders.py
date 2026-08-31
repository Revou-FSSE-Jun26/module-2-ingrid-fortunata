import logging
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

logger = logging.getLogger(__name__)

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
@orders_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
@orders_bp.arguments(OrderCreateInputSchema, location='json')
@orders_bp.response(201, OrderResponseWrapperSchema)
def create_order(order_data):
    """Place a new order linked to the logged-in user."""
    user = get_current_user()
    if not user:
        logger.warning("Order creation failed — unauthorized access")
        return unauthorized_response("Authenticated user not found.")

    items = order_data.get('items', [])
    logger.info("POST /orders — user_id=%s checkout %d items", user.id, len(items))

    product_updates, total_amount, err = validate_and_lock_order_items(items)
    if err:
        logger.warning("Order placement validation failed for user_id=%s", user.id)
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
        logger.info("Order placed successfully — order_id=%d, user_id=%d, total=%.2f", new_order.id, user.id, new_order.total_amount)

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error creating order for user_id=%s: %s", user.id, e, exc_info=True)
        return error_response("ORDER_DATABASE_ERROR", "An error occurred while placing the order.", 500)

    return jsonify({"data": new_order.to_detail_dict()}), 201


@orders_bp.route('/orders', methods=['GET'])
@orders_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
@orders_bp.response(200, OrderListResponseSchema)
def get_orders():
    """List orders.
    Admins/Superadmins see all orders; customers see only their own.
    Supports optional pagination via ?page=&per_page= (max per_page=100).
    """
    user = get_current_user()
    if not user:
        logger.warning("GET /orders failed — unauthorized")
        return unauthorized_response("Authenticated user not found.")

    is_admin = user.role in ['superadmin', 'admin']
    logger.info("GET /orders — user_id=%s, is_admin=%s", user.id, is_admin)

    query = build_filtered_orders_query(user, request.args)
    page, per_page = get_page_params()

    if page is not None:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        logger.debug("Returning %d paginated orders for user_id=%s", len(pagination.items), user.id)
        return jsonify({
            "data": [o.to_dict() for o in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }), 200

    orders = query.all()
    logger.debug("Returning %d orders for user_id=%s", len(orders), user.id)
    return jsonify({
        "data": [o.to_dict() for o in orders]
    }), 200


@orders_bp.route('/orders/<int:id>', methods=['GET'])
@orders_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
@orders_bp.response(200, OrderResponseWrapperSchema)
def get_order_by_id(id):
    """View a specific order. Admins/Superadmins can view any order; customers only their own."""
    user = get_current_user()
    if not user:
        return unauthorized_response("Authenticated user not found.")

    logger.info("GET /orders/%d — requested by user_id=%s", id, user.id)
    order = db.session.get(Order, id)
    is_admin = user.role in ['superadmin', 'admin']
    if not order or (not is_admin and order.user_id != user.id):
        logger.warning("Order not found or access forbidden: id=%d, user_id=%s", id, user.id)
        return not_found_response("Order", id)

    return jsonify({"data": order.to_detail_dict()}), 200


@orders_bp.route('/orders/<int:id>', methods=['PATCH'])
@orders_bp.doc(security=[{"BearerAuth": []}])
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
        logger.warning("Update status failed — Order not found: id=%d, user_id=%s", id, user.id)
        return not_found_response("Order", id)

    new_status = update_data['status']
    current_status = order.status
    logger.info("PATCH /orders/%d — status transition '%s' -> '%s' (user_id=%s, is_admin=%s)", id, current_status, new_status, user.id, is_admin)

    err = validate_order_status_transition(current_status, new_status, is_admin)
    if err:
        logger.warning("Invalid status transition for order_id=%d: '%s' -> '%s'", id, current_status, new_status)
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
        logger.info("Order status updated successfully — order_id=%d, new_status='%s'", id, new_status)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error updating status for order_id=%d: %s", id, e, exc_info=True)
        return error_response("ORDER_DATABASE_ERROR", "An error occurred while updating the order status.", 500)

    return jsonify({"data": order.to_detail_dict()}), 200


@orders_bp.route('/orders/<int:id>', methods=['DELETE'])
@orders_bp.doc(security=[{"BearerAuth": []}])
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

    logger.info("DELETE /orders/%d — cancellation requested by user_id=%s", id, user.id)
    order = db.session.get(Order, id)
    is_admin = user.role in ['superadmin', 'admin']
    if not order or (not is_admin and order.user_id != user.id):
        logger.warning("Cancel order failed — Order not found: id=%d, user_id=%s", id, user.id)
        return not_found_response("Order", id)

    err = validate_order_cancellation(order.status)
    if err:
        logger.warning("Cancel order blocked for id=%d — current status '%s'", id, order.status)
        return err

    body = request.get_json(silent=True) or {}
    cancellation_reason = body.get('cancellation_reason') or request.args.get('cancellation_reason')
    if not cancellation_reason or not str(cancellation_reason).strip():
        logger.warning("Cancel order failed — missing cancellation_reason for id=%d", id)
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
        logger.info("Order cancelled successfully — id=%d", id)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error cancelling order id=%d: %s", id, e, exc_info=True)
        return error_response("ORDER_DATABASE_ERROR", "An error occurred while cancelling the order.", 500)

    return jsonify({"data": order.to_detail_dict()}), 200

