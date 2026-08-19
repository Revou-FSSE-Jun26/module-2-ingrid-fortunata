import secrets
from flask_smorest import Blueprint
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.product import Product, ProductImage
from app.models.category import Category
from app.models.order import Order, order_items
from app.auth import roles_required, is_admin_user
from app.schemas import (
    ProductListResponseSchema,
    ProductCreateInputSchema,
    ProductUpdateInputSchema,
    ProductDetailResponseSchema,
)

products_bp = Blueprint('products', __name__, description='Operations on products')

# Pagination defaults and limits
PAGE_DEFAULT = 1
PER_PAGE_DEFAULT = 10
PER_PAGE_MAX = 100


def generate_unique_sku():
    """Generates a random unique SKU code with prefix UQ-."""
    while True:
        sku_candidate = f"UQ-{secrets.token_hex(4).upper()}"
        if not Product.query.filter_by(sku=sku_candidate).first():
            return sku_candidate


def _safe_page_params():
    """Parse and clamp pagination query params. Returns (page, per_page) or (None, None)."""
    raw_page = request.args.get('page', None, type=int)
    raw_per_page = request.args.get('per_page', None, type=int)

    if raw_page is None and raw_per_page is None:
        return None, None

    page = max(PAGE_DEFAULT, raw_page) if raw_page is not None else PAGE_DEFAULT
    per_page = min(PER_PAGE_MAX, max(1, raw_per_page)) if raw_per_page is not None else PER_PAGE_DEFAULT
    return page, per_page


@products_bp.route('/products', methods=['GET'])
@products_bp.response(200, ProductListResponseSchema)
def get_all_products():
    """Returns a paginated list of active products whose category is also active (or uncategorized).
    Supports optional filters: ?gender=Women&size=M&color=Black
    Pagination: ?page=1&per_page=10 (max per_page=100)
    """
    # Subquery to select the base64 content of primary image
    primary_image_subquery = db.session.query(
        ProductImage.product_id,
        ProductImage.image_base64
    ).filter(
        ProductImage.is_primary == True
    ).subquery()

    is_admin = is_admin_user()

    # Build base query
    products_query = db.session.query(
        Product,
        primary_image_subquery.c.image_base64.label('primary_image')
    ).join(
        Category, Product.category_id == Category.id, isouter=True
    ).outerjoin(
        primary_image_subquery, Product.id == primary_image_subquery.c.product_id
    )

    if not is_admin:
        # Public / customer view: strictly active products in active (or uncategorized) categories
        products_query = products_query.filter(
            Product.is_active == True,
            (Category.id == None) | (Category.is_active == True)
        )
    else:
        # Admin / seller view: shows all by default, or filters by is_active query param
        is_active_param = request.args.get('is_active')
        if is_active_param is not None:
            if is_active_param.lower() == 'true':
                products_query = products_query.filter(Product.is_active == True)
            elif is_active_param.lower() == 'false':
                products_query = products_query.filter(Product.is_active == False)

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

    # Category filter
    category_id = request.args.get('category_id', None, type=int)
    if category_id is not None:
        products_query = products_query.filter(Product.category_id == category_id)

    # Price range filters
    min_price = request.args.get('min_price', None, type=float)
    if min_price is not None:
        products_query = products_query.filter(Product.price >= max(0.0, min_price))

    max_price = request.args.get('max_price', None, type=float)
    if max_price is not None:
        products_query = products_query.filter(Product.price <= max_price)

    # Free-text search across name and description
    search = request.args.get('search')
    if search:
        search_term = f'%{search}%'
        products_query = products_query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )

    # Sorting
    sort_by = request.args.get('sort_by')
    if sort_by == 'price_asc':
        products_query = products_query.order_by(Product.price.asc(), Product.id.asc())
    elif sort_by == 'price_desc':
        products_query = products_query.order_by(Product.price.desc(), Product.id.asc())
    elif sort_by == 'newest':
        products_query = products_query.order_by(Product.created_at.desc(), Product.id.asc())
    elif sort_by == 'name_asc':
        products_query = products_query.order_by(Product.name.asc(), Product.id.asc())
    else:
        products_query = products_query.order_by(Product.id.asc())

    # Pagination (clamped)
    page, per_page = _safe_page_params()

    if page is not None:
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

    # Default: return all matching products (no pagination)
    results = products_query.all()
    data = []
    for prod, primary_image in results:
        d = prod.to_dict()
        d['primary_image'] = primary_image
        data.append(d)

    return jsonify({"data": data}), 200


