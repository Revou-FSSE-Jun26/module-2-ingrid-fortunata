import pytest
from app import create_app, db as _db


def seed_test_database(db_instance):
    """Seed initial in-memory SQLite database with users, categories, products, and orders."""
    from app.models.user import User
    from app.models.category import Category
    from app.models.product import Product, ProductImage
    from app.models.order import Order, order_items

    # 1. Seed Users
    users = [
        User(id=1, username="superadmin_user", email="superadmin@revofashion.com", role="superadmin", is_active=True),
        User(id=2, username="admin_user", email="admin@revofashion.com", role="admin", is_active=True),
        User(id=3, username="alice_smith", email="alice@example.com", role="customer", is_active=True),
        User(id=4, username="deactivated_user", email="deactivated@example.com", role="customer", is_active=False),
    ]
    users[0].set_password("superadmin_password")
    users[1].set_password("admin_password")
    users[2].set_password("alice_password")
    users[3].set_password("deactivated_password")
    db_instance.session.add_all(users)
    db_instance.session.commit()

    # 2. Seed Categories
    categories = [
        Category(id=1, name="T-Shirts", description="Casual and everyday t-shirts, crew necks, and graphic tees", is_active=True),
        Category(id=2, name="Shirts & Blouses", description="Formal and casual shirts, oxford shirts, and blouses", is_active=True),
        Category(id=3, name="Pants & Jeans", description="Bottoms including denim, chinos, and ankle pants", is_active=True),
        Category(id=4, name="Outerwear", description="Jackets, coats, down jackets, and hoodies", is_active=True),
        Category(id=5, name="Dresses & Skirts", description="Dresses, skirts, and jumpsuits for women", is_active=True),
        Category(id=6, name="Activewear", description="Sportswear, dry-EX, and athleisure clothing", is_active=True),
        Category(id=7, name="Innerwear & Loungewear", description="Underwear, socks, heattech, and home wear", is_active=True),
        Category(id=8, name="Discontinued Collection", description="Past season items no longer sold", is_active=False),
    ]
    db_instance.session.add_all(categories)
    db_instance.session.commit()

    # 3. Seed Products
    products = [
        Product(id=1, category_id=1, name="AIRism Cotton Crew Neck T-Shirt", description="Smooth AIRism cotton blend with quick-dry and anti-odor technology.", price=14.90, stock=200, size="M", color="White", material="58% Cotton, 38% Polyester, 4% Spandex", gender="Men", sku="RF-TS-001", is_active=True),
        Product(id=2, category_id=1, name="Supima Cotton Crew Neck T-Shirt", description="Premium Supima cotton with a luxuriously soft feel.", price=19.90, stock=150, size="L", color="Navy", material="100% Supima Cotton", gender="Men", sku="RF-TS-002", is_active=True),
        Product(id=3, category_id=1, name="Oversized Cropped T-Shirt", description="Relaxed oversized fit with a slightly cropped length.", price=19.90, stock=120, size="S", color="Black", material="100% Cotton", gender="Women", sku="RF-TS-003", is_active=True),
        Product(id=4, category_id=2, name="Oxford Slim-Fit Long Sleeve Shirt", description="Classic button-down oxford shirt with a modern slim fit.", price=29.90, stock=80, size="M", color="Light Blue", material="100% Cotton", gender="Men", sku="RF-SH-001", is_active=True),
        Product(id=5, category_id=2, name="Rayon Long Sleeve Blouse", description="Elegant drape with a smooth rayon finish.", price=29.90, stock=90, size="M", color="Off White", material="100% Rayon", gender="Women", sku="RF-SH-002", is_active=True),
        Product(id=6, category_id=3, name="EZY Ankle Pants", description="Incredibly comfortable ankle-length pants with elastic waist.", price=39.90, stock=100, size="L", color="Dark Gray", material="68% Polyester, 28% Rayon, 4% Spandex", gender="Men", sku="RF-PT-001", is_active=True),
        Product(id=7, category_id=3, name="Ultra Stretch High-Rise Jeans", description="High-rise skinny jeans with ultra stretch denim.", price=49.90, stock=70, size="S", color="Blue", material="86% Cotton, 12% Polyester, 2% Spandex", gender="Women", sku="RF-PT-002", is_active=True),
        Product(id=8, category_id=4, name="Ultra Light Down Jacket", description="Incredibly lightweight and warm premium down jacket.", price=79.90, stock=50, size="M", color="Olive", material="100% Nylon", gender="Unisex", sku="RF-OW-001", is_active=True),
        Product(id=9, category_id=4, name="Pocketable UV Protection Parka", description="Lightweight parka with UPF 50+ sun protection.", price=49.90, stock=60, size="M", color="Beige", material="100% Polyester", gender="Women", sku="RF-OW-002", is_active=True),
        Product(id=10, category_id=4, name="Dry Stretch Full-Zip Hoodie", description="Quick-drying hoodie with 4-way stretch fabric.", price=39.90, stock=85, size="L", color="Black", material="88% Polyester, 12% Spandex", gender="Men", sku="RF-OW-003", is_active=True),
        Product(id=11, category_id=5, name="Mercerized Cotton A-Line Dress", description="Elegant A-line dress with a subtle sheen.", price=39.90, stock=40, size="M", color="Dark Green", material="100% Cotton", gender="Women", sku="RF-DR-001", is_active=True),
        Product(id=12, category_id=6, name="DRY-EX Crew Neck T-Shirt", description="Ultra-fast drying performance tee with mesh ventilation.", price=19.90, stock=180, size="M", color="Red", material="100% Polyester", gender="Unisex", sku="RF-AW-001", is_active=True),
        Product(id=13, category_id=6, name="Ultra Stretch Active Jogger Pants", description="Flexible jogger pants with 4-way stretch.", price=39.90, stock=75, size="M", color="Navy", material="85% Nylon, 15% Spandex", gender="Men", sku="RF-AW-002", is_active=True),
        Product(id=14, category_id=7, name="HEATTECH Crew Neck Long Sleeve T-Shirt", description="Bio-warming technology that converts body moisture into heat.", price=14.90, stock=300, size="M", color="Black", material="43% Polyester", gender="Unisex", sku="RF-IW-001", is_active=True),
        Product(id=15, category_id=7, name="AIRism Cotton Ribbed Tank Top", description="Comfortable ribbed tank top with AIRism technology.", price=12.90, stock=160, size="S", color="White", material="62% Cotton", gender="Women", sku="RF-IW-002", is_active=True),
        Product(id=16, category_id=8, name="Vintage Flannel Shirt (Discontinued)", description="Past season flannel shirt — no longer in production.", price=34.90, stock=3, size="L", color="Red Plaid", material="100% Cotton", gender="Men", sku="RF-DC-001", is_active=False),
    ]
    db_instance.session.add_all(products)
    db_instance.session.commit()

    # 4. Seed Product Image
    img = ProductImage(
        id=1,
        product_id=1,
        image_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        is_primary=True
    )
    db_instance.session.add(img)
    db_instance.session.commit()

    # 5. Seed Order & Order Items
    order = Order(
        id=1,
        user_id=3,
        total_amount=54.80,
        status="pending",
        shipping_address="123 Marina Bay, Singapore",
        recipient_name="Alice Smith",
        recipient_phone="+6591234567"
    )
    db_instance.session.add(order)
    db_instance.session.flush()

    stmt1 = order_items.insert().values(order_id=order.id, product_id=1, quantity=1, price_at_purchase=14.90, size="M", color="White")
    stmt2 = order_items.insert().values(order_id=order.id, product_id=6, quantity=1, price_at_purchase=39.90, size="L", color="Dark Gray")
    db_instance.session.execute(stmt1)
    db_instance.session.execute(stmt2)
    db_instance.session.commit()


