import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token , get_jwt
from sqlalchemy import func
from api import db
from api.models.models import Store, Product, Category, Cart, CartItem, Order, OrderItem, Customer
from api.auth.auth import issue_buyer_token

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
    session_id = data.get("session_id") or str(uuid.uuid4()) #this is basically creating a new session
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
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    if role != "buyer":
        return jsonify({"error": "buyer access only"}), 403

    data = request.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    cart = Cart.query.filter_by(session_id=session_id).first()
    if not cart or not cart.items:
        return jsonify({"error": "Cart is empty or not found"}), 400

    customer_id = user_id

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