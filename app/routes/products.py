from flask_smorest import Blueprint
from flask import jsonify
from app.extensions import db
from app.models.product import Product, ProductImage
from app.models.category import Category
from app.models.order import order_items
from app.schemas import (
    ProductListResponseSchema,
    ProductGetResponseSchema,
    ProductCreateInputSchema,
    ProductUpdateInputSchema,
    ProductDetailResponseSchema,
)

products_bp = Blueprint('products', __name__, description='Operations on products')

@products_bp.route('/products', methods=['GET'])
@products_bp.response(200, ProductListResponseSchema)
def get_all_products():
    """Returns the list of active products whose category is also active (or uncategorized) from the database."""
    # Subquery to select the base64 content of primary image
    primary_image_subquery = db.session.query(
        ProductImage.product_id,
        ProductImage.image_base64
    ).filter(
        ProductImage.is_primary == True
    ).subquery()

    # Query products joined with primary images
    products_query = db.session.query(
        Product,
        primary_image_subquery.c.image_base64.label('primary_image')
    ).join(
        Category, Product.category_id == Category.id, isouter=True
    ).outerjoin(
        primary_image_subquery, Product.id == primary_image_subquery.c.product_id
    ).filter(
        Product.is_active == True,
        (Category.id == None) | (Category.is_active == True)
    ).all()

    data = []
    for prod, primary_image in products_query:
        d = prod.to_dict()
        d['primary_image'] = primary_image
        data.append(d)

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data)
    }), 200

@products_bp.route('/products/<int:id>', methods=['GET'])
@products_bp.response(200, ProductDetailResponseSchema)
def get_product_by_id(id):
    """Retrieves a single active product by ID from the database along with all images."""
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
        
    prod_dict = product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in product.images]

    return jsonify({
        "success": True,
        "data": prod_dict
    }), 200

@products_bp.route('/products', methods=['POST'])
@products_bp.arguments(ProductCreateInputSchema, location='json')
@products_bp.response(201, ProductDetailResponseSchema)
def create_product(product_data):
    """Create a new product with up to 3 images."""
    images_data = product_data.pop('images', [])

    if product_data.get('category_id'):
        if not db.session.get(Category, product_data['category_id']):
            return jsonify({
                "success": False,
                "error": "Validation Error",
                "message": "Category not found."
            }), 400

    new_product = Product(**product_data)
    db.session.add(new_product)
    db.session.commit()

    if images_data:
        # Default the first image to primary if none is selected
        if not any(img.get('is_primary') for img in images_data):
            images_data[0]['is_primary'] = True

        for img_obj in images_data:
            new_img = ProductImage(
                product_id=new_product.id,
                image_base64=img_obj['image_base64'],
                is_primary=img_obj.get('is_primary', False)
            )
            db.session.add(new_img)
        db.session.commit()

    prod_dict = new_product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in new_product.images]

    return jsonify({
        "success": True,
        "message": "Product created successfully",
        "data": prod_dict
    }), 201

@products_bp.route('/products/<int:id>', methods=['PUT'])
@products_bp.arguments(ProductUpdateInputSchema, location='json')
@products_bp.response(200, ProductDetailResponseSchema)
def update_product(product_data, id):
    """Update a product and its images."""
    product = db.session.get(Product, id)
    if not product:
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": f"Product with ID {id} not found."
          }), 404

    if product_data.get('category_id'):
        if not db.session.get(Category, product_data['category_id']):
            return jsonify({
                "success": False,
                "error": "Validation Error",
                "message": "Category not found."
            }), 400

    images_data = product_data.pop('images', None)

    for key, val in product_data.items():
        setattr(product, key, val)
    db.session.commit()

    if images_data is not None:
        ProductImage.query.filter_by(product_id=id).delete()
        if images_data:
            if not any(img.get('is_primary') for img in images_data):
                images_data[0]['is_primary'] = True

            for img_obj in images_data:
                new_img = ProductImage(
                    product_id=id,
                    image_base64=img_obj['image_base64'],
                    is_primary=img_obj.get('is_primary', False)
                )
                db.session.add(new_img)
        db.session.commit()

    prod_dict = product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in product.images]

    return jsonify({
        "success": True,
        "message": "Product updated successfully",
        "data": prod_dict
    }), 200

@products_bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    """Delete a product, blocked if linked to any orders."""
    product = db.session.get(Product, id)
    if not product:
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": f"Product with ID {id} not found."
        }), 404

    has_orders = db.session.query(order_items).filter_by(product_id=id).first() is not None
    if has_orders:
        return jsonify({
            "success": False,
            "error": "Conflict",
            "message": "Cannot delete product because it is linked to existing orders."
        }), 400

    db.session.delete(product)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Product deleted successfully"
    }), 200