@products_bp.route('/products/<int:id>', methods=['GET'])
@products_bp.response(200, ProductDetailResponseSchema)
def get_product_by_id(id):
    """Retrieves a single product by ID.
    Customers can only view active products. Admins/superadmins can view any product.
    """
    is_admin = is_admin_user()
    query = Product.query.join(
        Category, Product.category_id == Category.id, isouter=True
    ).filter(Product.id == id)

    if not is_admin:
        query = query.filter(
            Product.is_active == True,
            (Category.id == None) | (Category.is_active == True)
        )

    product = query.first()

    if not product:
        return jsonify({
            "error_code": "PRODUCT_NOT_FOUND",
            "message": f"No product exists with ID {id}."
        }), 404

    prod_dict = product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in product.images]

    return jsonify({"data": prod_dict}), 200


@products_bp.route('/products', methods=['POST'])
@roles_required('superadmin', 'admin')
@products_bp.arguments(ProductCreateInputSchema, location='json')
@products_bp.response(201, ProductDetailResponseSchema)
def create_product(product_data):
    """Create a new product with up to 3 images."""
    images_data = product_data.pop('images', [])

    if product_data.get('category_id'):
        category = db.session.get(Category, product_data['category_id'])
        if not category:
            return jsonify({
                "error_code": "CATEGORY_NOT_FOUND",
                "message": "Category not found."
            }), 404
        if not category.is_active:
            return jsonify({
                "error_code": "CATEGORY_INACTIVE",
                "message": "Cannot assign product to an inactive category."
            }), 400

    # Auto-generate unique SKU if not provided
    if not product_data.get('sku'):
        product_data['sku'] = generate_unique_sku()

    try:
        new_product = Product(**product_data)
        db.session.add(new_product)
        db.session.flush()  # get new_product.id before commit

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

        db.session.commit()  # single atomic commit for product + images

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "PRODUCT_DATABASE_ERROR",
            "message": "An error occurred while creating the product."
        }), 500

    prod_dict = new_product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in new_product.images]

    return jsonify({"data": prod_dict}), 201


@products_bp.route('/products/<int:id>', methods=['PUT'])
@roles_required('superadmin', 'admin')
@products_bp.arguments(ProductUpdateInputSchema, location='json')
@products_bp.response(200, ProductDetailResponseSchema)
def update_product(product_data, id):
    """Replace/update an entire product and its images.
    Under RESTful PUT semantics, the client provides the full product representation to replace the existing resource.
    """
    product = db.session.get(Product, id)
    if not product:
        return jsonify({
            "error_code": "PRODUCT_NOT_FOUND",
            "message": f"Product with ID {id} not found."
        }), 404

    if product_data.get('category_id'):
        category = db.session.get(Category, product_data['category_id'])
        if not category:
            return jsonify({
                "error_code": "CATEGORY_NOT_FOUND",
                "message": "Category not found."
            }), 404
        if not category.is_active:
            return jsonify({
                "error_code": "CATEGORY_INACTIVE",
                "message": "Cannot assign product to an inactive category."
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

        db.session.commit()  # single atomic commit for product + images

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "PRODUCT_DATABASE_ERROR",
            "message": "An error occurred while updating the product."
        }), 500

    prod_dict = product.to_dict()
    prod_dict['images'] = [img.to_dict() for img in product.images]

    return jsonify({"data": prod_dict}), 200


@products_bp.route('/products/<int:id>', methods=['DELETE'])
@roles_required('superadmin', 'admin')
def delete_product(id):
    """Delete a product.
    - If linked to ACTIVE in-progress orders ('pending', 'paid', 'processing', 'shipped'): blocked with 409 Conflict.
    - If linked ONLY to completed/cancelled orders ('delivered', 'cancelled'): soft-deleted (is_active = False) with 204.
    - If never ordered: hard-deleted with 204.
    """
    product = db.session.get(Product, id)
    if not product:
        return jsonify({
            "error_code": "PRODUCT_NOT_FOUND",
            "message": f"Product with ID {id} not found."
        }), 404

    # Check for active in-progress orders
    active_orders_count = db.session.query(order_items).join(
        Order, order_items.c.order_id == Order.id
    ).filter(
        order_items.c.product_id == id,
        Order.status.in_(['pending', 'paid', 'processing', 'shipped'])
    ).count()

    if active_orders_count > 0:
        return jsonify({
            "error_code": "PRODUCT_CONFLICT",
            "message": (
                f"Cannot delete product because it is linked to {active_orders_count} active in-progress order(s). "
                "Complete or cancel those orders first."
            )
        }), 409

    # Check if referenced in historical orders
    has_any_orders = db.session.query(order_items).filter_by(product_id=id).first() is not None

    try:
        if has_any_orders:
            # Soft-delete: deactivate from catalog so historical order items and DB foreign keys remain intact
            product.is_active = False
            db.session.commit()
        else:
            # Hard-delete: safe to remove completely
            db.session.delete(product)
            db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error_code": "PRODUCT_DATABASE_ERROR",
            "message": "An error occurred while deleting the product."
        }), 500

    return '', 204
