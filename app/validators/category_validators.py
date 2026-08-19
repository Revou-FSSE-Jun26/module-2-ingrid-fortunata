from app.models.category import Category
from app.models.product import Product
from app.errors import conflict_response


def validate_category_name_unique(name: str, exclude_id: int = None):
    """Validates that a category name does not already exist (case-sensitive or normalized).

    Returns:
        tuple: None if valid, or error_response_tuple if conflict.
    """
    query = Category.query.filter_by(name=name)
    if exclude_id is not None:
        query = query.filter(Category.id != exclude_id)

    if query.first():
        return conflict_response("CATEGORY_CONFLICT", "Category name already exists.")

    return None


def validate_category_deletion(category_id: int):
    """Validates that a category can be deleted safely (no active products linked).

    Returns:
        tuple: None if deletion is safe, or error_response_tuple if blocked.
    """
    active_product_count = Product.query.filter_by(
        category_id=category_id, is_active=True
    ).count()

    if active_product_count > 0:
        return conflict_response(
            "CATEGORY_CONFLICT",
            f"Cannot delete category because it has {active_product_count} active product(s) linked to it. "
            "Reassign or deactivate those products first."
        )

    return None
