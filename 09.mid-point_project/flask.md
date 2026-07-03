# Dukaan Backend API — Assessment

A Flask + PostgreSQL backend supporting seller/buyer workflows, JWT auth, Docker, Kubernetes (with HPA, PVC, ConfigMap, Secrets), and Tilt for local dev.

---

## Project Structure

```
dukaan/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── auth.py
│   ├── seller_routes.py
│   ├── buyer_routes.py
│   └── utils.py
├── migrations/
├── config.py
├── run.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── pvc.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── app-deployment.yaml
│   ├── app-service.yaml
│   └── hpa.yaml
└── Tiltfile
```

---

## `requirements.txt`

```txt
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-JWT-Extended==4.6.0
psycopg2-binary==2.9.9
python-dotenv==1.0.1
Werkzeug==3.0.3
```

---

## `config.py`

```python
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://dukaan:dukaan123@localhost:5432/dukaan_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = False  # tokens don't expire for this assessment
```

---

## `app/__init__.py`

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.seller_routes import seller_bp
    from app.buyer_routes import buyer_bp

    app.register_blueprint(seller_bp, url_prefix="/api/seller")
    app.register_blueprint(buyer_bp, url_prefix="/api/buyer")

    return app
```

---

## `app/models.py`

```python
from app import db
from datetime import datetime


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stores = db.relationship("Store", back_populates="account", lazy=True)

    def to_dict(self):
        return {"id": self.id, "mobile": self.mobile}


class Store(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    store_link = db.Column(db.String(512), unique=True, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship("Account", back_populates="stores")
    products = db.relationship("Product", back_populates="store", lazy=True)
    orders = db.relationship("Order", back_populates="store", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "store_link": self.store_link,
        }


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)

    products = db.relationship("Product", back_populates="category", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("name", "store_id", name="uq_category_store"),
    )

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    mrp = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(512), nullable=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship("Store", back_populates="products")
    category = db.relationship("Category", back_populates="products")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "mrp": str(self.mrp),
            "sale_price": str(self.sale_price),
            "image_url": self.image_url,
            "category": self.category.to_dict() if self.category else None,
        }


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", back_populates="customer", lazy=True)
    carts = db.relationship("Cart", back_populates="customer", lazy=True)

    def to_dict(self):
        return {"id": self.id, "mobile": self.mobile, "address": self.address}


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)  # for unauthenticated users
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="carts")
    items = db.relationship("CartItem", back_populates="cart", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "store_id": self.store_id,
            "items": [item.to_dict() for item in self.items],
        }


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product")

    def to_dict(self):
        return {
            "id": self.id,
            "product": self.product.to_dict() if self.product else None,
            "qty": self.qty,
        }


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship("Store", back_populates="orders")
    customer = db.relationship("Customer", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "store_id": self.store_id,
            "customer_id": self.customer_id,
            "total_amount": str(self.total_amount),
            "status": self.status,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat(),
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "qty": self.qty,
            "unit_price": str(self.unit_price),
        }
```

---

## `app/utils.py`

```python
import re
import uuid


