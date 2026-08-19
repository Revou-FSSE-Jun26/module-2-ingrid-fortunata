from decimal import Decimal, ROUND_HALF_UP
from app.models.product import Product
from app.errors import error_response, conflict_response, forbidden_response

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

# Statuses that are cancellable
CANCELLABLE_STATUSES = {'pending', 'paid'}


def validate_and_lock_order_items(items: list):
    """Validates order items against database stock and price rules with pessimistic row locking.

    Returns:
        tuple: (product_updates, total_amount, None) on success, or (None, None, error_response_tuple) on error.
    """
    total_amount = Decimal('0.00')
    product_updates = []

    for item in items:
        prod_id = item.get('product_id')
        qty = item.get('quantity')

        # Pessimistic row-level lock to prevent concurrent overselling
        product = Product.query.filter_by(id=prod_id).with_for_update().first()
        if not product or not product.is_active:
            return None, None, error_response(
                "PRODUCT_NOT_FOUND",
                f"Product with ID {prod_id} not found or is inactive.",
                404
            )

        if product.price is None or float(product.price) <= 0:
            return None, None, error_response(
                "PRODUCT_PRICE_VALIDATION_ERROR",
                f"Price for product '{product.name}' is invalid (zero or negative).",
                400
            )

        if product.stock is None or product.stock < qty:
            return None, None, error_response(
                "PRODUCT_STOCK_VALIDATION_ERROR",
                f"Insufficient stock for product '{product.name}'. Requested: {qty}, Available: {product.stock or 0}.",
                400
            )

        # Sync size and color with product defaults if not explicitly provided
        item_size = item.get('size') or product.size or 'Free Size'
        item_color = item.get('color') or product.color

        # Decrement stock and calculate exact decimal total
        product.stock -= qty
        item_unit_price = Decimal(str(product.price))
        item_subtotal = (item_unit_price * Decimal(qty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_amount += item_subtotal

        product_updates.append((product, qty, item_size, item_color))

    return product_updates, total_amount, None


def validate_order_status_transition(current_status: str, new_status: str, is_admin: bool):
    """Validates if an order status change is permitted based on workflow rules and user role.

    Returns:
        tuple: None if valid, or error_response_tuple if transition is invalid.
    """
    if current_status == new_status:
        return conflict_response(
            "ORDER_STATUS_NO_CHANGE",
            f"Order is already in '{current_status}' status."
        )

    allowed_next = STATUS_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        return conflict_response(
            "ORDER_INVALID_TRANSITION",
            f"Cannot transition order from '{current_status}' to '{new_status}'. "
            f"Allowed next status(es): {allowed_next if allowed_next else 'none'}."
        )

    if not is_admin:
        customer_allowed = CUSTOMER_ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in customer_allowed:
            return forbidden_response(
                f"Customers cannot change order status from '{current_status}' to '{new_status}'."
            )

    return None


def validate_order_cancellation(current_status: str):
    """Validates if an order is eligible for cancellation.

    Returns:
        tuple: None if eligible, or error_response_tuple if cannot be cancelled.
    """
    if current_status not in CANCELLABLE_STATUSES:
        return conflict_response(
            "ORDER_CANNOT_BE_CANCELLED",
            f"Order with status '{current_status}' cannot be cancelled. "
            "Only orders with status 'pending' or 'paid' can be cancelled."
        )

    return None
