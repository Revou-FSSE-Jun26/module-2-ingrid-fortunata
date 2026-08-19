from app.extensions import db
from app.models.category import Category
from app.models.order import Order, order_items
from app.errors import error_response, not_found_response, conflict_response


def validate_product_category(category_id: int):
    """Validates that a category exists and is active before assigning to a product.

    Returns:
        tuple: (category, None) if valid, or (None, error_response_tuple) if invalid.
    """
    if not category_id:
        return None, None

    category = db.session.get(Category, category_id)
    if not category:
        return None, not_found_response("Category")

    if not category.is_active:
        return None, error_response("CATEGORY_INACTIVE", "Cannot assign product to an inactive category.", 400)

    return category, None


def validate_product_deletion(product_id: int):
    """Validates whether a product can be deleted or soft-deleted based on order history.

    Returns:
        tuple: (has_any_orders: bool, error_response_tuple: optional)
    """
    # Check for active in-progress orders
    active_orders_count = db.session.query(order_items).join(
        Order, order_items.c.order_id == Order.id
    ).filter(
        order_items.c.product_id == product_id,
        Order.status.in_(['pending', 'paid', 'processing', 'shipped'])
    ).count()

    if active_orders_count > 0:
        return False, conflict_response(
            "PRODUCT_CONFLICT",
            f"Cannot delete product because it is linked to {active_orders_count} active in-progress order(s). "
            "Complete or cancel those orders first."
        )

    # Check if referenced in any historical completed/cancelled orders
    has_any_orders = db.session.query(order_items).filter_by(product_id=product_id).first() is not None

    return has_any_orders, None
