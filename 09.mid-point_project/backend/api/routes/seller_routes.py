from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token,get_jwt
from api import db
from api.models.models import Account, Store, Product, Category, Order
from api.auth.auth import issue_seller_token
from api.utils.utils import generate_store_link

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
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    if role != "seller":
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
        account_id=user_id,
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
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    if role != "seller":
        return jsonify({"error": "Seller access only"}), 403

    store = Store.query.filter_by(id=store_id, account_id=user_id).first()
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
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    if role != "seller":
        return jsonify({"error": "Seller access only"}), 403

    store = Store.query.filter_by(id=store_id, account_id=user_id).first()
    if not store:
        return jsonify({"error": "Store not found or access denied"}), 404

    orders = Order.query.filter_by(store_id=store_id).all()
    return jsonify({"orders": [o.to_dict() for o in orders]}), 200
