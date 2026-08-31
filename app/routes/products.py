import logging
from flask_smorest import Blueprint
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.product import Product, ProductImage
from app.models.category import Category
from app.auth import roles_required, is_admin_user
from app.errors import error_response, not_found_response
from app.validators import validate_product_category, validate_product_deletion
from app.utils.pagination import get_page_params
from app.schemas import (
    ProductListResponseSchema,
    ProductCreateInputSchema,
    ProductUpdateInputSchema,
    ProductDetailResponseSchema,
)

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__, description='Operations on products')


def save_product_images(product_id: int, images_data: list, replace: bool = False):
    """Saves or replaces images for a product, ensuring exactly one primary image."""
    if replace:
        ProductImage.query.filter_by(product_id=product_id).delete()

    if not images_data:
        return

    if not any(img.get('is_primary') for img in images_data):
        images_data[0]['is_primary'] = True

    for img_obj in images_data:
        new_img = ProductImage(
            product_id=product_id,
            image_base64=img_obj['image_base64'],
            is_primary=img_obj.get('is_primary', False)
        )
        db.session.add(new_img)


def build_filtered_products_query(args: dict, is_admin: bool):
    """Builds the base query and applies role visibility, search, fashion filters, and sorting."""
    primary_image_subquery = db.session.query(
        ProductImage.product_id,
        ProductImage.image_base64
    ).filter(
        ProductImage.is_primary.is_(True)
    ).subquery()

    query = db.session.query(
        Product,
        primary_image_subquery.c.image_base64.label('primary_image')
    ).join(
        Category, Product.category_id == Category.id, isouter=True
    ).outerjoin(
        primary_image_subquery, Product.id == primary_image_subquery.c.product_id
    )

    if not is_admin:
        # Public / customer view: strictly active products in active (or uncategorized) categories
        query = query.filter(
            Product.is_active.is_(True),
            (Category.id.is_(None)) | (Category.is_active.is_(True))
        )
    else:
        # Admin / superadmin view: shows all by default, or filters by is_active query param
        is_active_param = args.get('is_active')
        if is_active_param is not None:
            if is_active_param.lower() == 'true':
                query = query.filter(Product.is_active.is_(True))
            elif is_active_param.lower() == 'false':
                query = query.filter(Product.is_active.is_(False))

    # Fashion-specific filters
    if args.get('gender'):
        query = query.filter(Product.gender == args['gender'])

    if args.get('size'):
        query = query.filter(Product.size == args['size'])

    if args.get('color'):
        query = query.filter(Product.color.ilike(f"%{args['color']}%"))

    if args.get('material'):
        query = query.filter(Product.material.ilike(f"%{args['material']}%"))

    if args.get('category_id') is not None:
        query = query.filter(Product.category_id == args.get('category_id', type=int))

    # Price range filters
    min_price = args.get('min_price', None, type=float)
    if min_price is not None:
        query = query.filter(Product.price >= max(0.0, min_price))

    max_price = args.get('max_price', None, type=float)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Free-text search across name and description
    search = args.get('search')
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )

    # Sorting
    sort_by = args.get('sort_by')
    sort_map = {
        'oldest': (Product.updated_at.asc(), Product.id.asc()),
        'price_asc': (Product.price.asc(), Product.id.asc()),
        'price_desc': (Product.price.desc(), Product.id.asc()),
        'name_asc': (Product.name.asc(), Product.id.asc()),
        'name_desc': (Product.name.desc(), Product.id.asc()),
    }
    order_clause = sort_map.get(sort_by, (Product.updated_at.desc(), Product.id.desc()))
    return query.order_by(*order_clause)


@products_bp.route('/products', methods=['GET'])
@products_bp.response(200, ProductListResponseSchema)
def get_all_products():
    """Returns a paginated list of active products whose category is also active (or uncategorized).
    Supports optional filters: ?gender=Women&size=M&color=Black
    Pagination: ?page=1&per_page=10 (max per_page=100)
    """
    is_admin = is_admin_user()
    page, per_page = get_page_params()
    logger.info("GET /products — page=%s, per_page=%s, is_admin=%s", page, per_page, is_admin)
    logger.debug("Request filters: %s", request.args.to_dict())

    products_query = build_filtered_products_query(request.args, is_admin=is_admin)

    if page is not None:
        pagination = products_query.paginate(page=page, per_page=per_page, error_out=False)
        data = []
        for prod, primary_image in pagination.items:
            d = prod.to_dict()
            d['primary_image'] = primary_image
            data.append(d)

        logger.debug("Returning %d products (total=%d, page %d of %d)", len(data), pagination.total, pagination.page, pagination.pages)
        return jsonify({
            "data": data,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }), 200

    results = products_query.all()
    data = []
    for prod, primary_image in results:
        d = prod.to_dict()
        d['primary_image'] = primary_image
        data.append(d)

    logger.debug("Returning %d non-paginated products", len(data))
    return jsonify({"data": data}), 200


