from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, order_items
from werkzeug.security import generate_password_hash

def seed_database():
    app = create_app()
    with app.app_context():
        print("Seeding sample data for Checkpoint 2...")

        # 1. Ensure Categories
        cat_electronics = Category.query.filter_by(name='Electronics').first()
        if not cat_electronics:
            cat_electronics = Category(name='Electronics', description='Gadgets and tech devices', is_active=True)
            db.session.add(cat_electronics)

        cat_apparel = Category.query.filter_by(name='Apparel').first()
        if not cat_apparel:
            cat_apparel = Category(name='Apparel', description='Clothing and fashion items', is_active=True)
            db.session.add(cat_apparel)

        cat_inactive = Category.query.filter_by(name='Inactive Category').first()
        if not cat_inactive:
            cat_inactive = Category(name='Inactive Category', description='Deactivated category', is_active=False)
            db.session.add(cat_inactive)

        db.session.commit()

        # 2. Ensure Products
        p1 = Product.query.filter_by(name='Wireless Noise-Canceling Headphones').first()
        if not p1:
            p1 = Product(
                category_id=cat_electronics.id,
                name='Wireless Noise-Canceling Headphones',
                description='High-fidelity Bluetooth headphones',
                price=199.99,
                stock=45,
                is_active=True
            )
            db.session.add(p1)

        p2 = Product.query.filter_by(name='Ergonomic Mechanical Keyboard').first()
        if not p2:
            p2 = Product(
                category_id=cat_electronics.id,
                name='Ergonomic Mechanical Keyboard',
                description='Custom RGB mechanical keyboard',
                price=129.50,
                stock=30,
                is_active=True
            )
            db.session.add(p2)

        p3 = Product.query.filter_by(name='Organic Cotton Hoodie').first()
        if not p3:
            p3 = Product(
                category_id=cat_apparel.id,
                name='Organic Cotton Hoodie',
                description='Premium organic cotton pullover hoodie',
                price=59.99,
                stock=100,
                is_active=True
            )
            db.session.add(p3)

        p_inactive = Product.query.filter_by(name='Deactivated Phone').first()
        if not p_inactive:
            p_inactive = Product(
                category_id=cat_electronics.id,
                name='Deactivated Phone',
                description='Old deactivated smartphone model',
                price=499.99,
                stock=5,
                is_active=False
            )
            db.session.add(p_inactive)

        p_in_inactive_cat = Product.query.filter_by(name='Product in Inactive Category').first()
        if not p_in_inactive_cat:
            p_in_inactive_cat = Product(
                category_id=cat_inactive.id,
                name='Product in Inactive Category',
                description='Product whose category is deactivated',
                price=10.00,
                stock=10,
                is_active=True
            )
            db.session.add(p_in_inactive_cat)

        db.session.commit()

        # 3. Ensure Users — passwords are stored as real bcrypt/pbkdf2 hashes
        alice = User.query.filter_by(username='alice_smith').first()
        if not alice:
            alice = User(
                username='alice_smith',
                email='alice@example.com',
                password_hash=generate_password_hash('alice_password'),
                role='customer',
                is_active=True
            )
            db.session.add(alice)
        else:
            # Update to a real hash if currently using the old fake prefix
            if alice.password_hash.startswith('pbkdf2:sha256:hash_sample'):
                alice.password_hash = generate_password_hash('alice_password')

        deactivated_user = User.query.filter_by(username='deactivated_user').first()
        if not deactivated_user:
            deactivated_user = User(
                username='deactivated_user',
                email='deactivated@example.com',
                password_hash=generate_password_hash('deactivated_password'),
                role='customer',
                is_active=False
            )
            db.session.add(deactivated_user)
        else:
            if not deactivated_user.password_hash.startswith(('pbkdf2:', 'scrypt:', 'bcrypt:')):
                deactivated_user.password_hash = generate_password_hash('deactivated_password')

        db.session.commit()

        # 4. Ensure Order linked to multiple products (Many-to-Many via order_items)
        existing_order = Order.query.filter_by(user_id=alice.id).first()
        if not existing_order:
            new_order = Order(
                user_id=alice.id,
                total_amount=329.49,
                status='pending'
            )
            db.session.add(new_order)
            db.session.commit()

            # Insert order_items (1 order linked to multiple products: p1 and p2)
            stmt1 = order_items.insert().values(
                order_id=new_order.id,
                product_id=p1.id,
                quantity=1,
                price_at_purchase=199.99
            )
            stmt2 = order_items.insert().values(
                order_id=new_order.id,
                product_id=p2.id,
                quantity=1,
                price_at_purchase=129.50
            )
            db.session.execute(stmt1)
            db.session.execute(stmt2)
            db.session.commit()
            print(f"Created Order ID #{new_order.id} for User '{alice.username}' linked to Products #{p1.id} and #{p2.id}.")

        print("Seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
