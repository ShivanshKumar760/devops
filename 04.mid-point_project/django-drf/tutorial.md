# Django DRF + SimpleJWT — Tutorial for the Dukaan API

This tutorial teaches you the essentials of Django REST Framework with JWT authentication, using the **Dukaan** codebase as the reference implementation. Every concept is tied directly to real code from the project.

---

## Table of contents

1. [What is DRF?](#1-what-is-drf)
2. [Models — your database tables in Python](#2-models)
3. [ModelSerializer — turning models into JSON](#3-modelserializer)
4. [@api_view — writing function-based API views](#4-api_view)
5. [Simple JWT — issuing and validating tokens](#5-simple-jwt)
6. [How role claims work in Dukaan](#6-role-claims)
7. [Password hashing in Dukaan](#7-password-hashing)
8. [Permission classes — protecting endpoints](#8-permission-classes)
9. [Settings wiring — putting it all together](#9-settings)
10. [Quick-reference cheat sheet](#10-cheat-sheet)

---

## 1. What is DRF?

**Django REST Framework (DRF)** is a library that sits on top of Django and adds everything you need to build a JSON API:

- Request/Response objects that parse JSON automatically
- View decorators and class-based views
- Serializers (converts ORM models ↔ JSON)
- Authentication and permission system
- Browsable API in development

In Dukaan, DRF is configured in `settings.py` and every endpoint is written as a **function decorated with `@api_view`** — no class-based views or ViewSets at all. This is a deliberate design choice that keeps the code readable.

---

## 2. Models

A **Model** is a Python class that maps to a single database table. Each class attribute becomes a column.

### What a model looks like

```python
# accounts/models.py
from django.db import models

class SellerAccount(models.Model):
    mobile = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts"   # exact table name in Postgres

    def __str__(self):
        return self.mobile
```

### The key field types used in Dukaan

| Field class | SQL type | Dukaan usage |
|---|---|---|
| `CharField(max_length=N)` | VARCHAR(N) | mobile numbers, names |
| `TextField()` | TEXT | address, description |
| `DecimalField(max_digits, decimal_places)` | NUMERIC | mrp, sale_price |
| `URLField()` | VARCHAR(512) | image_url |
| `DateTimeField(auto_now_add=True)` | TIMESTAMPTZ | created_at |
| `ForeignKey(Model, on_delete=...)` | BIGINT + FK constraint | all relations |
| `PositiveIntegerField()` | INT (unsigned) | qty in CartItem |

### ForeignKey — relationships between tables

```python
# stores/models.py
class Store(models.Model):
    account = models.ForeignKey(
        SellerAccount,
        on_delete=models.CASCADE,   # delete store when seller is deleted
        related_name="stores",      # seller.stores.all() works from the other side
    )
```

`on_delete` options you need to know:
- `CASCADE` — deletes this row when the related row is deleted
- `SET_NULL` — sets the FK column to NULL (requires `null=True`)
- `PROTECT` — raises an error, preventing deletion

### unique_together — composite uniqueness

```python
# stores/models.py
class Category(models.Model):
    class Meta:
        unique_together = ("name", "store")
        # "Electronics" can exist in Store A and Store B, but not twice in Store A
```

### Running migrations

After changing any model, always:

```bash
python manage.py makemigrations   # generates migration files
python manage.py migrate          # applies them to the database
```

---

## 3. ModelSerializer

A **Serializer** is the bridge between your Django model and JSON. It validates incoming data and converts outgoing querysets to dictionaries. `ModelSerializer` auto-generates this from the model.

### Basic usage

```python
# accounts/serializers.py
from rest_framework import serializers
from .models import SellerAccount, Customer

class SellerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerAccount
        fields = ["id", "mobile"]   # only expose these columns
```

When you call `SellerAccountSerializer(account).data`, DRF returns:

```json
{"id": 1, "mobile": "9876543210"}
```

### Serializing many objects

```python
accounts = SellerAccount.objects.all()
data = SellerAccountSerializer(accounts, many=True).data
# Returns a list of dicts
```

### Nested serializers (read-only)

In `products/serializers.py`, the category is a nested object, not just an ID:

```python
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)  # nested, not writable

    class Meta:
        model = Product
        fields = ["id", "name", "description", "mrp", "sale_price", "image_url", "category"]
```

Output:
```json
{
  "id": 1,
  "name": "Laptop",
  "category": {"id": 2, "name": "Electronics"}
}
```

### Two serializers for one model

Dukaan uses two serializers for `Product`:

```python
class ProductSerializer(serializers.ModelSerializer):
    """Full detail — includes nested category."""
    category = CategorySerializer(read_only=True)
    class Meta:
        model = Product
        fields = ["id", "name", "description", "mrp", "sale_price", "image_url", "category"]

class ProductBriefSerializer(serializers.ModelSerializer):
    """Lightweight for catalog listings — no description, no category object."""
    class Meta:
        model = Product
        fields = ["id", "name", "image_url", "mrp", "sale_price"]
```

This is a common pattern: use a lean serializer for list endpoints, a full one for detail endpoints.

### Validation

If you add `validate_<fieldname>` methods, DRF calls them before saving:

```python
def validate_mobile(self, value):
    if not value.isdigit():
        raise serializers.ValidationError("Mobile must be numeric")
    return value
```

---

## 4. @api_view

`@api_view` is the DRF decorator that turns a plain Python function into an API endpoint. It:

1. Parses the incoming body as JSON (instead of form data)
2. Returns a DRF `Response` object (not `HttpResponse`)
3. Handles `405 Method Not Allowed` for unlisted HTTP methods
4. Enforces authentication and permissions via `@permission_classes`

### Basic structure

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

@api_view(["POST"])
@permission_classes([AllowAny])
def seller_signup(request):
    # request.data  → parsed JSON body (dict)
    # request.method → "POST"
    # request.auth  → JWT token payload (after authentication)
    # request.user  → Django user (not used in Dukaan — custom auth instead)

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
        {"message": "Signup successful", "account": SellerAccountSerializer(account).data, "token": token},
        status=status.HTTP_201_CREATED,
    )
```

### key things about request.data

`request.data` is DRF's replacement for `request.POST`. It works for JSON, form data, and multipart — you never have to `json.loads()` manually.

```python
# Never do this in DRF:
import json
body = json.loads(request.body)

# Always do this instead:
mobile = request.data.get("mobile")
```

### Multiple HTTP methods in one view

```python
@api_view(["GET", "POST"])
def cart_view(request):
    if request.method == "GET":
        ...
    elif request.method == "POST":
        ...
```

### get_or_create — the ORM pattern Dukaan relies on heavily

```python
account, created = SellerAccount.objects.get_or_create(mobile=mobile)
# created is True if a new row was inserted, False if an existing row was found
```

This is atomic — no race condition between SELECT and INSERT.

---

## 5. Simple JWT

`djangorestframework-simplejwt` is the library Dukaan uses for authentication. A JWT (JSON Web Token) is a signed string that encodes claims (key-value pairs). The server signs it with a secret key; any server that knows the secret can verify it without a database lookup.

### Installation and settings

```python
# settings.py
INSTALLED_APPS = [
    ...
    "rest_framework_simplejwt",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),   # how long access tokens live
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),  # how long refresh tokens live
    "ALGORITHM": "HS256",                          # signing algorithm
    "SIGNING_KEY": os.environ.get("JWT_SECRET_KEY", "jwt-secret-key"),
    "AUTH_HEADER_TYPES": ("Bearer",),              # Authorization: Bearer <token>
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",                    # claim name inside the token
}
```

### A standard JWT payload (decoded)

```json
{
  "token_type": "access",
  "exp": 1721827200,
  "iat": 1719235200,
  "jti": "unique-token-id",
  "user_id": 42,
  "role": "seller"
}
```

The `role` field is a **custom claim** added by Dukaan — SimpleJWT does not add it by default.

### Issuing tokens manually (no username/password)

Dukaan does not use Django's built-in `User` model or SimpleJWT's default `/token/` endpoint. Instead, it issues tokens manually after an OTP check using a helper function:

```python
# utils/helpers.py
from rest_framework_simplejwt.tokens import AccessToken

def make_jwt_for_user(user_id: int, role: str) -> str:
    """Issue a SimpleJWT AccessToken with a custom role claim."""
    token = AccessToken()          # creates a new token with default claims
    token["user_id"] = user_id    # set the standard user identifier
    token["role"] = role          # add our custom claim
    return str(token)             # serialise to signed JWT string
```

### Reading claims in a protected view

Once the request passes `JWTAuthentication`, the decoded payload is available as `request.auth`:

```python
def get_seller(request):
    role = request.auth.get("role") if request.auth else None
    if role != "seller":
        return None, Response({"error": "Seller access only"}, status=403)

    user_id = request.auth.get("user_id")
    try:
        return SellerAccount.objects.get(id=user_id), None
    except SellerAccount.DoesNotExist:
        return None, Response({"error": "Account not found"}, status=404)
```

This pattern replaces a database user table with a lightweight role check — if the token says `"role": "seller"`, the user is a seller.

---

## 6. Role claims

Dukaan uses **a single token with a role claim** instead of two separate token types or two user models. Here is why this matters and how it works end-to-end.

### The flow

```
POST /api/seller/signup/   →   make_jwt_for_user(id=1, role="seller")
POST /api/buyer/login/     →   make_jwt_for_user(id=5, role="buyer")
```

Both tokens are structurally identical JWTs. The only difference is the `role` field inside.

### Enforcing role separation

```python
# In stores/views.py — a seller-only endpoint
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_store(request):
    seller, err = get_seller(request)   # checks role == "seller"
    if err:
        return err
    ...
```

```python
# In orders/views.py — a buyer-only endpoint
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_order(request):
    customer, err = get_customer(request)   # checks role == "buyer"
    if err:
        return err
    ...
```

A seller JWT sent to `POST /api/buyer/order/` will get a `403 Forbidden` because `get_customer()` checks for `role == "buyer"` and finds `"seller"` instead.

---

## 7. Password hashing in Dukaan

> **Important observation:** Dukaan does **not** store passwords at all.

Authentication is OTP-based (mobile number + a one-time code). The OTP validation is bypassed in this implementation — any OTP is accepted — but the design intent is clear: there is no password column in `SellerAccount` or `Customer`.

### Why this matters for your learning

If you were building a traditional username + password API with DRF, you would:

1. Use Django's built-in `AbstractUser` or `AbstractBaseUser` which comes with `set_password()` and `check_password()`.
2. Never store raw passwords — Django hashes them with PBKDF2-SHA256 by default.
3. Use SimpleJWT's built-in `/api/token/` endpoint which calls `authenticate(username, password)`.

### How Django hashes passwords (for reference)

```python
from django.contrib.auth.hashers import make_password, check_password

hashed = make_password("mysecretpassword")
# Returns: "pbkdf2_sha256$600000$salt$hash"

is_valid = check_password("mysecretpassword", hashed)
# Returns: True
```

The hash string encodes the algorithm, iteration count, salt, and hash in one string. Django's `User.set_password()` calls `make_password()` internally.

### Dukaan's equivalent

Dukaan's equivalent of "verifying credentials" is:

```python
account, created = SellerAccount.objects.get_or_create(mobile=mobile)
# If the mobile exists → log in. If not → register. OTP skipped.
```

In production you would replace this with a real OTP verification step (send SMS, compare OTP from cache, then issue token). The token issuance and role structure would remain identical.

---

## 8. Permission classes

DRF permission classes are run after authentication and before the view function body. They decide whether the authenticated (or anonymous) user is allowed to call this endpoint.

### The two main classes used in Dukaan

```python
from rest_framework.permissions import AllowAny, IsAuthenticated
```

| Class | Behaviour |
|---|---|
| `AllowAny` | Anyone can call this endpoint, authenticated or not |
| `IsAuthenticated` | Request must carry a valid JWT, else 401 |
| `IsAuthenticatedOrReadOnly` | GET/HEAD/OPTIONS are open; POST/PUT/PATCH/DELETE require auth |

`IsAuthenticatedOrReadOnly` is the global default in `settings.py`. Individual views override it with `@permission_classes([...])`.

### Decorator stacking order matters

```python
@api_view(["POST"])            # 1. wraps function as DRF view
@permission_classes([AllowAny]) # 2. runs permission check before view body
def seller_signup(request):
    ...
```

Decorators are applied bottom-up, so `@api_view` wraps the outermost layer.

### AllowAny vs removing the decorator

If you omit `@permission_classes`, DRF uses the global default (`IsAuthenticatedOrReadOnly`). Always be explicit about whether an endpoint requires auth — silence defaults to the global setting, which can change.

---

## 9. Settings

Here is every DRF/JWT setting from `dukaan/settings.py` explained line by line.

```python
# ── DRF global defaults ───────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # Every request is checked with JWTAuthentication first.
    # If the header is missing, request.user is AnonymousUser.
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),

    # GET requests work without a token; POST/PUT/PATCH/DELETE require one.
    # Individual views override this with @permission_classes.
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
}

# ── SimpleJWT config ─────────────────────────────────────────────────────────
SIMPLE_JWT = {
    # Access tokens last 30 days (generous for mobile apps; tighten in prod).
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),

    # Refresh tokens last 90 days.
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),

    # HS256 = symmetric HMAC. Both signing and verification use the same key.
    # Use RS256 (asymmetric) in microservice architectures.
    "ALGORITHM": "HS256",

    # The secret used to sign tokens. NEVER hardcode — always use env var.
    "SIGNING_KEY": os.environ.get("JWT_SECRET_KEY", "jwt-secret-key"),

    # Client sends: Authorization: Bearer <token>
    "AUTH_HEADER_TYPES": ("Bearer",),

    # Which model field is stored as the user identifier claim.
    "USER_ID_FIELD": "id",

    # What that claim is named inside the JWT payload.
    "USER_ID_CLAIM": "user_id",
}
```

---

## 10. Quick-reference cheat sheet

### Starting a new DRF endpoint

```python
# 1. Define the model (models.py)
class MyModel(models.Model):
    name = models.CharField(max_length=255)

# 2. Create a serializer (serializers.py)
class MySerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ["id", "name"]

# 3. Write the view (views.py)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def my_view(request):
    if request.method == "GET":
        items = MyModel.objects.all()
        return Response(MySerializer(items, many=True).data)
    if request.method == "POST":
        name = request.data.get("name")
        obj = MyModel.objects.create(name=name)
        return Response(MySerializer(obj).data, status=201)

# 4. Register the URL (urls.py)
urlpatterns = [
    path("my-endpoint/", views.my_view, name="my-endpoint"),
]
```

### Reading JWT claims in a view

```python
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def protected_view(request):
    role = request.auth.get("role")       # custom claim
    user_id = request.auth.get("user_id") # standard claim
    ...
```

### Common HTTP status shortcuts

```python
from rest_framework import status

status.HTTP_200_OK           # 200
status.HTTP_201_CREATED      # 201
status.HTTP_400_BAD_REQUEST  # 400
status.HTTP_401_UNAUTHORIZED # 401
status.HTTP_403_FORBIDDEN    # 403
status.HTTP_404_NOT_FOUND    # 404
```

### ORM patterns used in Dukaan

```python
# Get or create atomically
obj, created = Model.objects.get_or_create(mobile=mobile)

# Filter with annotation
from django.db.models import Count
qs = Category.objects.filter(store=store).annotate(product_count=Count("products")).order_by("-product_count")

# Safe get with 404 handling
try:
    store = Store.objects.get(id=store_id, account=seller)
except Store.DoesNotExist:
    return Response({"error": "Not found"}, status=404)

# Null FK filter
uncategorised = Product.objects.filter(store=store, category__isnull=True)
```

---

*This tutorial is grounded in the Dukaan codebase. Every snippet is real code, not a toy example. Refer back to `django.md` alongside this document.*
