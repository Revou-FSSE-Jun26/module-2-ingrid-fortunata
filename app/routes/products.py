from flask_smorest import Blueprint
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.product import Product, ProductImage
from app.models.category import Category
from app.models.order import order_items
from app.auth import roles_required
from app.schemas import (
    ProductListResponseSchema,
    ProductCreateInputSchema,
    ProductUpdateInputSchema,
    ProductDetailResponseSchema,
)

products_bp = Blueprint('products', __name__, description='Operations on products')

@products_bp.route('/products', methods=['GET'])
@products_bp.response(200, ProductListResponseSchema)
def get_all_products():
    """Returns a paginated list of active products whose category is also active (or uncategorized) from the database.
    Supports optional filters: ?gender=Women&size=M&color=Black
    """
    # Subquery to select the base64 content of primary image
    primary_image_subquery = db.session.query(
        ProductImage.product_id,
        ProductImage.image_base64
    ).filter(
        ProductImage.is_primary == True
    ).subquery()

    # Build query (without .all() so paginate() can be applied)
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
    )

    # Fashion-specific filters
    gender = request.args.get('gender')
    if gender:
        products_query = products_query.filter(Product.gender == gender)

    size = request.args.get('size')
    if size:
        products_query = products_query.filter(Product.size == size)

    color = request.args.get('color')
    if color:
        products_query = products_query.filter(Product.color.ilike(f'%{color}%'))

    material = request.args.get('material')
    if material:
        products_query = products_query.filter(Product.material.ilike(f'%{material}%'))

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = products_query.paginate(page=page, per_page=per_page, error_out=False)

    data = []
    for prod, primary_image in pagination.items:
        d = prod.to_dict()
        d['primary_image'] = primary_image
        data.append(d)

    return jsonify({
        "data": data,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages
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
            "error_code": "PRODUCT_NOT_FOUND",
            "message": f"No product exists with ID {id}"
        }), 404
        
    prod_dict = product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in product.images]

    return jsonify({
        "data": prod_dict
    }), 200

@products_bp.route('/products', methods=['POST'])
@roles_required('superadmin', 'admin', 'seller')
@products_bp.arguments(ProductCreateInputSchema, location='json')
@products_bp.response(201, ProductDetailResponseSchema)
def create_product(product_data):
    """Create a new product with up to 3 images."""
    images_data = product_data.pop('images', [])

    if product_data.get('category_id'):
        if not db.session.get(Category, product_data['category_id']):
            return jsonify({
                "error_code": "CATEGORY_NOT_FOUND",
                "message": "Category not found."
            }), 400

    try:
        new_product = Product(**product_data)
        db.session.add(new_product)
        db.session.flush()  # Dapatkan new_product.id sebelum commit

        if images_data:
            if not any(img.get('is_primary') for img in images_data):
                images_data[0]['is_primary'] = True

            for img_obj in images_data:
                new_img = ProductImage(
                    product_id=new_product.id,
                    image_base64=img_obj['image_base64'],
                    is_primary=img_obj.get('is_primary', False)
                )
                db.session.add(new_img)

        db.session.commit()  # 1 commit atomik untuk product + images

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "PRODUCT_DATABASE_ERROR",
            "message": "An error occurred while creating the product."
        }), 500

    prod_dict = new_product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in new_product.images]

    return jsonify({
        "data": prod_dict
    }), 201

@products_bp.route('/products/<int:id>', methods=['PUT'])
@roles_required('superadmin', 'admin', 'seller')
@products_bp.arguments(ProductUpdateInputSchema, location='json')
@products_bp.response(200, ProductDetailResponseSchema)
def update_product(product_data, id):
    """Update a product and its images."""
    product = db.session.get(Product, id)
    if not product:
        return jsonify({
            "error_code": "PRODUCT_NOT_FOUND",
            "message": f"Product with ID {id} not found."
        }), 404

    if product_data.get('category_id'):
        if not db.session.get(Category, product_data['category_id']):
            return jsonify({
                "error_code": "CATEGORY_NOT_FOUND",
                "message": "Category not found."
            }), 400

    images_data = product_data.pop('images', None)

    try:
        for key, val in product_data.items():
            setattr(product, key, val)

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

        db.session.commit()  # 1 commit atomik untuk product + images

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "PRODUCT_DATABASE_ERROR",
            "message": "An error occurred while updating the product."
        }), 500

    prod_dict = product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in product.images]

    return jsonify({
        "data": prod_dict
    }), 200

@products_bp.route('/products/<int:id>', methods=['DELETE'])
@roles_required('superadmin', 'admin', 'seller')
def delete_product(id):
    """Delete a product, blocked if linked to any orders."""
    product = db.session.get(Product, id)
    if not product:
        return jsonify({
            "error_code": "PRODUCT_NOT_FOUND",
            "message": f"Product with ID {id} not found."
        }), 404

    has_orders = db.session.query(order_items).filter_by(product_id=id).first() is not None
    if has_orders:
        return jsonify({
            "error_code": "PRODUCT_CONFLICT",
            "message": "Cannot delete product because it is linked to existing orders."
        }), 409

    try:
        db.session.delete(product)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "PRODUCT_DATABASE_ERROR",
            "message": "An error occurred while deleting the product."
        }), 500

    return '', 204
