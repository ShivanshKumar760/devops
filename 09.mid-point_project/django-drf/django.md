# Dukaan Backend API — Django DRF

A Django REST Framework backend using `@api_view` decorators and `djangorestframework-simplejwt` for JWT authentication, backed by PostgreSQL.

---

## Project Structure

```
dukaan/
├── dukaan/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── stores/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── products/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── orders/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── cart/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── manage.py
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
Django==5.0.6
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
psycopg2-binary==2.9.9
python-dotenv==1.0.1
django-cors-headers==4.4.0
```

---

## `dukaan/settings.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-change-in-prod")

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Local apps
    "accounts",
    "stores",
    "products",
    "orders",
    "cart",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dukaan.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "dukaan.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "dukaan_db"),
        "USER": os.environ.get("DATABASE_USER", "dukaan"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "dukaan123"),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True

# ── DRF ──────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
}

# ── Simple JWT ───────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.environ.get("JWT_SECRET_KEY", "jwt-secret-key"),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
```

---

## `dukaan/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/seller/", include("accounts.urls")),
    path("api/seller/", include("stores.urls")),
    path("api/buyer/", include("orders.urls")),
    path("api/buyer/", include("cart.urls")),
]
```

---

## `utils/helpers.py`

```python
import re
import uuid


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def generate_store_link(store_name: str) -> str:
    slug = slugify(store_name)
    unique_suffix = uuid.uuid4().hex[:6]
    return f"{slug}-{unique_suffix}"


def make_jwt_for_user(user_id: int, role: str) -> str:
    """Issue a SimpleJWT token carrying a role claim."""
    from rest_framework_simplejwt.tokens import AccessToken

    token = AccessToken()
    token["user_id"] = user_id
    token["role"] = role
    return str(token)
```

---

## Accounts App

### `accounts/models.py`

```python
from django.db import models


class SellerAccount(models.Model):
    mobile = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts"

    def __str__(self):
        return self.mobile


class Customer(models.Model):
    mobile = models.CharField(max_length=15, unique=True)
    address = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customers"

    def __str__(self):
        return self.mobile
```

---

### `accounts/serializers.py`

```python
from rest_framework import serializers
from .models import SellerAccount, Customer


class SellerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerAccount
        fields = ["id", "mobile"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "mobile", "address"]
```

---

### `accounts/views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import SellerAccount, Customer
from .serializers import SellerAccountSerializer, CustomerSerializer
from utils.helpers import make_jwt_for_user


