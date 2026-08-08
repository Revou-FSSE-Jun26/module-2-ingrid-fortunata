from flask import Blueprint, jsonify

products_bp = Blueprint('products', __name__)

# Hardcoded product data (warm-up for Checkpoint 2)
HARDCODED_PRODUCTS = [
    {
        "id": 1,
        "name": "Wireless Noise-Canceling Headphones",
        "description": "High-fidelity Bluetooth headphones with active noise cancellation",
        "price": 199.99,
        "stock": 45,
        "category_id": 1
    },
    {
        "id": 2,
        "name": "Ergonomic Mechanical Keyboard",
        "description": "Custom RGB mechanical keyboard with tactile switches",
        "price": 129.50,
        "stock": 30,
        "category_id": 1
    },
    {
        "id": 3,
        "name": "Organic Cotton Hoodie",
        "description": "Premium 100% organic cotton unisex pullover hoodie",
        "price": 59.99,
        "stock": 100,
        "category_id": 2
    },
    {
        "id": 4,
        "name": "Smart Fitness Watch",
        "description": "Water-resistant smartwatch with heart rate monitoring and GPS",
        "price": 149.00,
        "stock": 25,
        "category_id": 1
    }
]

@products_bp.route('/products', methods=['GET'])
def get_all_products():
    """Returns the full hardcoded list of products as JSON."""
    return jsonify({
        "success": True,
        "data": HARDCODED_PRODUCTS,
        "count": len(HARDCODED_PRODUCTS)
    }), 200

@products_bp.route('/products/<int:id>', methods=['GET'])
def get_product_by_id(id):
    """Retrieves a single hardcoded product by ID or returns 404 if not found."""
    product = next((p for p in HARDCODED_PRODUCTS if p["id"] == id), None)
    if not product:
        return jsonify({
            "success": False,
            "error": "Product not found",
            "message": f"No product exists with ID {id}"
        }), 404
        
    return jsonify({
        "success": True,
        "data": product
    }), 200
