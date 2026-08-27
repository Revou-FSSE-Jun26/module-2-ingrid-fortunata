from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, order_items
from werkzeug.security import generate_password_hash

def seed_database(app=None, reset=False):
    if app is None:
        app = create_app()
    with app.app_context():
        if reset:
            print("Clearing and resetting database tables...")
            db.session.remove()
            db.drop_all()
            db.create_all()
            print("Database schema reset successfully.")

        print("Seeding fashion store data for RevoFashion...")

        # ─── 1. Categories (Uniqlo-inspired) ───
        categories_data = [
            ('T-Shirts', 'Casual and everyday t-shirts, crew necks, and graphic tees'),
            ('Shirts & Blouses', 'Formal and casual shirts, oxford shirts, and blouses'),
            ('Pants & Jeans', 'Bottoms including denim, chinos, and ankle pants'),
            ('Outerwear', 'Jackets, coats, down jackets, and hoodies'),
            ('Dresses & Skirts', 'Dresses, skirts, and jumpsuits for women'),
            ('Activewear', 'Sportswear, dry-EX, and athleisure clothing'),
            ('Innerwear & Loungewear', 'Underwear, socks, heattech, and home wear'),
        ]

        cats = {}
        for name, desc in categories_data:
            cat = Category.query.filter_by(name=name).first()
            if not cat:
                cat = Category(name=name, description=desc, is_active=True)
                db.session.add(cat)
            cats[name] = cat

        # Add one inactive category for testing
        cat_inactive = Category.query.filter_by(name='Discontinued Collection').first()
        if not cat_inactive:
            cat_inactive = Category(name='Discontinued Collection', description='Past season items no longer sold', is_active=False)
            db.session.add(cat_inactive)

        db.session.commit()

        # ─── 2. Products (Uniqlo-inspired clothing items) ───
        products_data = [
            # T-Shirts
            {
                'category': 'T-Shirts', 'name': 'AIRism Cotton Crew Neck T-Shirt',
                'description': 'Smooth AIRism cotton blend with quick-dry and anti-odor technology. Perfect for everyday layering.',
                'price': 14.90, 'stock': 200, 'size': 'M', 'color': 'White',
                'material': '58% Cotton, 38% Polyester, 4% Spandex', 'gender': 'Men', 'sku': 'RF-TS-001'
            },
            {
                'category': 'T-Shirts', 'name': 'Supima Cotton Crew Neck T-Shirt',
                'description': 'Premium Supima cotton with a luxuriously soft feel. Minimal and timeless design.',
                'price': 19.90, 'stock': 150, 'size': 'L', 'color': 'Navy',
                'material': '100% Supima Cotton', 'gender': 'Men', 'sku': 'RF-TS-002'
            },
            {
                'category': 'T-Shirts', 'name': 'Oversized Cropped T-Shirt',
                'description': 'Relaxed oversized fit with a slightly cropped length. Soft washed cotton.',
                'price': 19.90, 'stock': 120, 'size': 'S', 'color': 'Black',
                'material': '100% Cotton', 'gender': 'Women', 'sku': 'RF-TS-003'
            },
            # Shirts & Blouses
            {
                'category': 'Shirts & Blouses', 'name': 'Oxford Slim-Fit Long Sleeve Shirt',
                'description': 'Classic button-down oxford shirt with a modern slim fit. Wrinkle-resistant fabric.',
                'price': 29.90, 'stock': 80, 'size': 'M', 'color': 'Light Blue',
                'material': '100% Cotton', 'gender': 'Men', 'sku': 'RF-SH-001'
            },
            {
                'category': 'Shirts & Blouses', 'name': 'Rayon Long Sleeve Blouse',
                'description': 'Elegant drape with a smooth rayon finish. Features a relaxed silhouette.',
                'price': 29.90, 'stock': 90, 'size': 'M', 'color': 'Off White',
                'material': '100% Rayon', 'gender': 'Women', 'sku': 'RF-SH-002'
            },
            # Pants & Jeans
            {
                'category': 'Pants & Jeans', 'name': 'EZY Ankle Pants',
                'description': 'Incredibly comfortable ankle-length pants with elastic waist. Looks dressy, feels like sweats.',
                'price': 39.90, 'stock': 100, 'size': 'L', 'color': 'Dark Gray',
                'material': '68% Polyester, 28% Rayon, 4% Spandex', 'gender': 'Men', 'sku': 'RF-PT-001'
            },
            {
                'category': 'Pants & Jeans', 'name': 'Ultra Stretch High-Rise Jeans',
                'description': 'High-rise skinny jeans with ultra stretch denim for maximum comfort and mobility.',
                'price': 49.90, 'stock': 70, 'size': 'S', 'color': 'Blue',
                'material': '86% Cotton, 12% Polyester, 2% Spandex', 'gender': 'Women', 'sku': 'RF-PT-002'
            },
            # Outerwear
            {
                'category': 'Outerwear', 'name': 'Ultra Light Down Jacket',
                'description': 'Incredibly lightweight and warm premium down jacket. Packs into its own pouch for easy carrying.',
                'price': 79.90, 'stock': 50, 'size': 'M', 'color': 'Olive',
                'material': '100% Nylon (Shell), 90% Down 10% Feather (Fill)', 'gender': 'Unisex', 'sku': 'RF-OW-001'
            },
            {
                'category': 'Outerwear', 'name': 'Pocketable UV Protection Parka',
                'description': 'Lightweight parka with UPF 50+ sun protection. Folds into a compact pouch.',
                'price': 49.90, 'stock': 60, 'size': 'M', 'color': 'Beige',
                'material': '100% Polyester', 'gender': 'Women', 'sku': 'RF-OW-002'
            },
            {
                'category': 'Outerwear', 'name': 'Dry Stretch Full-Zip Hoodie',
                'description': 'Quick-drying hoodie with 4-way stretch fabric. Great for workouts or casual wear.',
                'price': 39.90, 'stock': 85, 'size': 'L', 'color': 'Black',
                'material': '88% Polyester, 12% Spandex', 'gender': 'Men', 'sku': 'RF-OW-003'
            },
            # Dresses & Skirts
            {
                'category': 'Dresses & Skirts', 'name': 'Mercerized Cotton A-Line Dress',
                'description': 'Elegant A-line dress with a subtle sheen from mercerized cotton treatment.',
                'price': 39.90, 'stock': 40, 'size': 'M', 'color': 'Dark Green',
                'material': '100% Cotton', 'gender': 'Women', 'sku': 'RF-DR-001'
            },
            # Activewear
            {
                'category': 'Activewear', 'name': 'DRY-EX Crew Neck T-Shirt',
                'description': 'Ultra-fast drying performance tee with mesh ventilation panels.',
                'price': 19.90, 'stock': 180, 'size': 'M', 'color': 'Red',
                'material': '100% Polyester', 'gender': 'Unisex', 'sku': 'RF-AW-001'
            },
            {
                'category': 'Activewear', 'name': 'Ultra Stretch Active Jogger Pants',
                'description': 'Flexible jogger pants with 4-way stretch. Tapered leg with zippered cuffs.',
                'price': 39.90, 'stock': 75, 'size': 'M', 'color': 'Navy',
                'material': '85% Nylon, 15% Spandex', 'gender': 'Men', 'sku': 'RF-AW-002'
            },
            # Innerwear & Loungewear
            {
                'category': 'Innerwear & Loungewear', 'name': 'HEATTECH Crew Neck Long Sleeve T-Shirt',
                'description': 'Bio-warming technology that converts body moisture into heat. Essential for cold weather layering.',
                'price': 14.90, 'stock': 300, 'size': 'M', 'color': 'Black',
                'material': '43% Polyester, 35% Acrylic, 15% Rayon, 7% Spandex', 'gender': 'Unisex', 'sku': 'RF-IW-001'
            },
            {
                'category': 'Innerwear & Loungewear', 'name': 'AIRism Cotton Ribbed Tank Top',
                'description': 'Comfortable ribbed tank top with AIRism technology for breathability.',
                'price': 12.90, 'stock': 160, 'size': 'S', 'color': 'White',
                'material': '62% Cotton, 33% Polyester, 5% Spandex', 'gender': 'Women', 'sku': 'RF-IW-002'
            },
            # Accessories (Free Size demo)
            {
                'category': 'Outerwear', 'name': 'Round Mini Shoulder Bag',
                'description': 'Viral lightweight round mini shoulder bag with water-repellent finish. Fits all daily essentials.',
                'price': 19.90, 'stock': 250, 'size': 'Free Size', 'color': 'Black',
                'material': '100% Nylon', 'gender': 'Unisex', 'sku': 'RF-AC-001'
            },
        ]

        # Inactive product for testing
        products_data.append({
            'category': 'Discontinued Collection', 'name': 'Vintage Flannel Shirt (Discontinued)',
            'description': 'Past season flannel shirt — no longer in production.',
            'price': 34.90, 'stock': 3, 'size': 'L', 'color': 'Red Plaid',
            'material': '100% Cotton Flannel', 'gender': 'Men', 'sku': 'RF-DC-001',
            'is_active': False
        })

        prods = {}
        for pd in products_data:
            existing = Product.query.filter_by(sku=pd['sku']).first()
            if not existing:
                cat_name = pd.pop('category')
                cat_obj = cats.get(cat_name, cat_inactive)
                new_prod = Product(category_id=cat_obj.id, **pd)
                db.session.add(new_prod)
                prods[pd['sku']] = new_prod
            else:
                prods[pd['sku']] = existing
                pd.pop('category', None)  # remove to avoid key error

        db.session.commit()

        # ─── 3. Users (superadmin, admin, customer) ───
        superadmin = User.query.filter_by(username='superadmin_user').first()
        if not superadmin:
            superadmin = User(
                username='superadmin_user',
                email='superadmin@revofashion.com',
                password_hash=generate_password_hash('superadmin_password'),
                role='superadmin',
                is_active=True
            )
            db.session.add(superadmin)

        admin = User.query.filter_by(username='admin_user').first()
        if not admin:
            admin = User(
                username='admin_user',
                email='admin@revofashion.com',
                password_hash=generate_password_hash('admin_password'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)

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

        db.session.commit()

        # ─── 4. Orders (Fashion purchases with size/color & shipping details) ───
        existing_order = Order.query.filter_by(user_id=alice.id).first()
        if not existing_order:
            # Order 1: Alice buys AIRism T-Shirt + EZY Ankle Pants
            p_airism = prods.get('RF-TS-001')
            p_ezy = prods.get('RF-PT-001')

            if p_airism and p_ezy:
                new_order = Order(
                    user_id=alice.id,
                    total_amount=float(p_airism.price) + float(p_ezy.price),
                    status='pending',
                    shipping_address='Jl. Sudirman No. 10, Jakarta Pusat, DKI Jakarta 10220',
                    recipient_name='Alice Smith',
                    recipient_phone='081234567890'
                )
                db.session.add(new_order)
                db.session.commit()

                stmt1 = order_items.insert().values(
                    order_id=new_order.id,
                    product_id=p_airism.id,
                    quantity=1,
                    price_at_purchase=p_airism.price,
                    size='M',
                    color='White'
                )
                stmt2 = order_items.insert().values(
                    order_id=new_order.id,
                    product_id=p_ezy.id,
                    quantity=1,
                    price_at_purchase=p_ezy.price,
                    size='L',
                    color='Dark Gray'
                )
                db.session.execute(stmt1)
                db.session.execute(stmt2)
                db.session.commit()
                print(f"Created Order ID #{new_order.id} for User '{alice.username}' — AIRism T-Shirt (M/White) + EZY Ankle Pants (L/Dark Gray)")

        print("Fashion store seeding completed successfully! 🧥👗👖")

if __name__ == '__main__':
    import sys
    reset_flag = '--reset' in sys.argv or '--clear' in sys.argv
    seed_database(reset=reset_flag)