# ─── Seller Signup ────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def seller_signup(request):
    """
    POST /api/seller/signup
    Body: { "mobile": "9876543210", "otp": "1234" }
    OTP is accepted as-is — no real validation per spec.
    """
    mobile = request.data.get("mobile")
    otp = request.data.get("otp")

    if not mobile or not otp:
        return Response(
            {"error": "mobile and otp are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    account, created = SellerAccount.objects.get_or_create(mobile=mobile)
    token = make_jwt_for_user(account.id, role="seller")

    return Response(
        {
            "message": "Signup successful",
            "account": SellerAccountSerializer(account).data,
            "token": token,
        },
        status=status.HTTP_201_CREATED,
    )


# ─── Buyer Login ──────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def buyer_login(request):
    """
    POST /api/buyer/login
    Body: { "mobile": "9000000001", "otp": "0000", "address": "optional" }
    OTP bypass — any combination issues a token.
    """
    mobile = request.data.get("mobile")
    otp = request.data.get("otp")
    address = request.data.get("address", "")

    if not mobile or not otp:
        return Response(
            {"error": "mobile and otp are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    customer, created = Customer.objects.get_or_create(mobile=mobile)

    if address and not customer.address:
        customer.address = address
        customer.save()

    token = make_jwt_for_user(customer.id, role="buyer")

    return Response(
        {
            "message": "Login successful",
            "customer": CustomerSerializer(customer).data,
            "token": token,
        },
        status=status.HTTP_200_OK,
    )
```

---

### `accounts/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.seller_signup, name="seller-signup"),
]
```

---

## Stores App

### `stores/models.py`

```python
from django.db import models
from accounts.models import SellerAccount


class Store(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, default="")
    store_link = models.CharField(max_length=512, unique=True)
    account = models.ForeignKey(
        SellerAccount, on_delete=models.CASCADE, related_name="stores"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stores"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="categories"
    )

    class Meta:
        db_table = "categories"
        unique_together = ("name", "store")

    def __str__(self):
        return f"{self.name} ({self.store.name})"
```

---

### `stores/serializers.py`

```python
from rest_framework import serializers
from .models import Store, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "name", "address", "store_link"]
```

---

### `stores/views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Store, Category
from .serializers import StoreSerializer, CategorySerializer
from accounts.models import SellerAccount
from utils.helpers import generate_store_link


def get_seller(request):
    """Extract seller from JWT role claim."""
    role = request.auth.get("role") if request.auth else None
    if role != "seller":
        return None, Response(
            {"error": "Seller access only"}, status=status.HTTP_403_FORBIDDEN
        )
    user_id = request.auth.get("user_id")
    try:
        return SellerAccount.objects.get(id=user_id), None
    except SellerAccount.DoesNotExist:
        return None, Response(
            {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
        )


# ─── Create Store ─────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_store(request):
    """
    POST /api/seller/store/
    Headers: Authorization: Bearer <token>
    Body: { "name": "My Shop", "address": "123 MG Road, Pune" }
    """
    seller, err = get_seller(request)
    if err:
        return err

    name = request.data.get("name")
    address = request.data.get("address", "")

    if not name:
        return Response(
            {"error": "Store name is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    store_link = generate_store_link(name)
    store = Store.objects.create(
        name=name, address=address, store_link=store_link, account=seller
    )

    return Response(
        {
            "store_id": store.id,
            "store_link": store.store_link,
            "name": store.name,
            "address": store.address,
        },
        status=status.HTTP_201_CREATED,
    )


# ─── Get Store Details (Buyer) ────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def get_store(request, store_link):
    """GET /api/buyer/store/<store_link>/"""
    try:
        store = Store.objects.get(store_link=store_link)
    except Store.DoesNotExist:
        return Response({"error": "Store not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {"store_id": store.id, "name": store.name, "address": store.address}
    )
```

---

### `stores/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path("store/", views.create_store, name="create-store"),
]
```

---

## Products App

### `products/models.py`

```python
from django.db import models
from stores.models import Store, Category


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(max_length=512, blank=True, default="")
    store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products"

    def __str__(self):
        return self.name
```

---

### `products/serializers.py`

```python
from rest_framework import serializers
from .models import Product
from stores.serializers import CategorySerializer


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "mrp",
            "sale_price", "image_url", "category",
        ]


class ProductBriefSerializer(serializers.ModelSerializer):
    """Lightweight serializer for catalog listings."""

    class Meta:
        model = Product
        fields = ["id", "name", "image_url", "mrp", "sale_price"]
```

---

### `products/views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count

from .models import Product
from .serializers import ProductSerializer, ProductBriefSerializer
from stores.models import Store, Category
from stores.views import get_seller


# ─── Add Product ──────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_product(request, store_id):
    """
    POST /api/seller/store/<store_id>/product/
    Headers: Authorization: Bearer <token>
    Body: {
        "name": "Laptop", "description": "...", "mrp": 50000,
        "sale_price": 45000, "image_url": "http://...", "category": "Electronics"
    }
    """
    seller, err = get_seller(request)
    if err:
        return err

    try:
        store = Store.objects.get(id=store_id, account=seller)
    except Store.DoesNotExist:
        return Response(
            {"error": "Store not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    name = request.data.get("name")
    description = request.data.get("description", "")
    mrp = request.data.get("mrp")
    sale_price = request.data.get("sale_price")
    image_url = request.data.get("image_url", "")
    category_name = request.data.get("category", "")

    if not name or mrp is None or sale_price is None:
        return Response(
            {"error": "name, mrp and sale_price are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    category = None
    if category_name:
        category, _ = Category.objects.get_or_create(
            name=category_name, store=store
        )

    product = Product.objects.create(
        name=name,
        description=description,
        mrp=mrp,
        sale_price=sale_price,
        image_url=image_url,
        store=store,
        category=category,
    )

    return Response(
        {"id": product.id, "name": product.name, "image_url": product.image_url},
        status=status.HTTP_201_CREATED,
    )


# ─── Get Catalog (Buyer) ──────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def get_catalog(request, store_link):
    """
    GET /api/buyer/store/<store_link>/catalog/
    Products grouped by category, sorted by product count descending.
    """
    try:
        store = Store.objects.get(store_link=store_link)
    except Store.DoesNotExist:
        return Response({"error": "Store not found"}, status=status.HTTP_404_NOT_FOUND)

    # Categories sorted by number of products (descending)
    categories = (
        Category.objects.filter(store=store)
        .annotate(product_count=Count("products"))
        .order_by("-product_count")
    )

    catalog = []
    for cat in categories:
        products = Product.objects.filter(store=store, category=cat)
        catalog.append(
            {
                "category": {"id": cat.id, "name": cat.name},
                "product_count": cat.product_count,
                "products": ProductBriefSerializer(products, many=True).data,
            }
        )

    # Uncategorised products
    uncategorised = Product.objects.filter(store=store, category__isnull=True)
    if uncategorised.exists():
        catalog.append(
            {
                "category": {"id": None, "name": "Uncategorised"},
                "product_count": uncategorised.count(),
                "products": ProductBriefSerializer(uncategorised, many=True).data,
            }
        )

    return Response({"store_id": store.id, "catalog": catalog})
```

---

### `products/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path("store/<int:store_id>/product/", views.add_product, name="add-product"),
]
```

---

## Cart App

### `cart/models.py`

```python
from django.db import models
from stores.models import Store
from products.models import Product
from accounts.models import Customer


class Cart(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="carts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"

    def __str__(self):
        return f"Cart {self.session_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cart_items"
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.qty}x {self.product.name}"
```

---

### `cart/serializers.py`

```python
from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "qty"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "session_id", "store_id", "items"]
```

---

### `cart/views.py`

```python
import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Cart, CartItem
from .serializers import CartSerializer
from stores.models import Store
from products.models import Product


# ─── Add / Update Cart ────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def update_cart(request):
    """
    POST /api/buyer/cart/
    Body: {
        "session_id": "uuid-string",   (optional — auto-generated if missing)
        "store_link": "my-shop-abc123",
        "product_id": 1,
        "qty": 2                        (0 = remove item)
    }
    Works for unauthenticated users; identified by session_id.
    """
    session_id = request.data.get("session_id") or str(uuid.uuid4())
    store_link = request.data.get("store_link")
    product_id = request.data.get("product_id")
    qty = request.data.get("qty", 1)

    if not store_link or product_id is None:
        return Response(
            {"error": "store_link and product_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        store = Store.objects.get(store_link=store_link)
    except Store.DoesNotExist:
        return Response({"error": "Store not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        product = Product.objects.get(id=product_id, store=store)
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found in this store"},
            status=status.HTTP_404_NOT_FOUND,
        )

    cart, _ = Cart.objects.get_or_create(session_id=session_id, store=store)

    try:
        item = CartItem.objects.get(cart=cart, product=product)
        if int(qty) <= 0:
            item.delete()
        else:
            item.qty = qty
            item.save()
    except CartItem.DoesNotExist:
        if int(qty) > 0:
            CartItem.objects.create(cart=cart, product=product, qty=qty)

    cart.refresh_from_db()
    return Response(
        {"session_id": session_id, "cart": CartSerializer(cart).data},
        status=status.HTTP_200_OK,
    )


# ─── Get Cart ─────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def get_cart(request, session_id):
    """GET /api/buyer/cart/<session_id>/"""
    try:
        cart = Cart.objects.get(session_id=session_id)
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(CartSerializer(cart).data)
```

---

### `cart/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path("cart/", views.update_cart, name="update-cart"),
    path("cart/<str:session_id>/", views.get_cart, name="get-cart"),
]
```

---

## Orders App

### `orders/models.py`

```python
from django.db import models
from stores.models import Store
from accounts.models import Customer
from products.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="orders")
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders"

    def __str__(self):
        return f"Order #{self.id} — {self.customer.mobile}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.qty}x {self.product.name if self.product else 'deleted'}"
```

---

### `orders/serializers.py`

```python
from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "product_name", "qty", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "store_id", "customer_id",
            "total_amount", "status", "items", "created_at",
        ]
```

---

### `orders/views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart, CartItem
from accounts.models import Customer
from stores.views import get_seller


# ─── Place Order (Buyer) ──────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_order(request):
    """
    POST /api/buyer/order/
    Headers: Authorization: Bearer <buyer-token>
    Body: { "session_id": "uuid-string" }
    Converts the cart into an order.
    """
    role = request.auth.get("role") if request.auth else None
    if role != "buyer":
        return Response(
            {"error": "Buyer access only"}, status=status.HTTP_403_FORBIDDEN
        )

    customer_id = request.auth.get("user_id")
    session_id = request.data.get("session_id")

    if not session_id:
        return Response(
            {"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        cart = Cart.objects.prefetch_related("items__product").get(
            session_id=session_id
        )
    except Cart.DoesNotExist:
        return Response(
            {"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if not cart.items.exists():
        return Response(
            {"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Link cart to the customer if not already set
    if not cart.customer_id:
        cart.customer = customer
        cart.save()

    total = sum(item.product.sale_price * item.qty for item in cart.items.all())

    order = Order.objects.create(
        store=cart.store,
        customer=customer,
        total_amount=total,
        status="pending",
    )

    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            qty=item.qty,
            unit_price=item.product.sale_price,
        )

    # Clear cart after order
    cart.items.all().delete()

    return Response(
        {
            "message": "Order placed successfully",
            "order_id": order.id,
            "total_amount": str(order.total_amount),
        },
        status=status.HTTP_201_CREATED,
    )


# ─── Get Seller Orders ────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders(request, store_id):
    """
    GET /api/seller/store/<store_id>/orders/
    Returns all orders for a store owned by the authenticated seller.
    """
    seller, err = get_seller(request)
    if err:
        return err

    from stores.models import Store

    try:
        store = Store.objects.get(id=store_id, account=seller)
    except Store.DoesNotExist:
        return Response(
            {"error": "Store not found or access denied"},
            status=status.HTTP_404_NOT_FOUND,
        )

    orders = Order.objects.prefetch_related("items__product").filter(store=store)
    return Response({"orders": OrderSerializer(orders, many=True).data})
```

---

### `orders/urls.py`

```python
from django.urls import path
from . import views
from accounts.views import buyer_login
from stores.views import get_store
from products.views import get_catalog

urlpatterns = [
    # Buyer auth
    path("login/", buyer_login, name="buyer-login"),
    # Store info
    path("store/<str:store_link>/", get_store, name="get-store"),
    path("store/<str:store_link>/catalog/", get_catalog, name="get-catalog"),
    # Orders
    path("order/", views.place_order, name="place-order"),
    # Seller orders (also under buyer prefix for convenience; move to seller if preferred)
    path("store/<int:store_id>/orders/", views.get_orders, name="get-orders"),
]
```

---

## Root URL conf (final)

```python
# dukaan/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/seller/", include("accounts.urls")),   # signup
    path("api/seller/", include("stores.urls")),     # create store
    path("api/seller/", include("products.urls")),   # add product
    path("api/seller/store/", include([              # seller orders
        path("<int:store_id>/orders/", __import__("orders.views", fromlist=["get_orders"]).get_orders),
    ])),
    path("api/buyer/", include("orders.urls")),      # login, store, catalog, order
    path("api/buyer/", include("cart.urls")),        # cart
]
```

> **Tip:** You can also keep a cleaner urls.py by importing `get_orders` at the top:

```python
# dukaan/urls.py  (cleaner version)
from django.contrib import admin
from django.urls import path, include
from orders.views import get_orders

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/seller/", include("accounts.urls")),
    path("api/seller/", include("stores.urls")),
    path("api/seller/", include("products.urls")),
    path("api/seller/store/<int:store_id>/orders/", get_orders, name="get-orders"),
    path("api/buyer/", include("orders.urls")),
    path("api/buyer/", include("cart.urls")),
]
```

---

## `manage.py`

```python
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dukaan.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

---

## `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations then start the dev server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

EXPOSE 8000
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
      - "8000:8000"
    environment:
      DATABASE_NAME: dukaan_db
      DATABASE_USER: dukaan
      DATABASE_PASSWORD: dukaan123
      DATABASE_HOST: db
      DATABASE_PORT: "5432"
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
  DJANGO_SETTINGS_MODULE: "dukaan.settings"
  DEBUG: "False"
  ALLOWED_HOSTS: "*"
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
# Encode values: echo -n 'value' | base64
# dukaan123       -> ZHVrYWFuMTIz
# super-secret-k  -> c3VwZXItc2VjcmV0LWs=
# jwt-secret-key  -> and3Qtc2VjcmV0LWtleQ==
data:
  DATABASE_PASSWORD: ZHVrYWFuMTIz
  SECRET_KEY: c3VwZXItc2VjcmV0LWs=
  JWT_SECRET_KEY: and3Qtc2VjcmV0LWtleQ==
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
            - containerPort: 8000
          env:
            - name: DJANGO_SETTINGS_MODULE
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: DJANGO_SETTINGS_MODULE
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
            - name: DEBUG
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: DEBUG
            - name: ALLOWED_HOSTS
              valueFrom:
                configMapKeyRef:
                  name: dukaan-config
                  key: ALLOWED_HOSTS
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
              path: /api/buyer/store/test/
              port: 8000
            initialDelaySeconds: 15
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
      targetPort: 8000
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
        sync("./accounts", "/app/accounts"),
        sync("./stores", "/app/stores"),
        sync("./products", "/app/products"),
        sync("./orders", "/app/orders"),
        sync("./cart", "/app/cart"),
        sync("./utils", "/app/utils"),
        sync("./dukaan", "/app/dukaan"),
        sync("./manage.py", "/app/manage.py"),
        run(
            "pip install -r /app/requirements.txt",
            trigger=["./requirements.txt"],
        ),
        run(
            "python /app/manage.py migrate --no-input",
            trigger=["./*/migrations/"],
        ),
    ],
)

# ── Apply manifests in dependency order ──────────────────────────────────────
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

# ── Resource config ───────────────────────────────────────────────────────────
k8s_resource(
    "postgres",
    port_forwards=["5432:5432"],
    labels=["database"],
)

k8s_resource(
    "dukaan-app",
    port_forwards=["8000:8000"],
    resource_deps=["postgres"],
    labels=["backend"],
)
```

---

## API Reference

### Seller Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/seller/signup/` | None | Signup with mobile + OTP, receive JWT |
| POST | `/api/seller/store/` | Bearer JWT (seller) | Create a new store |
| POST | `/api/seller/store/<store_id>/product/` | Bearer JWT (seller) | Add product to store |
| GET | `/api/seller/store/<store_id>/orders/` | Bearer JWT (seller) | View all store orders |

### Buyer Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/buyer/login/` | None | Login (OTP bypassed), receive JWT |
| GET | `/api/buyer/store/<store_link>/` | None | Get store info by link |
| GET | `/api/buyer/store/<store_link>/catalog/` | None | Catalog grouped by category |
| POST | `/api/buyer/cart/` | None | Add / update / remove cart item |
| GET | `/api/buyer/cart/<session_id>/` | None | View cart |
| POST | `/api/buyer/order/` | Bearer JWT (buyer) | Place order from cart |

---

## Sample Requests

### Seller Signup

```bash
curl -X POST http://localhost:8000/api/seller/signup/ \
  -H "Content-Type: application/json" \
  -d '{"mobile": "9876543210", "otp": "1234"}'
```

```json
{
  "message": "Signup successful",
  "account": {"id": 1, "mobile": "9876543210"},
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Create Store

```bash
curl -X POST http://localhost:8000/api/seller/store/ \
  -H "Authorization: Bearer <seller-token>" \
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
curl -X POST http://localhost:8000/api/seller/store/1/product/ \
  -H "Authorization: Bearer <seller-token>" \
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
{"id": 1, "name": "Laptop", "image_url": "http://example.com/laptop.jpg"}
```

### Get Catalog

```bash
curl http://localhost:8000/api/buyer/store/raj-electronics-a3f9c1/catalog/
```

```json
{
  "store_id": 1,
  "catalog": [
    {
      "category": {"id": 1, "name": "Electronics"},
      "product_count": 3,
      "products": [...]
    }
  ]
}
```

### Add to Cart (unauthenticated)

```bash
curl -X POST http://localhost:8000/api/buyer/cart/ \
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
curl -X POST http://localhost:8000/api/buyer/login/ \
  -H "Content-Type: application/json" \
  -d '{"mobile": "9000000001", "otp": "0000", "address": "Kothrud, Pune"}'
```

### Place Order

```bash
curl -X POST http://localhost:8000/api/buyer/order/ \
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

# 3. Create virtualenv and install deps
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Start the dev server
python manage.py runserver
# App available at http://localhost:8000
```

---

## Local Setup (with Tilt + K8s)

> Requires: Docker, kubectl, kind or minikube, and Tilt

```bash
# 1. Start a local cluster
kind create cluster
# or: minikube start

# 2. Start Tilt (builds image, applies all manifests, port-forwards)
tilt up

# App: http://localhost:8000
# Postgres: localhost:5432
```

---

## Database Schema (Summary)

```
accounts      — SellerAccount (mobile, created_at)
customers     — Customer (mobile, address, created_at)
stores        — Store (name, address, store_link, account_id)
categories    — Category (name, store_id)  [unique: name+store]
products      — Product (name, description, mrp, sale_price, image_url, store_id, category_id)
carts         — Cart (session_id, customer_id, store_id)
cart_items    — CartItem (cart_id, product_id, qty)  [unique: cart+product]
orders        — Order (store_id, customer_id, total_amount, status)
order_items   — OrderItem (order_id, product_id, qty, unit_price)
```

---

## Design Decisions

- **`@api_view` throughout** — no class-based views or ViewSets, per spec.
- **SimpleJWT with custom `role` claim** — `make_jwt_for_user(id, role)` embeds `"role": "seller"` or `"role": "buyer"` in the token payload. Views read `request.auth.get("role")` to enforce role separation without a second user model.
- **OTP bypass** — any mobile + OTP combination succeeds and issues a token.
- **Cart is session-based** — unauthenticated users get a cart via `session_id`. On order placement, the cart is linked to the authenticated customer.
- **`get_or_create` for categories** — creates a category if it doesn't exist for that store; scoped by `(name, store)` unique constraint.
- **Postgres as Deployment + PVC** — single-instance, per spec. StatefulSet not used.
- **HPA** scales app pods between 2–10 replicas at 60% CPU / 70% memory.
- **`django-cors-headers`** included for browser/mobile clients.
