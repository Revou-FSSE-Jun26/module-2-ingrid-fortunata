from flask import Blueprint, jsonify
from app.models.product import Product
from app.models.category import Category

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_all_products():
    """Returns the list of active products whose category is also active (or uncategorized) from the database."""
    products = Product.query.join(
        Category, Product.category_id == Category.id, isouter=True
    ).filter(
        Product.is_active == True,
        (Category.id == None) | (Category.is_active == True)
    ).all()
    
    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in products],
        "count": len(products)
    }), 200

@products_bp.route('/products/<int:id>', methods=['GET'])
def get_product_by_id(id):
    """Retrieves a single active product by ID from the database, or returns 404 if not found or inactive."""
    product = Product.query.join(
        Category, Product.category_id == Category.id, isouter=True
    ).filter(
        Product.id == id,
        Product.is_active == True,
        (Category.id == None) | (Category.is_active == True)
    ).first()

    if not product:
        return jsonify({
            "success": False,
            "error": "Product not found",
            "message": f"No product exists with ID {id}"
        }), 404
        
    return jsonify({
        "success": True,
        "data": product.to_dict()
    }), 200
