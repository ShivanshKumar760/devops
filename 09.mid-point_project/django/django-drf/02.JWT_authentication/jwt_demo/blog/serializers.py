from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Post

# ── Registration serializer ───────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label="Confirm password")

    class Meta:
        model = User
        fields = ["id" , "username" , "email" , "password" , "password2"]

    def validate_password(self, value):
        validate_password(value)
        return value
    
    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match"})
        return data
    def create(self , validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(
            username = validated_data["username"],
            email = validated_data.get("email" , ""),
            password = validated_data["password"]
        )
        return user
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self,data):
        from django.contrib.auth import authenticate
        user = authenticate(username=data["username"] , password=data["password"])
        if user is None:
            raise serializers.ValidationError("Invalid username or password")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        
        refresh = RefreshToken.for_user(user)

        refresh.access_token["username"] = user.username
        refresh.access_token["email"] = user.email

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }
    

class PostSerializer(serializers.ModelSerializer):
    author          = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model  = Post
        fields = ["id", "author", "title", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_author_username(self, obj):
        """SerializerMethodField — return any value you compute."""
        return obj.author.username