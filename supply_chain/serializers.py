
from rest_framework import serializers

from .models import (
    Product,
    Warehouse,
    StockLevel,
    FulfilmentOrder,
    OrderItem,
)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class StockLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLevel
        fields = "__all__"
        read_only_fields = ("id", "updated_at")


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class FulfilmentOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    created_by = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = FulfilmentOrder
        fields = (
            "id",
            "created_by",
            "status",
            "shipping_address",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")
