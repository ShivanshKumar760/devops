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
    #.save() merges it into validated_data before calling create().
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
    