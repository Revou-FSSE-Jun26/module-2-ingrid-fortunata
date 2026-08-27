import logging
from flask_smorest import Blueprint
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload
from app.extensions import db
from app.models.category import Category
from app.auth import roles_required, is_admin_user
from app.schemas import (
    CategoryCreateInputSchema,
    CategoryUpdateInputSchema,
    CategoryGetResponseSchema,
    CategoryWithProductsResponseSchema,
    CategoryListResponseSchema,
)

from app.errors import error_response, not_found_response, conflict_response
from app.validators import validate_category_name_unique, validate_category_deletion

logger = logging.getLogger(__name__)

categories_bp = Blueprint('categories', __name__, description='Operations on categories')


@categories_bp.route('/categories', methods=['POST'])
@roles_required('superadmin', 'admin')
@categories_bp.arguments(CategoryCreateInputSchema, location='json')
@categories_bp.response(201, CategoryGetResponseSchema)
def create_category(category_data):
    """Create a new category."""
    name = category_data.get('name', '').strip()
    category_data['name'] = name
    logger.info("POST /categories — creating category '%s'", name)

    err = validate_category_name_unique(name)
    if err:
        logger.warning("Create category failed — name conflict: '%s'", name)
        return err

    try:
        new_cat = Category(**category_data)
        db.session.add(new_cat)
        db.session.commit()
        logger.info("Category created successfully — id=%d, name='%s'", new_cat.id, new_cat.name)
    except IntegrityError:
        db.session.rollback()
        logger.warning("Create category failed on commit — IntegrityError for name '%s'", name)
        return conflict_response("CATEGORY_CONFLICT", "Category name already exists.")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error creating category '%s': %s", name, e, exc_info=True)
        return error_response("CATEGORY_DATABASE_ERROR", "An error occurred while creating the category.", 500)

    return jsonify({
        "data": new_cat.to_dict()
    }), 201


@categories_bp.route('/categories', methods=['GET'])
@categories_bp.response(200, CategoryListResponseSchema)
def get_categories():
    """List categories.
    Customers see only active categories. Admins can see all or filter by ?is_active=true|false.
    """
    is_admin = is_admin_user()
    logger.info("GET /categories — is_admin=%s", is_admin)
    query = Category.query

    if not is_admin:
        query = query.filter_by(is_active=True)
    else:
        is_active_param = request.args.get('is_active')
        if is_active_param is not None:
            if is_active_param.lower() == 'true':
                query = query.filter_by(is_active=True)
            elif is_active_param.lower() == 'false':
                query = query.filter_by(is_active=False)

    # Listed alphabetically by name
    categories = query.order_by(Category.name.asc()).all()
    logger.debug("Returning %d categories", len(categories))
    return jsonify({
        "data": [c.to_dict() for c in categories]
    }), 200


@categories_bp.route('/categories/<int:id>', methods=['GET'])
@categories_bp.response(200, CategoryWithProductsResponseSchema)
def get_category_by_id(id):
    """Get a specific category along with its products.
    Customers can only access active categories and active products.
    Admins can view any category along with all associated products.
    """
    logger.info("GET /categories/%d", id)
    is_admin = is_admin_user()
    query = Category.query.options(selectinload(Category.products)).filter_by(id=id)

    if not is_admin:
        query = query.filter_by(is_active=True)

    category = query.first()
    if not category:
        logger.warning("Category not found: id=%d (is_admin=%s)", id, is_admin)
        return not_found_response("Category", id)

    return jsonify({
        "data": category.to_with_products_dict(is_admin=is_admin)
    }), 200


@categories_bp.route('/categories/<int:id>', methods=['PUT'])
@roles_required('superadmin', 'admin')
@categories_bp.arguments(CategoryUpdateInputSchema, location='json')
@categories_bp.response(200, CategoryGetResponseSchema)
def update_category(category_data, id):
    """Replace/update an entire category.
    Under RESTful PUT semantics, the client provides the full category representation to replace the existing resource.
    """
    logger.info("PUT /categories/%d — updating category", id)
    category = db.session.get(Category, id)
    if not category:
        logger.warning("Update category failed — Category not found: id=%d", id)
        return not_found_response("Category", id)

    name = category_data.get('name')
    if name:
        name = name.strip()
        category_data['name'] = name
        if name != category.name:
            err = validate_category_name_unique(name, exclude_id=id)
            if err:
                logger.warning("Update category failed — name conflict: '%s'", name)
                return err

    try:
        for key, val in category_data.items():
            setattr(category, key, val)
        db.session.commit()
        logger.info("Category updated successfully — id=%d, name='%s'", category.id, category.name)
    except IntegrityError:
        db.session.rollback()
        logger.warning("Update category failed on commit — IntegrityError for name '%s'", name)
        return conflict_response("CATEGORY_CONFLICT", "Category name already exists.")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error updating category id=%d: %s", id, e, exc_info=True)
        return error_response("CATEGORY_DATABASE_ERROR", "An error occurred while updating the category.", 500)

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
    logger.info("DELETE /categories/%d — deleting category", id)
    category = db.session.get(Category, id)
    if not category:
        logger.warning("Delete category failed — Category not found: id=%d", id)
        return not_found_response("Category", id)

    # Block deletion if active products are linked to this category
    err = validate_category_deletion(id)
    if err:
        logger.warning("Delete category blocked for id=%d", id)
        return err

    try:
        db.session.delete(category)
        db.session.commit()
        logger.info("Category deleted successfully — id=%d", id)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error("Error deleting category id=%d: %s", id, e, exc_info=True)
        return error_response("CATEGORY_DATABASE_ERROR", "An error occurred while deleting the category.", 500)

    return '', 204