def slugify(text: str) -> str:
    """Convert store name to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def generate_store_link(store_name: str) -> str:
    slug = slugify(store_name)
    unique_suffix = uuid.uuid4().hex[:6]
    return f"{slug}-{unique_suffix}"
```

---

## `app/auth.py`

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import db
from app.models import Account, Customer

auth_bp = Blueprint("auth", __name__)


def issue_seller_token(mobile: str):
    """Create seller account if not exists and return JWT."""
    account = Account.query.filter_by(mobile=mobile).first()
    if not account:
        account = Account(mobile=mobile)
        db.session.add(account)
        db.session.commit()
    token = create_access_token(identity={"id": account.id, "role": "seller"})
    return account, token


def issue_buyer_token(mobile: str):
    """Create customer record if not exists and return JWT."""
    customer = Customer.query.filter_by(mobile=mobile).first()
    if not customer:
        customer = Customer(mobile=mobile)
        db.session.add(customer)
        db.session.commit()
    token = create_access_token(identity={"id": customer.id, "role": "buyer"})
    return customer, token
```

---

## `app/seller_routes.py`

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app import db
from app.models import Account, Store, Product, Category, Order
from app.auth import issue_seller_token
from app.utils import generate_store_link

seller_bp = Blueprint("seller", __name__)


# ─── 1. Seller Signup ────────────────────────────────────────────────────────

@seller_bp.route("/signup", methods=["POST"])
def seller_signup():
    """
    POST /api/seller/signup
    Body: { "mobile": "9876543210", "otp": "1234" }
    OTP is accepted as-is (no real validation per spec).
    """
    data = request.get_json()
    mobile = data.get("mobile")
    otp = data.get("otp")

    if not mobile or not otp:
        return jsonify({"error": "mobile and otp are required"}), 400

    account, token = issue_seller_token(mobile)

    return jsonify({
        "message": "Signup successful",
        "account": account.to_dict(),
        "token": token,
    }), 201


# ─── 2. Create Store ─────────────────────────────────────────────────────────

@seller_bp.route("/store", methods=["POST"])
@jwt_required()
def create_store():
    """
    POST /api/seller/store
    Headers: Authorization: Bearer <token>
    Body: { "name": "My Shop", "address": "123 MG Road, Pune" }
    """
    identity = get_jwt_identity()
    if identity.get("role") != "seller":
        return jsonify({"error": "Seller access only"}), 403

    data = request.get_json()
    name = data.get("name")
    address = data.get("address", "")

    if not name:
        return jsonify({"error": "Store name is required"}), 400

    store_link = generate_store_link(name)

    store = Store(
        name=name,
        address=address,
        store_link=store_link,
        account_id=identity["id"],
    )
    db.session.add(store)
    db.session.commit()

    return jsonify({
        "store_id": store.id,
        "store_link": store.store_link,
        "name": store.name,
        "address": store.address,
    }), 201


# ─── 3. Add Product ──────────────────────────────────────────────────────────

@seller_bp.route("/store/<int:store_id>/product", methods=["POST"])
@jwt_required()
def add_product(store_id):
    """
    POST /api/seller/store/<store_id>/product
    Headers: Authorization: Bearer <token>
    Body: {
        "name": "Laptop", "description": "...", "mrp": 50000,
        "sale_price": 45000, "image_url": "http://...", "category": "Electronics"
    }
    """
    identity = get_jwt_identity()
    if identity.get("role") != "seller":
        return jsonify({"error": "Seller access only"}), 403

    store = Store.query.filter_by(id=store_id, account_id=identity["id"]).first()
    if not store:
        return jsonify({"error": "Store not found or access denied"}), 404

    data = request.get_json()
    name = data.get("name")
    description = data.get("description", "")
    mrp = data.get("mrp")
    sale_price = data.get("sale_price")
    image_url = data.get("image_url", "")
    category_name = data.get("category", "")

    if not name or mrp is None or sale_price is None:
        return jsonify({"error": "name, mrp and sale_price are required"}), 400

    # Create category if it doesn't exist
    category = None
    if category_name:
        category = Category.query.filter_by(name=category_name, store_id=store_id).first()
        if not category:
            category = Category(name=category_name, store_id=store_id)
            db.session.add(category)
            db.session.flush()  # get ID before commit

    product = Product(
        name=name,
        description=description,
        mrp=mrp,
        sale_price=sale_price,
        image_url=image_url,
        store_id=store_id,
        category_id=category.id if category else None,
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({
        "id": product.id,
        "name": product.name,
        "image_url": product.image_url,
    }), 201


# ─── 4. Get Seller Orders ────────────────────────────────────────────────────

@seller_bp.route("/store/<int:store_id>/orders", methods=["GET"])
@jwt_required()
def get_orders(store_id):
    """
    GET /api/seller/store/<store_id>/orders
    Returns all orders for the store.
    """
    identity = get_jwt_identity()
    if identity.get("role") != "seller":
        return jsonify({"error": "Seller access only"}), 403

    store = Store.query.filter_by(id=store_id, account_id=identity["id"]).first()
    if not store:
        return jsonify({"error": "Store not found or access denied"}), 404

    orders = Order.query.filter_by(store_id=store_id).all()
    return jsonify({"orders": [o.to_dict() for o in orders]}), 200
```

---

## `app/buyer_routes.py`

```python
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from sqlalchemy import func
from app import db
from app.models import Store, Product, Category, Cart, CartItem, Order, OrderItem, Customer
from app.auth import issue_buyer_token

buyer_bp = Blueprint("buyer", __name__)


# ─── 1. Get Store Details ────────────────────────────────────────────────────

@buyer_bp.route("/store/<store_link>", methods=["GET"])
def get_store(store_link):
    """
    GET /api/buyer/store/<store_link>
    Returns store info by unique link.
    """
    store = Store.query.filter_by(store_link=store_link).first()
    if not store:
        return jsonify({"error": "Store not found"}), 404

    return jsonify({
        "store_id": store.id,
        "name": store.name,
        "address": store.address,
    }), 200


# ─── 2. Get Product Catalog ──────────────────────────────────────────────────

@buyer_bp.route("/store/<store_link>/catalog", methods=["GET"])
def get_catalog(store_link):
    """
    GET /api/buyer/store/<store_link>/catalog
    Returns products grouped by category, sorted by product count desc.
    """
    store = Store.query.filter_by(store_link=store_link).first()
    if not store:
        return jsonify({"error": "Store not found"}), 404

    # Categories with product counts, sorted descending
    categories = (
        db.session.query(Category, func.count(Product.id).label("product_count"))
        .outerjoin(Product, Product.category_id == Category.id)
        .filter(Category.store_id == store.id)
        .group_by(Category.id)
        .order_by(func.count(Product.id).desc())
        .all()
    )

    catalog = []
    for cat, count in categories:
        products = Product.query.filter_by(store_id=store.id, category_id=cat.id).all()
        catalog.append({
            "category": cat.to_dict(),
            "product_count": count,
            "products": [p.to_dict() for p in products],
        })

    # Products with no category
    uncategorised = Product.query.filter_by(store_id=store.id, category_id=None).all()
    if uncategorised:
        catalog.append({
            "category": {"id": None, "name": "Uncategorised"},
            "product_count": len(uncategorised),
            "products": [p.to_dict() for p in uncategorised],
        })

    return jsonify({"store_id": store.id, "catalog": catalog}), 200


# ─── 3a. Add / Update Cart Item ──────────────────────────────────────────────

@buyer_bp.route("/cart", methods=["POST"])
def update_cart():
    """
    POST /api/buyer/cart
    Body: { "session_id": "uuid-string", "store_link": "my-shop-abc123",
            "product_id": 1, "qty": 2 }
    qty=0 removes the item. Works for unauthenticated users via session_id.
    """
    data = request.get_json()
    session_id = data.get("session_id") or str(uuid.uuid4())
    store_link = data.get("store_link")
    product_id = data.get("product_id")
    qty = data.get("qty", 1)

    if not store_link or product_id is None:
        return jsonify({"error": "store_link and product_id are required"}), 400

    store = Store.query.filter_by(store_link=store_link).first()
    if not store:
        return jsonify({"error": "Store not found"}), 404

    product = Product.query.filter_by(id=product_id, store_id=store.id).first()
    if not product:
        return jsonify({"error": "Product not found in this store"}), 404

    # Get or create cart
    cart = Cart.query.filter_by(session_id=session_id, store_id=store.id).first()
    if not cart:
        cart = Cart(session_id=session_id, store_id=store.id)
        db.session.add(cart)
        db.session.flush()

    # Get or create cart item
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

    if qty <= 0:
        if item:
            db.session.delete(item)
    else:
        if item:
            item.qty = qty
        else:
            item = CartItem(cart_id=cart.id, product_id=product_id, qty=qty)
            db.session.add(item)

    db.session.commit()
    return jsonify({"session_id": session_id, "cart": cart.to_dict()}), 200


# ─── 3b. Get Cart ────────────────────────────────────────────────────────────

@buyer_bp.route("/cart/<session_id>", methods=["GET"])
def get_cart(session_id):
    """GET /api/buyer/cart/<session_id>"""
    cart = Cart.query.filter_by(session_id=session_id).first()
    if not cart:
        return jsonify({"error": "Cart not found"}), 404
    return jsonify(cart.to_dict()), 200


# ─── 4a. Buyer Login / Token ─────────────────────────────────────────────────

@buyer_bp.route("/login", methods=["POST"])
def buyer_login():
    """
    POST /api/buyer/login
    Body: { "mobile": "9876543210", "otp": "0000", "address": "optional" }
    OTP bypass — any combination issues a token.
    """
    data = request.get_json()
    mobile = data.get("mobile")
    otp = data.get("otp")
    address = data.get("address", "")

    if not mobile or not otp:
        return jsonify({"error": "mobile and otp are required"}), 400

    customer, token = issue_buyer_token(mobile)

    if address and not customer.address:
        customer.address = address
        db.session.commit()

    return jsonify({
        "message": "Login successful",
        "customer": customer.to_dict(),
        "token": token,
    }), 200


# ─── 4b. Place Order ─────────────────────────────────────────────────────────

@buyer_bp.route("/order", methods=["POST"])
@jwt_required()
def place_order():
    """
    POST /api/buyer/order
    Headers: Authorization: Bearer <token>
    Body: { "session_id": "uuid-string" }
    Converts the cart into an order.
    """
    identity = get_jwt_identity()
    if identity.get("role") != "buyer":
        return jsonify({"error": "Buyer access only"}), 403

    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    cart = Cart.query.filter_by(session_id=session_id).first()
    if not cart or not cart.items:
        return jsonify({"error": "Cart is empty or not found"}), 400

    customer_id = identity["id"]

    # Link cart to customer if not already linked
    if not cart.customer_id:
        cart.customer_id = customer_id

    # Build order
    total = sum(item.product.sale_price * item.qty for item in cart.items)

    order = Order(
        store_id=cart.store_id,
        customer_id=customer_id,
        total_amount=total,
        status="pending",
    )
    db.session.add(order)
    db.session.flush()

    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            qty=item.qty,
            unit_price=item.product.sale_price,
        )
        db.session.add(order_item)

    # Clear the cart after order
    for item in cart.items:
        db.session.delete(item)

    db.session.commit()

    return jsonify({
        "message": "Order placed successfully",
        "order_id": order.id,
        "total_amount": str(order.total_amount),
    }), 201
```

---

## `run.py`

```python
from app import create_app, db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
```

---

## `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]
```

---

## `docker-compose.yml`

```yaml
version: "3.9"

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dukaan_db
      POSTGRES_USER: dukaan
      POSTGRES_PASSWORD: dukaan123
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://dukaan:dukaan123@db:5432/dukaan_db
      SECRET_KEY: super-secret-key
      JWT_SECRET_KEY: jwt-super-secret
    depends_on:
      - db

volumes:
  pgdata:
```

---

## Kubernetes Manifests

### `k8s/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dukaan
```

---

### `k8s/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dukaan-config
  namespace: dukaan
data:
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  DATABASE_NAME: "dukaan_db"
  DATABASE_USER: "dukaan"
  FLASK_ENV: "production"
```

---

### `k8s/secret.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dukaan-secret
  namespace: dukaan
type: Opaque
# Values below are base64-encoded. To encode: echo -n 'value' | base64
# dukaan123     -> ZHVrYWFuMTIz
# super-secret  -> c3VwZXItc2VjcmV0
# jwt-secret    -> and3Qtc2VjcmV0
data:
  DATABASE_PASSWORD: ZHVrYWFuMTIz
  SECRET_KEY: c3VwZXItc2VjcmV0
  JWT_SECRET_KEY: and3Qtc2VjcmV0
```

---

### `k8s/pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: dukaan
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

---

### `k8s/postgres-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: dukaan
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: DATABASE_NAME
            - name: POSTGRES_USER
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: DATABASE_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: dukaan-secret
                  key: DATABASE_PASSWORD
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
      volumes:
        - name: postgres-storage
          persistentVolumeClaim:
            claimName: postgres-pvc
```

---

### `k8s/postgres-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: dukaan
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
  type: ClusterIP
```

---

### `k8s/app-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dukaan-app
  namespace: dukaan
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dukaan-app
  template:
    metadata:
      labels:
        app: dukaan-app
    spec:
      containers:
        - name: dukaan-app
          image: dukaan-app:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
          env:
            - name: DATABASE_URL
              value: "postgresql://$(DATABASE_USER):$(DATABASE_PASSWORD)@$(DATABASE_HOST):$(DATABASE_PORT)/$(DATABASE_NAME)"
            - name: DATABASE_HOST
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: DATABASE_HOST
            - name: DATABASE_PORT
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: DATABASE_PORT
            - name: DATABASE_NAME
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: DATABASE_NAME
            - name: DATABASE_USER
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: DATABASE_USER
            - name: DATABASE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: dukaan-secret
                  key: DATABASE_PASSWORD
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: dukaan-secret
                  key: SECRET_KEY
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: dukaan-secret
                  key: JWT_SECRET_KEY
          readinessProbe:
            httpGet:
              path: /api/buyer/store/test
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
```

---

### `k8s/app-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: dukaan-app-service
  namespace: dukaan
spec:
  selector:
    app: dukaan-app
  ports:
    - name: http
      port: 80
      targetPort: 5000
      nodePort: 30080
  type: NodePort
```

---

### `k8s/hpa.yaml`

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dukaan-app-hpa
  namespace: dukaan
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dukaan-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 70
```

---

## `Tiltfile`

```python
# Tiltfile — local dev with Tilt (https://tilt.dev)

# ── Build the app image ───────────────────────────────────────────────────────
docker_build(
    "dukaan-app",
    ".",
    dockerfile="Dockerfile",
    live_update=[
        # Sync local code changes into the running container without full rebuild
        sync("./app", "/app/app"),
        sync("./run.py", "/app/run.py"),
        sync("./config.py", "/app/config.py"),
        run("pip install -r /app/requirements.txt", trigger=["./requirements.txt"]),
    ],
)

# ── Apply K8s manifests ───────────────────────────────────────────────────────
k8s_yaml([
    "k8s/namespace.yaml",
    "k8s/configmap.yaml",
    "k8s/secret.yaml",
    "k8s/pvc.yaml",
    "k8s/postgres-deployment.yaml",
    "k8s/postgres-service.yaml",
    "k8s/app-deployment.yaml",
    "k8s/app-service.yaml",
    "k8s/hpa.yaml",
])

# ── Resource configuration ────────────────────────────────────────────────────
k8s_resource(
    "postgres",
    port_forwards=["5432:5432"],
    labels=["database"],
)

k8s_resource(
    "dukaan-app",
    port_forwards=["5000:5000"],
    resource_deps=["postgres"],
    labels=["backend"],
)
```

---

## API Reference

### Seller Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/seller/signup` | None | Signup with mobile + OTP, receive JWT |
| POST | `/api/seller/store` | Bearer JWT | Create a new store |
| POST | `/api/seller/store/<store_id>/product` | Bearer JWT | Add product to store |
| GET | `/api/seller/store/<store_id>/orders` | Bearer JWT | View all orders for store |

### Buyer Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/buyer/store/<store_link>` | None | Get store info by link |
| GET | `/api/buyer/store/<store_link>/catalog` | None | Get catalog grouped by category |
| POST | `/api/buyer/cart` | None | Add/update/remove item in cart |
| GET | `/api/buyer/cart/<session_id>` | None | View cart contents |
| POST | `/api/buyer/login` | None | Login (OTP bypassed), receive JWT |
| POST | `/api/buyer/order` | Bearer JWT | Place order from cart |

---

## Sample Request/Response

### Seller Signup

```bash
curl -X POST http://localhost:5000/api/seller/signup \
  -H "Content-Type: application/json" \
  -d '{"mobile": "9876543210", "otp": "1234"}'
```

```json
{
  "message": "Signup successful",
  "account": { "id": 1, "mobile": "9876543210" },
  "token": "eyJ0eXAiOiJKV1Qi..."
}
```

### Create Store

```bash
curl -X POST http://localhost:5000/api/seller/store \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Raj Electronics", "address": "FC Road, Pune"}'
```

```json
{
  "store_id": 1,
  "store_link": "raj-electronics-a3f9c1",
  "name": "Raj Electronics",
  "address": "FC Road, Pune"
}
```

### Add Product

```bash
curl -X POST http://localhost:5000/api/seller/store/1/product \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "15-inch laptop",
    "mrp": 50000,
    "sale_price": 45000,
    "image_url": "http://example.com/laptop.jpg",
    "category": "Electronics"
  }'
```

```json
{ "id": 1, "name": "Laptop", "image_url": "http://example.com/laptop.jpg" }
```

### Add to Cart (unauthenticated)

```bash
curl -X POST http://localhost:5000/api/buyer/cart \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session-abc123",
    "store_link": "raj-electronics-a3f9c1",
    "product_id": 1,
    "qty": 2
  }'
```

### Buyer Login

```bash
curl -X POST http://localhost:5000/api/buyer/login \
  -H "Content-Type: application/json" \
  -d '{"mobile": "9000000001", "otp": "0000", "address": "Kothrud, Pune"}'
```

### Place Order

```bash
curl -X POST http://localhost:5000/api/buyer/order \
  -H "Authorization: Bearer <buyer-token>" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "my-session-abc123"}'
```

```json
{
  "message": "Order placed successfully",
  "order_id": 1,
  "total_amount": "90000.00"
}
```

---

## Local Setup (without K8s)

```bash
# 1. Clone and enter project
git clone <repo> && cd dukaan

# 2. Start Postgres
docker-compose up -d db

# 3. Create virtualenv
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Init DB
flask db init
flask db migrate -m "initial"
flask db upgrade

# 5. Run app
python run.py
```

---

## Local Setup (with Tilt + K8s)

> Requires: [Docker](https://docs.docker.com/get-docker/), [kubectl](https://kubernetes.io/docs/tasks/tools/), [kind](https://kind.sigs.k8s.io/) or [minikube](https://minikube.sigs.k8s.io/), and [Tilt](https://docs.tilt.dev/install.html)

```bash
# 1. Start a local cluster (choose one)
kind create cluster
# or
minikube start

# 2. Start Tilt
tilt up

# App will be available at http://localhost:5000
# Postgres port-forwarded to localhost:5432
```

---

## Database Schema (Summary)

```
accounts         — seller accounts (mobile, id)
stores           — seller stores (name, address, store_link, account_id)
categories       — product categories (name, store_id)
products         — inventory (name, description, mrp, sale_price, image_url, store_id, category_id)
customers        — buyer accounts (mobile, address)
carts            — server-side cart (session_id, customer_id, store_id)
cart_items       — line items in cart (cart_id, product_id, qty)
orders           — placed orders (store_id, customer_id, total_amount, status)
order_items      — line items in order (order_id, product_id, qty, unit_price)
```

---

## Design Decisions

- **OTP validation is bypassed** — any mobile + OTP combination issues a JWT, per spec.
- **Cart is session-based** — identified by a client-generated `session_id` UUID. No auth required to add to cart. On order placement, the cart is linked to the authenticated customer.
- **One seller → multiple stores** — the `stores` table has a FK to `accounts`.
- **Categories are store-scoped** — `(name, store_id)` has a unique constraint, so the same category name can exist in different stores.
- **Postgres as a Deployment (not StatefulSet)** — per spec, with PVC for data persistence. Suitable for single-instance local/staging setups.
- **HPA** scales the app pods between 2 and 10 replicas based on CPU (60%) and memory (70%) utilization.
