
from django.contrib import admin
from .models import (
    Product,
    Warehouse,
    StockLevel,
    FulfilmentOrder,
    OrderItem,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "unit_price", "reorder_level", "is_active")
    search_fields = ("sku", "name")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "location")
    search_fields = ("code", "name")


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "quantity", "reserved_quantity")
    list_filter = ("warehouse",)
    search_fields = ("product__sku", "product__name", "warehouse__code")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(FulfilmentOrder)
class FulfilmentOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_by", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "created_by__username")
    inlines = [OrderItemInline]
