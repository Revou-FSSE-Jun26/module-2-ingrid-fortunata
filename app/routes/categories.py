from flask_smorest import Blueprint
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import db
from app.models.category import Category
from app.models.product import Product
from app.auth import roles_required
from app.schemas import (
    CategoryCreateInputSchema,
    CategoryUpdateInputSchema,
    CategoryGetResponseSchema,
    CategoryWithProductsResponseSchema,
    CategoryListResponseSchema,
)

categories_bp = Blueprint('categories', __name__, description='Operations on categories')


@categories_bp.route('/categories', methods=['POST'])
@roles_required('superadmin', 'admin')
@categories_bp.arguments(CategoryCreateInputSchema, location='json')
@categories_bp.response(201, CategoryGetResponseSchema)
def create_category(category_data):
    """Create a new category."""
    name = category_data.get('name', '').strip()
    # Normalize name before uniqueness check
    category_data['name'] = name

    if Category.query.filter_by(name=name).first():
        return jsonify({
            "error_code": "CATEGORY_CONFLICT",
            "message": "Category name already exists."
        }), 409

    try:
        new_cat = Category(**category_data)
        db.session.add(new_cat)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error_code": "CATEGORY_CONFLICT",
            "message": "Category name already exists."
        }), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "CATEGORY_DATABASE_ERROR",
            "message": "An error occurred while creating the category."
        }), 500

    return jsonify({
        "data": new_cat.to_dict()
    }), 201


@categories_bp.route('/categories', methods=['GET'])
@categories_bp.response(200, CategoryListResponseSchema)
def get_categories():
    """List all categories."""
    categories = Category.query.all()
    return jsonify({
        "data": [c.to_dict() for c in categories]
    }), 200


@categories_bp.route('/categories/<int:id>', methods=['GET'])
@categories_bp.response(200, CategoryWithProductsResponseSchema)
def get_category_by_id(id):
    """Get a specific category along with its active products."""
    category = db.session.get(Category, id)
    if not category:
        return jsonify({
            "error_code": "CATEGORY_NOT_FOUND",
            "message": f"Category with ID {id} not found."
        }), 404

    cat_dict = category.to_dict()
    cat_dict['products'] = [p.to_dict() for p in category.products]
    return jsonify({
        "data": cat_dict
    }), 200


@categories_bp.route('/categories/<int:id>', methods=['PUT'])
@roles_required('superadmin', 'admin')
@categories_bp.arguments(CategoryUpdateInputSchema, location='json')
@categories_bp.response(200, CategoryGetResponseSchema)
def update_category(category_data, id):
    """Replace/update an entire category.
    Under RESTful PUT semantics, the client provides the full category representation to replace the existing resource.
    """
    category = db.session.get(Category, id)
    if not category:
        return jsonify({
            "error_code": "CATEGORY_NOT_FOUND",
            "message": f"Category with ID {id} not found."
        }), 404

    name = category_data.get('name')
    if name:
        name = name.strip()
        category_data['name'] = name
        if name != category.name:
            if Category.query.filter_by(name=name).first():
                return jsonify({
                    "error_code": "CATEGORY_CONFLICT",
                    "message": "Category name already exists."
                }), 409

    try:
        for key, val in category_data.items():
            setattr(category, key, val)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error_code": "CATEGORY_CONFLICT",
            "message": "Category name already exists."
        }), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "CATEGORY_DATABASE_ERROR",
            "message": "An error occurred while updating the category."
        }), 500

    return jsonify({
        "data": category.to_dict()
    }), 200


@categories_bp.route('/categories/<int:id>', methods=['DELETE'])
@roles_required('superadmin', 'admin')
def delete_category(id):
    """Delete a category.
    WARNING: Deleting a category will unlink (set category_id = NULL) all products that belong to it.
    Products themselves are NOT deleted — they become uncategorized.
    To prevent this, the endpoint blocks deletion if the category has active products.
    """
    category = db.session.get(Category, id)
    if not category:
        return jsonify({
            "error_code": "CATEGORY_NOT_FOUND",
            "message": f"Category with ID {id} not found."
        }), 404

    # Block deletion if active products are linked to this category
    active_product_count = Product.query.filter_by(
        category_id=id, is_active=True
    ).count()
    if active_product_count > 0:
        return jsonify({
            "error_code": "CATEGORY_CONFLICT",
            "message": (
                f"Cannot delete category because it has {active_product_count} active product(s) linked to it. "
                "Reassign or deactivate those products first."
            )
        }), 409

    try:
        db.session.delete(category)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "CATEGORY_DATABASE_ERROR",
            "message": "An error occurred while deleting the category."
        }), 500

    return '', 204
