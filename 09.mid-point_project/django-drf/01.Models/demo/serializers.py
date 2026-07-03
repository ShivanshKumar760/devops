from rest_framework import serializers
from .models import Product

# class ProductModelSerializer(serializers.ModelSerializer):
#     """
#     ModelSerializer — fields and create/update auto-generated from the model.
#     Use this for 95% of cases. Override only what needs custom logic.
#     """
#     class Meta:
#         model  = Product
#         fields = ["id", "name", "description", "price", "in_stock", "created_at","updated_at"]
#         # OR: fields = "__all__"   — exposes every column (avoid in production)
#         read_only_fields = ["id", "created_at","updated_at"]  # never written by incoming data

class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = ["id", "name", "price"]

    def validate_price(self, value):
        """Runs automatically when is_valid() is called."""
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value

    def validate(self, data):
        """Cross-field validation — runs after all field-level validators."""
        if data["name"].lower() == "free" and data["price"] > 0:
            raise serializers.ValidationError("Free items must have price 0")
        return data