@pytest.fixture(scope='module')
def app():
    """Flask app configured for testing — uses in-memory SQLite."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    }
    flask_app = create_app(test_config)

    with flask_app.app_context():
        _db.create_all()       # create all tables
        seed_test_database(_db) # populate initial test fixture dataset
        yield flask_app        # run tests
        _db.session.remove()
        _db.drop_all()         # clean up tables after all module tests finish
        _db.engine.dispose()


@pytest.fixture(scope='module')
def client(app):
    """Test client — depends on the app fixture."""
    return app.test_client()


@pytest.fixture(scope='function')
def admin_headers(client):
    """Returns Bearer authorization headers for the seeded admin user."""
    payload = {"username": "admin_user", "password": "admin_password"}
    res = client.post('/auth/login', json=payload)
    data = res.get_json()
    assert res.status_code == 200, f"Admin login failed: {data}"
    token = data['data']['token']
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope='function')
def customer_headers(client):
    """Returns Bearer authorization headers for the seeded customer user (alice_smith)."""
    payload = {"username": "alice_smith", "password": "alice_password"}
    res = client.post('/auth/login', json=payload)
    data = res.get_json()
    assert res.status_code == 200, f"Customer login failed: {data}"
    token = data['data']['token']
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope='function')
def superadmin_headers(client):
    """Returns Bearer authorization headers for the seeded superadmin user."""
    payload = {"username": "superadmin_user", "password": "superadmin_password"}
    res = client.post('/auth/login', json=payload)
    data = res.get_json()
    assert res.status_code == 200, f"Superadmin login failed: {data}"
    token = data['data']['token']
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_test_stocks(app):
    """Ensure seeded products maintain healthy stock level for order test runs."""
    yield
    with app.app_context():
        from app.models.product import Product
        p = _db.session.get(Product, 1)
        if p and p.stock < 10:
            p.stock = 50
            _db.session.commit()
