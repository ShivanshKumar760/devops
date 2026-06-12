# Django REST Framework — Complete tutorial with `@api_view`

> **What you will build by the end of this tutorial**
> A fully working **Blog API** with user registration (hashed password), login (JWT), and protected blog post CRUD — all written with `@api_view` function-based views.

---

## Table of contents

1. [Simple HTTP verbs — GET, POST, PUT, PATCH, DELETE](#1-simple-http-verbs)
2. [CRUD API with a real database](#2-crud-api-with-a-real-database)
3. [Models — your database table in Python](#3-models)
4. [Serializer vs ModelSerializer](#4-serializer-vs-modelserializer)
5. [How `.save()` works internally](#5-how-save-works-internally)
6. [Simple JWT — how authentication works internally](#6-simple-jwt-internals)
7. [Blog API — full implementation](#7-blog-api-full-implementation)

---

## 1. Simple HTTP verbs

Before touching a database, understand how DRF maps HTTP verbs to intent.

| Verb | Meaning | Typical use |
|---|---|---|
| `GET` | Read | Fetch a resource or a list |
| `POST` | Create | Submit new data |
| `PUT` | Full replace | Replace an entire resource |
| `PATCH` | Partial update | Change one or two fields |
| `DELETE` | Remove | Delete a resource |

### Setup — install DRF and wire it up

```bash
pip install django djangorestframework
django-admin startproject myproject
cd myproject
python manage.py startapp demo
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    "rest_framework",
    "demo",
]
```

### The simplest possible view — in-memory data, no database

```python
# demo/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# A fake in-memory store so you can focus on the HTTP layer
ITEMS = [
    {"id": 1, "name": "Laptop",  "price": 50000},
    {"id": 2, "name": "Monitor", "price": 15000},
]

# ── GET — return every item ───────────────────────────────────────────────────
@api_view(["GET"])
def item_list(request):
    return Response(ITEMS)


# ── POST — add a new item ─────────────────────────────────────────────────────
@api_view(["POST"])
def item_create(request):
    # request.data is the parsed JSON body — no json.loads() needed
    name  = request.data.get("name")
    price = request.data.get("price")

    if not name or price is None:
        return Response(
            {"error": "name and price are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_item = {"id": len(ITEMS) + 1, "name": name, "price": price}
    ITEMS.append(new_item)
    return Response(new_item, status=status.HTTP_201_CREATED)


# ── GET single / PUT / PATCH / DELETE — all on one item ──────────────────────
@api_view(["GET", "PUT", "PATCH", "DELETE"])
def item_detail(request, pk):
    # Find the item or 404
    item = next((i for i in ITEMS if i["id"] == pk), None)
    if item is None:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(item)

    if request.method == "PUT":
        # Full replace — both fields required
        item["name"]  = request.data.get("name",  item["name"])
        item["price"] = request.data.get("price", item["price"])
        return Response(item)

    if request.method == "PATCH":
        # Partial update — only provided fields change
        if "name"  in request.data: item["name"]  = request.data["name"]
        if "price" in request.data: item["price"] = request.data["price"]
        return Response(item)

    if request.method == "DELETE":
        ITEMS.remove(item)
        return Response(status=status.HTTP_204_NO_CONTENT)
```

```python
# demo/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("items/",      views.item_list,   name="item-list"),
    path("items/",      views.item_create, name="item-create"),
    path("items/<int:pk>/", views.item_detail, name="item-detail"),
]
```

```python
# myproject/urls.py
from django.urls import path, include

urlpatterns = [
    path("api/", include("demo.urls")),
]
```

### Test it with curl

```bash
# List all items
curl http://localhost:8000/api/items/

# Create
curl -X POST http://localhost:8000/api/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Keyboard", "price": 3000}'

# Full replace
curl -X PUT http://localhost:8000/api/items/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Laptop Pro", "price": 75000}'

# Partial update
curl -X PATCH http://localhost:8000/api/items/1/ \
  -H "Content-Type: application/json" \
  -d '{"price": 80000}'

# Delete
curl -X DELETE http://localhost:8000/api/items/1/
```

---

## 2. CRUD API with a real database

Now replace the in-memory list with PostgreSQL (or SQLite for local dev). This introduces the **Model → Serializer → View → URL** pattern that Django enforces.

### The four-layer pattern

```
Request
   ↓
urls.py         — maps URL + method to a view function
   ↓
views.py        — reads request.data, calls ORM, returns Response
   ↓
serializers.py  — converts ORM objects ↔ Python dicts ↔ JSON
   ↓
models.py       — describes the database table
   ↓
Database (Postgres / SQLite)
```

---

## 3. Models

A **Model** is a Python class where each attribute is a database column. Django generates and runs the SQL for you.

```python
# demo/models.py
from django.db import models


class Product(models.Model):
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    in_stock    = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)  # set once on INSERT
    updated_at  = models.DateTimeField(auto_now=True)      # updated on every save

    class Meta:
        db_table = "products"     # exact table name; defaults to demo_product
        ordering = ["-created_at"] # default queryset order

    def __str__(self):
        return self.name
```

```bash
python manage.py makemigrations demo   # generates demo/migrations/0001_initial.py
python manage.py migrate               # runs SQL: CREATE TABLE products (...)
```

### Common field types

```python
models.CharField(max_length=N)              # VARCHAR(N)       — short strings
models.TextField()                          # TEXT             — long strings
models.IntegerField()                       # INTEGER
models.DecimalField(max_digits, decimal_places)  # NUMERIC     — money
models.FloatField()                         # FLOAT
models.BooleanField(default=True)           # BOOLEAN
models.DateTimeField(auto_now_add=True)     # TIMESTAMPTZ      — timestamps
models.URLField()                           # VARCHAR(200)     — URLs
models.EmailField()                         # VARCHAR(254)     — emails
models.ForeignKey(OtherModel, on_delete=models.CASCADE)  # FK
models.OneToOneField(OtherModel, on_delete=models.CASCADE)
models.ManyToManyField(OtherModel)
```

---

## 4. Serializer vs ModelSerializer

A **Serializer** does two jobs:

1. **Deserialization** — validates incoming JSON and converts it to Python data / model instances.
2. **Serialization** — converts model instances (or querysets) to Python dicts that DRF renders as JSON.

There are two ways to write one.

### 4a. `Serializer` — the manual way

You declare every field explicitly. Gives maximum control.

```python
# demo/serializers.py
from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.Serializer):
    """
    Manual serializer — every field declared by hand.
    Use when you need full control over validation or computed fields.
    """
    id          = serializers.IntegerField(read_only=True)
    name        = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="")
    price       = serializers.DecimalField(max_digits=10, decimal_places=2)
    in_stock    = serializers.BooleanField(default=True)

    # ── create() is called by .save() when there is no instance ──────────────
    def create(self, validated_data):
        """
        validated_data is the dict that passed all field-level validations.
        We manually call the ORM here.
        """
        return Product.objects.create(**validated_data)

    # ── update() is called by .save() when an instance is passed in ──────────
    def update(self, instance, validated_data):
        """
        instance is the existing Product row.
        We update only the fields that were provided.
        """
        instance.name        = validated_data.get("name",        instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.price       = validated_data.get("price",       instance.price)
        instance.in_stock    = validated_data.get("in_stock",    instance.in_stock)
        instance.save()   # triggers UPDATE SQL
        return instance
```

### 4b. `ModelSerializer` — the automatic way

`ModelSerializer` inspects the model and generates fields, `create()`, and `update()` automatically. You only declare what differs from the default.

```python
class ProductModelSerializer(serializers.ModelSerializer):
    """
    ModelSerializer — fields and create/update auto-generated from the model.
    Use this for 95% of cases. Override only what needs custom logic.
    """
    class Meta:
        model  = Product
        fields = ["id", "name", "description", "price", "in_stock", "created_at"]
        # OR: fields = "__all__"   — exposes every column (avoid in production)
        read_only_fields = ["id", "created_at"]  # never written by incoming data
```

### Side-by-side comparison

| Feature | `Serializer` | `ModelSerializer` |
|---|---|---|
| Field declaration | Manual | Auto from model |
| `create()` | You write it | Auto-generated |
| `update()` | You write it | Auto-generated |
| Custom validation | Both support it | Both support it |
| Nested objects | Manual | Manual (same effort) |
| When to use | Non-model data, login forms | Standard model CRUD |

### Using a serializer in a view

```python
# Deserializing (incoming POST body → validated data)
serializer = ProductModelSerializer(data=request.data)
if serializer.is_valid():
    product = serializer.save()        # calls create() internally
else:
    return Response(serializer.errors, status=400)

# Serializing (model instance → JSON-ready dict)
product = Product.objects.get(pk=1)
data = ProductModelSerializer(product).data   # .data triggers serialization

# Serializing a queryset
products = Product.objects.all()
data = ProductModelSerializer(products, many=True).data
```

### Field-level validation

```python
class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = ["id", "name", "price"]

    def validate_price(self, value):
        """Runs automatically when is_valid() is called."""
        if value <= 0:
            raise serializers.ValidationError("Price must be positive")
        return value

    def validate(self, data):
        """Cross-field validation — runs after all field-level validators."""
        if data["name"].lower() == "free" and data["price"] > 0:
            raise serializers.ValidationError("Free items must have price 0")
        return data
```

---

## 5. How `.save()` works internally

`.save()` is the method you call on a **validated serializer instance**. Understanding what happens inside it removes all the magic.

### The decision tree inside `.save()`

```python
# Simplified version of what DRF's BaseSerializer.save() actually does:

def save(self, **kwargs):
    # 1. Merge any extra kwargs into validated_data
    validated_data = {**self.validated_data, **kwargs}

    # 2. Was an instance passed to the serializer constructor?
    if self.instance is not None:
        # YES → this is an UPDATE
        self.instance = self.update(self.instance, validated_data)
    else:
        # NO  → this is a CREATE
        self.instance = self.create(validated_data)

    return self.instance
```

So `.save()` dispatches to either `create()` or `update()` depending on whether you passed an existing object to the serializer.

### Concrete examples

```python
# ── CREATE: no instance → calls create() ─────────────────────────────────────
serializer = ProductModelSerializer(data=request.data)
#                                   ^^^^ no `instance` argument
serializer.is_valid(raise_exception=True)
product = serializer.save()
# Internally: Product.objects.create(**validated_data)
# SQL: INSERT INTO products (name, price, ...) VALUES (...)


# ── UPDATE: instance provided → calls update() ───────────────────────────────
product = Product.objects.get(pk=pk)
serializer = ProductModelSerializer(product, data=request.data, partial=True)
#                                   ^^^^^^^ instance IS provided
serializer.is_valid(raise_exception=True)
product = serializer.save()
# Internally: instance.name = ...; instance.save()
# SQL: UPDATE products SET name=... WHERE id=...


# ── Passing extra data into save() ───────────────────────────────────────────
# Anything in kwargs gets merged into validated_data before create/update.
# This is how you attach the logged-in user without putting it in the request body:
serializer.save(author=request.user)
# Inside create(): Product.objects.create(name=..., price=..., author=<User>)
```

### What `ModelSerializer.create()` does automatically

```python
# This is the actual source of ModelSerializer.create():
def create(self, validated_data):
    # Handles M2M fields separately — can't pass them to objects.create()
    info = model_meta.get_field_info(ModelClass)
    many_to_many = {}
    for field_name, relation_info in info.relations.items():
        if relation_info.to_many and (field_name in validated_data):
            many_to_many[field_name] = validated_data.pop(field_name)

    instance = ModelClass._default_manager.create(**validated_data)  # the actual INSERT

    for field_name, value in many_to_many.items():
        field = getattr(instance, field_name)
        field.set(value)   # M2M INSERT

    return instance
```

### What `ModelSerializer.update()` does automatically

```python
def update(self, instance, validated_data):
    # Raises error on nested writable serializers (you must handle those yourself)
    raise_errors_on_nested_writes("update", self, validated_data)

    for attr, value in validated_data.items():
        setattr(instance, attr, value)   # instance.name = "new name" etc.

    instance.save()   # triggers UPDATE SQL
    return instance
```

### `raise_exception=True` — shorthand for error responses

```python
# Without it:
if not serializer.is_valid():
    return Response(serializer.errors, status=400)

# With it — raises ValidationError → DRF converts to 400 automatically:
serializer.is_valid(raise_exception=True)
# No if/return needed
```

### Full CRUD view using ModelSerializer

```python
# demo/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductModelSerializer


@api_view(["GET", "POST"])
def product_list(request):
    if request.method == "GET":
        products = Product.objects.all()
        serializer = ProductModelSerializer(products, many=True)
        return Response(serializer.data)

    if request.method == "POST":
        serializer = ProductModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()              # calls create()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(ProductModelSerializer(product).data)

    if request.method == "PUT":
        # Full update — all fields required
        serializer = ProductModelSerializer(product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()              # calls update()
        return Response(serializer.data)

    if request.method == "PATCH":
        # Partial update — only provided fields change
        serializer = ProductModelSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()              # calls update() with partial validated_data
        return Response(serializer.data)

    if request.method == "DELETE":
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

---

## 6. Simple JWT internals

This section goes deep into what actually happens when a JWT is issued and validated. You need this understanding to customise authentication in the Blog API.

### What a JWT is

A JWT is three Base64url-encoded segments joined by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9   ← header
.
eyJ1c2VyX2lkIjo0MiwidXNlcm5hbWUiOiJhbGljZSJ9  ← payload (claims)
.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c   ← signature
```

Decode the payload:
```json
{
  "token_type": "access",
  "exp": 1719235200,
  "iat": 1716643200,
  "jti": "3f8e1b2a4c",
  "user_id": 42
}
```

The **signature** is `HMAC-SHA256(base64(header) + "." + base64(payload), SECRET_KEY)`. The server re-computes this on every request. If the result matches the third segment, the token is genuine and unmodified.

### `TokenObtainPairView` — the login endpoint

`TokenObtainPairView` is SimpleJWT's built-in class-based view that handles `POST /api/token/`. Its job:

1. Receive `{"username": "alice", "password": "secret"}`
2. Delegate validation to `TokenObtainPairSerializer`
3. Return `{"access": "...", "refresh": "..."}`

```python
# The actual simplified source of TokenObtainPairView:
class TokenObtainPairView(TokenViewBase):
    serializer_class = TokenObtainPairSerializer
```

It delegates everything to the serializer. The view itself is thin.

### `TokenObtainPairSerializer` — where authentication actually happens

```python
# Simplified version of the actual DRF SimpleJWT source:
class TokenObtainPairSerializer(TokenObtainSerializer):

    @classmethod
    def get_token(cls, user):
        """Builds the token payload. Override this to add custom claims."""
        token = RefreshToken.for_user(user)
        # token["username"] = user.username   ← add custom claims here
        return token

    def validate(self, attrs):
        # 1. Call Django's authenticate() — checks username + hashed password
        data = super().validate(attrs)

        # 2. Build access + refresh tokens
        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"]  = str(refresh.access_token)
        return data
```

### The `authenticate()` function

`django.contrib.auth.authenticate(username=..., password=...)` is the low-level credential check. It:

1. Loops through every class in `AUTHENTICATION_BACKENDS` (default: `ModelBackend`)
2. `ModelBackend` fetches the user by username from the database
3. Calls `user.check_password(raw_password)` — which re-hashes the input and compares it to the stored hash
4. Returns the user object if successful, `None` otherwise

```python
from django.contrib.auth import authenticate

user = authenticate(request, username="alice", password="secret123")
if user is None:
    # Bad credentials
    raise AuthenticationFailed("Invalid username or password")
# user is the authenticated User instance
```

### `JWTAuthentication` — how it validates tokens on every request

`JWTAuthentication` is set as the `DEFAULT_AUTHENTICATION_CLASSES` in DRF settings. DRF calls it at the start of every request, before your view function runs.

```python
# Simplified version of the actual JWTAuthentication source:
class JWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        """
        Called by DRF on every incoming request.
        Returns (user, token) tuple or None.
        """
        # 1. Look for "Authorization: Bearer <token>" header
        header = self.get_header(request)
        if header is None:
            return None   # no token → anonymous request

        # 2. Extract the raw token string after "Bearer "
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        # 3. Decode and verify the JWT
        #    - checks signature using SIGNING_KEY
        #    - checks exp (not expired)
        #    - checks token_type == "access"
        validated_token = self.get_validated_token(raw_token)

        # 4. Fetch the user from the database using user_id claim
        user = self.get_user(validated_token)

        return (user, validated_token)   # → request.user, request.auth
```

### When exactly does DRF call `JWTAuthentication`?

```
Incoming HTTP request
       ↓
Django WSGI handler
       ↓
Django middleware stack (CORS, Security, etc.)
       ↓
DRF APIView.dispatch()  ←─ the entry point for all DRF views
       ↓
APIView.initial()
       ↓
   ┌── APIView.perform_authentication()
   │        calls request.user  (lazy property)
   │        which calls Authenticator.authenticate()  ← JWTAuthentication runs here
   │
   ├── APIView.check_permissions()
   │        calls permission.has_permission(request, view)  ← IsAuthenticated runs here
   │
   └── APIView.check_throttles()
       ↓
Your @api_view function body runs
```

Authentication is **lazy** — `request.user` is not evaluated until something accesses it. The first access (usually in `check_permissions`) triggers `JWTAuthentication.authenticate()`.

### `IsAuthenticated` — the permission class

```python
# The actual source — it's this simple:
class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
```

If `JWTAuthentication` returned `None` (no token), `request.user` is `AnonymousUser` whose `is_authenticated` is `False` → 401 Unauthorized.

If the token is invalid or expired, `JWTAuthentication` raises `AuthenticationFailed` → 401.

If the token is valid but `is_authenticated` is False somehow → 403 Forbidden.

### The full token lifecycle

```
1. Client POSTs credentials → TokenObtainPairSerializer.validate()
        → authenticate(username, password)
        → check_password() compares PBKDF2 hashes
        → RefreshToken.for_user(user) builds JWT payload
        → Returns {access: "...", refresh: "..."}

2. Client stores access token locally (memory / secure storage)

3. Client sends: Authorization: Bearer <access_token>

4. JWTAuthentication.authenticate()
        → decode JWT, verify HS256 signature
        → check exp claim
        → fetch User from DB by user_id claim
        → returns (user, token)

5. IsAuthenticated checks request.user.is_authenticated → True

6. Your view runs with request.user = the authenticated User
```

---

## 7. Blog API — full implementation

We now build a complete Blog API that demonstrates everything above. It uses Django's built-in `User` model.

### Features

- `POST /api/auth/register/` — create account, password hashed with PBKDF2
- `POST /api/auth/login/` — returns custom JWT with `username` claim
- `GET /api/posts/` — public list of all posts
- `POST /api/posts/` — create a post (auth required)
- `GET /api/posts/<id>/` — get single post (public)
- `PUT/PATCH /api/posts/<id>/` — update own post (auth + ownership)
- `DELETE /api/posts/<id>/` — delete own post (auth + ownership)

### Step 1 — install packages

```bash
pip install django djangorestframework djangorestframework-simplejwt
django-admin startproject blogproject
cd blogproject
python manage.py startapp blog
```

### Step 2 — settings

```python
# blogproject/settings.py
from datetime import timedelta

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",          # provides the built-in User model
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "blog",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # Every request is checked for a Bearer token.
        # If valid → request.user is set. If missing → AnonymousUser.
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        # GET requests are open. Mutations need a valid token.
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_CLAIM": "user_id",
}
```

### Step 3 — model

```python
# blog/models.py
from django.db import models
from django.contrib.auth.models import User   # built-in User: id, username, email, password


class Post(models.Model):
    author     = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",    # user.posts.all()
    )
    title      = models.CharField(max_length=255)
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "posts"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
```

```bash
python manage.py makemigrations blog
python manage.py migrate
```

### Step 4 — serializers

```python
# blog/serializers.py
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Post


# ── Registration serializer ───────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    """
    Uses ModelSerializer on Django's built-in User model.
    Password field is write-only — it will never appear in serialized output.
    """
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta:
        model  = User
        fields = ["id", "username", "email", "password", "password2"]

    def validate_password(self, value):
        """
        Run Django's built-in password validators:
        - minimum length, not too common, not entirely numeric, etc.
        Configured in settings.AUTH_PASSWORD_VALIDATORS.
        """
        validate_password(value)
        return value

    def validate(self, data):
        """Cross-field: both password fields must match."""
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match"})
        return data

    def create(self, validated_data):
        """
        We must NOT call User.objects.create(**validated_data) directly.
        That would store the raw password as plain text.

        User.objects.create_user() calls user.set_password(raw) internally,
        which calls make_password(raw) → PBKDF2-SHA256 hash stored in the DB.
        """
        validated_data.pop("password2")   # remove confirm field — not a model column
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],   # hashed internally
        )
        return user


# ── Login serializer ──────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    """
    Plain Serializer (not ModelSerializer) because login is not a model operation.
    We validate credentials and build JWT tokens manually.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate

        # authenticate() fetches user by username, then calls check_password()
        # check_password() hashes the input and compares to the stored PBKDF2 hash
        user = authenticate(username=data["username"], password=data["password"])

        if user is None:
            raise serializers.ValidationError("Invalid username or password")

        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled")

        # Build JWT tokens manually
        refresh = RefreshToken.for_user(user)

        # Add custom claims to the access token payload
        refresh.access_token["username"] = user.username
        refresh.access_token["email"]    = user.email

        return {
            "user_id":      user.id,
            "username":     user.username,
            "email":        user.email,
            "access_token":  str(refresh.access_token),
            "refresh_token": str(refresh),
        }


# ── Post serializers ──────────────────────────────────────────────────────────

class PostSerializer(serializers.ModelSerializer):
    """
    author is read-only — set by the view from request.user, never from request body.
    author_username is a computed field (SerializerMethodField).
    """
    author_username = serializers.SerializerMethodField()
    author          = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model  = Post
        fields = ["id", "author", "author_username", "title", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_author_username(self, obj):
        """SerializerMethodField — return any value you compute."""
        return obj.author.username
```

### Step 5 — views

```python
# blog/views.py
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Post
from .serializers import RegisterSerializer, LoginSerializer, PostSerializer


# ────────────────────────────────────────────────────────────────────────────
# Auth endpoints
# ────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])   # override global default — no token needed
def register(request):
    """
    POST /api/auth/register/
    Body: { "username": "alice", "email": "alice@example.com",
            "password": "securepass1", "password2": "securepass1" }
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)   # 400 with errors if invalid

    # .save() calls our custom create() which calls User.objects.create_user()
    # Password is hashed inside create_user() before hitting the database.
    user = serializer.save()

    return Response(
        {
            "message":  "Account created successfully",
            "user_id":  user.id,
            "username": user.username,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/auth/login/
    Body: { "username": "alice", "password": "securepass1" }

    The LoginSerializer.validate() calls authenticate() → check_password() → tokens.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # validated_data is the dict returned by LoginSerializer.validate()
    return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ────────────────────────────────────────────────────────────────────────────
# Post endpoints
# ────────────────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def post_list(request):
    """
    GET  /api/posts/  — public, returns all posts
    POST /api/posts/  — requires JWT, creates a post
    """
    if request.method == "GET":
        posts      = Post.objects.select_related("author").all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    # POST — permission enforced by IsAuthenticatedOrReadOnly global default
    # If no valid JWT → DRF already returned 401 before reaching this line
    serializer = PostSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Pass author=request.user as an extra kwarg.
    # .save() merges it into validated_data before calling create().
    serializer.save(author=request.user)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def post_detail(request, pk):
    """
    GET    /api/posts/<pk>/  — public
    PUT    /api/posts/<pk>/  — author only
    PATCH  /api/posts/<pk>/  — author only
    DELETE /api/posts/<pk>/  — author only
    """
    try:
        post = Post.objects.select_related("author").get(pk=pk)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(PostSerializer(post).data)

    # Ownership check — only the author can mutate their post
    # request.user is set by JWTAuthentication at this point
    if post.author != request.user:
        return Response(
            {"error": "You can only edit your own posts"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "PUT":
        serializer = PostSerializer(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()   # calls update() — sets fields, calls instance.save()
        return Response(serializer.data)

    if request.method == "PATCH":
        serializer = PostSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    if request.method == "DELETE":
        post.delete()   # Django ORM DELETE SQL
        return Response(
            {"message": "Post deleted"},
            status=status.HTTP_204_NO_CONTENT,
        )
```

### Step 6 — URLs

```python
# blog/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("auth/register/", views.register,    name="register"),
    path("auth/login/",    views.login,       name="login"),

    # Posts
    path("posts/",         views.post_list,   name="post-list"),
    path("posts/<int:pk>/", views.post_detail, name="post-detail"),
]
```

```python
# blogproject/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("blog.urls")),
]
```

### Step 7 — run and test

```bash
python manage.py migrate
python manage.py runserver
```

#### Register

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "securepass1",
    "password2": "securepass1"
  }'
```

Response:
```json
{
  "message": "Account created successfully",
  "user_id": 1,
  "username": "alice"
}
```

#### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "securepass1"}'
```

Response:
```json
{
  "user_id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Create a post (authenticated)

```bash
curl -X POST http://localhost:8000/api/posts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"title": "My first post", "body": "Hello world!"}'
```

Response:
```json
{
  "id": 1,
  "author": 1,
  "author_username": "alice",
  "title": "My first post",
  "body": "Hello world!",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

#### Get all posts (no token needed)

```bash
curl http://localhost:8000/api/posts/
```

#### Update own post

```bash
curl -X PATCH http://localhost:8000/api/posts/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"title": "Updated title"}'
```

#### Delete own post

```bash
curl -X DELETE http://localhost:8000/api/posts/1/ \
  -H "Authorization: Bearer <access_token>"
```

---

## How password hashing works in this API

When `register` is called:

```
request.data["password"] = "securepass1"   ← raw, plain text
        ↓
RegisterSerializer.validate_password()     ← checks complexity rules
        ↓
RegisterSerializer.create()
        ↓
User.objects.create_user(password="securepass1")
        ↓
user.set_password("securepass1")
        ↓
make_password("securepass1")
        ↓
PBKDF2_SHA256(iterations=600000, salt=random, password)
        ↓
Stored in DB: "pbkdf2_sha256$600000$Wg1KKl...$hashed..."
                            ^^^^^^^^^^^^^^^^ NEVER the raw password
```

When `login` is called:

```
request.data["password"] = "securepass1"   ← raw, plain text
        ↓
LoginSerializer.validate()
        ↓
authenticate(username="alice", password="securepass1")
        ↓
ModelBackend fetches User from DB
        ↓
user.check_password("securepass1")
        ↓
hash("securepass1") using stored salt + algorithm
        ↓
compare to stored hash — True or False
        ↓
True → user returned → RefreshToken.for_user(user) → JWT issued
```

---

## Full project structure

```
blogproject/
├── blogproject/
│   ├── settings.py
│   └── urls.py
├── blog/
│   ├── models.py        ← Post model
│   ├── serializers.py   ← Register, Login, Post serializers
│   ├── views.py         ← @api_view functions
│   └── urls.py          ← URL patterns
└── manage.py
```

---

## Quick mental model — the whole flow in one diagram

```
POST /api/auth/register/
  → RegisterSerializer(data=request.data)
  → .is_valid()  runs field validators + validate()
  → .save()      calls create() → create_user() → PBKDF2 hash → INSERT

POST /api/auth/login/
  → LoginSerializer(data=request.data)
  → .is_valid()  calls validate() → authenticate() → check_password()
  → .validated_data  contains {access_token, refresh_token}

POST /api/posts/  (with Bearer token)
  → JWTAuthentication.authenticate()  verifies signature + exp
  → IsAuthenticatedOrReadOnly.has_permission()  True
  → PostSerializer(data=request.data).is_valid()
  → .save(author=request.user)  calls create() → INSERT INTO posts
  → 201 Created

GET /api/posts/  (no token)
  → JWTAuthentication returns None → request.user = AnonymousUser
  → IsAuthenticatedOrReadOnly allows GET → view runs → SELECT * FROM posts
  → 200 OK
```