@products_bp.route('/products/<int:id>', methods=['GET'])
@products_bp.response(200, ProductDetailResponseSchema)
def get_product_by_id(id):
    """Retrieves a single product by ID.
    Customers can only view active products. Admins/superadmins can view any product.
    """
    logger.info("GET /products/%d", id)
    is_admin = is_admin_user()
    query = Product.query.join(
        Category, Product.category_id == Category.id, isouter=True
    ).filter(Product.id == id)

    if not is_admin:
        query = query.filter(
            Product.is_active.is_(True),
            (Category.id.is_(None)) | (Category.is_active.is_(True))
        )

    product = query.first()
    if not product:
        logger.warning("Product not found: id=%d (is_admin=%s)", id, is_admin)
        return not_found_response("Product", id)

    return jsonify({"data": product.to_detail_dict()}), 200


@products_bp.route('/products', methods=['POST'])
@products_bp.doc(security=[{"BearerAuth": []}])
@roles_required('superadmin', 'admin')
@products_bp.arguments(ProductCreateInputSchema, location='json')
@products_bp.response(201, ProductDetailResponseSchema)
def create_product(product_data):
    """Create a new product with up to 3 images."""
    logger.info("POST /products — creating product '%s'", product_data.get('name'))
    images_data = product_data.pop('images', [])

    category, err = validate_product_category(product_data.get('category_id'))
    if err:
        logger.warning("Create product failed — invalid category_id=%s", product_data.get('category_id'))
        return err

    if not product_data.get('sku'):
        product_data['sku'] = Product.generate_unique_sku()

    try:
        new_product = Product(**product_data)
        db.session.add(new_product)
        db.session.flush()

        save_product_images(new_product.id, images_data, replace=False)
        db.session.commit()
        logger.info("Product created successfully — id=%d, sku='%s'", new_product.id, new_product.sku)

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error creating product '%s': %s", product_data.get('name'), e, exc_info=True)
        return error_response("PRODUCT_DATABASE_ERROR", "An error occurred while creating the product.", 500)

    return jsonify({"data": new_product.to_detail_dict()}), 201


@products_bp.route('/products/<int:id>', methods=['PUT'])
@products_bp.doc(security=[{"BearerAuth": []}])
@roles_required('superadmin', 'admin')
@products_bp.arguments(ProductUpdateInputSchema, location='json')
@products_bp.response(200, ProductDetailResponseSchema)
def update_product(product_data, id):
    """Update a product and its images (supports partial payload update).
    Only provided fields in the request body will be updated. Existing fields and images are preserved if omitted.
    """
    logger.info("PUT /products/%d — updating product", id)
    product = db.session.get(Product, id)
    if not product:
        logger.warning("Update product failed — Product not found: id=%d", id)
        return not_found_response("Product", id)

    category, err = validate_product_category(product_data.get('category_id'))
    if err:
        logger.warning("Update product failed — invalid category_id=%s", product_data.get('category_id'))
        return err

    images_data = product_data.pop('images', None)

    try:
        for key, val in product_data.items():
            setattr(product, key, val)

        if images_data is not None:
            save_product_images(id, images_data, replace=True)

        db.session.commit()
        logger.info("Product updated successfully — id=%d", id)

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error updating product id=%d: %s", id, e, exc_info=True)
        return error_response("PRODUCT_DATABASE_ERROR", "An error occurred while updating the product.", 500)

    return jsonify({"data": product.to_detail_dict()}), 200


@products_bp.route('/products/<int:id>', methods=['DELETE'])
@products_bp.doc(security=[{"BearerAuth": []}])
@roles_required('superadmin', 'admin')
@products_bp.response(204)
def delete_product(id):
    """Delete a product.
    - If linked to ACTIVE in-progress orders ('pending', 'paid', 'processing', 'shipped'): blocked with 409 Conflict.
    - If linked ONLY to completed/cancelled orders ('delivered', 'cancelled'): soft-deleted (is_active = False) with 204.
    - If never ordered: hard-deleted with 204.
    """
    logger.info("DELETE /products/%d — deleting product", id)
    product = db.session.get(Product, id)
    if not product:
        logger.warning("Delete product failed — Product not found: id=%d", id)
        return not_found_response("Product", id)

    has_any_orders, err = validate_product_deletion(id)
    if err:
        logger.warning("Delete product blocked for id=%d", id)
        return err

    try:
        if has_any_orders:
            product.is_active = False
            db.session.commit()
            logger.info("Product soft-deleted (has historical orders) — id=%d", id)
        else:
            db.session.delete(product)
            db.session.commit()
            logger.info("Product hard-deleted (no orders) — id=%d", id)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error deleting product id=%d: %s", id, e, exc_info=True)
        return error_response("PRODUCT_DATABASE_ERROR", "An error occurred while deleting the product.", 500)

    return '', 204

