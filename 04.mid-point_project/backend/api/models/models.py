from api import db
from datetime import datetime

class Account(db.Model):
    __tablename__="accounts"

    id = db.Column(db.Integer, primary_key=True)
    mobile=db.Column(db.String(20), nullable=False, unique=True)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    stores = db.relationship('Store', back_populates="account", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "mobile": self.mobile,
            "created_at": self.created_at.isoformat(),
        }
    

class Store(db.Model):
    __tablename__="stores"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255),nullable=False)
    address = db.Column(db.Text , nullable=True)
    store_link = db.Column(db.String(512), nullable=False, unique=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = db.relationship('Account', back_populates="stores")
    products = db.relationship('Product', back_populates="store", lazy=True)
    orders = db.relationship('Order', back_populates="store", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "store_link": self.store_link,
            "account_id": self.account_id,
            "created_at": self.created_at.isoformat(),
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