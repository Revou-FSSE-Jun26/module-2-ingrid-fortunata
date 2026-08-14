from flask_smorest import Blueprint
from flask import jsonify
from app.extensions import db
from app.models.category import Category
from app.schemas import (
    CategoryCreateInputSchema,
    CategoryUpdateInputSchema,
    CategoryGetResponseSchema,
    CategoryWithProductsResponseSchema,
    CategoryListResponseSchema,
)

categories_bp = Blueprint('categories', __name__, description='Operations on categories')

@categories_bp.route('/categories', methods=['POST'])
@categories_bp.arguments(CategoryCreateInputSchema, location='json')
@categories_bp.response(201, CategoryGetResponseSchema)
def create_category(category_data):
    """Create a new category."""
    name = category_data.get('name')
    if Category.query.filter_by(name=name).first():
        return jsonify({
            "success": False,
            "error": "Conflict",
            "message": "Category name already exists."
        }), 400

    new_cat = Category(**category_data)
    db.session.add(new_cat)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Category created successfully",
        "data": new_cat.to_dict()
    }), 201

@categories_bp.route('/categories', methods=['GET'])
@categories_bp.response(200, CategoryListResponseSchema)
def get_categories():
    """List all categories."""
    categories = Category.query.all()
    return jsonify({
        "success": True,
        "data": [c.to_dict() for c in categories],
        "count": len(categories)
    }), 200

@categories_bp.route('/categories/<int:id>', methods=['GET'])
@categories_bp.response(200, CategoryWithProductsResponseSchema)
def get_category_by_id(id):
    """Get a specific category along with its products."""
    category = db.session.get(Category, id)
    if not category:
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": f"Category with ID {id} not found."
        }), 404

    # Build payload with products
    cat_dict = category.to_dict()
    cat_dict['products'] = [p.to_dict() for p in category.products]
    return jsonify({
        "success": True,
        "data": cat_dict
    }), 200

@categories_bp.route('/categories/<int:id>', methods=['PUT'])
@categories_bp.arguments(CategoryUpdateInputSchema, location='json')
@categories_bp.response(200, CategoryGetResponseSchema)
def update_category(category_data, id):
    """Update a category."""
    category = db.session.get(Category, id)
    if not category:
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": f"Category with ID {id} not found."
        }), 404

    name = category_data.get('name')
    if name and name != category.name:
        if Category.query.filter_by(name=name).first():
            return jsonify({
                "success": False,
                "error": "Conflict",
                "message": "Category name already exists."
            }), 400

    for key, val in category_data.items():
        setattr(category, key, val)

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Category updated successfully",
        "data": category.to_dict()
    }), 200

@categories_bp.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    """Delete a category."""
    category = db.session.get(Category, id)
    if not category:
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": f"Category with ID {id} not found."
        }), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Category deleted successfully"
    }), 200
