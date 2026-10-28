
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=150, db_index=True)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    reorder_level = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.sku} - {self.name}"


class Warehouse(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class StockLevel(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_levels",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock_levels",
    )
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "warehouse"],
                name="unique_product_warehouse_stock",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    reserved_quantity__lte=models.F("quantity")
                ),
                name="reserved_stock_not_above_quantity",
            ),
        ]
        indexes = [
            models.Index(fields=["warehouse", "product"]),
        ]

    def __str__(self):
        return f"{self.product.sku} at {self.warehouse.code}"


class FulfilmentOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="fulfilment_orders",
    )
    products = models.ManyToManyField(
        Product,
        through="OrderItem",
        related_name="fulfilment_orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    shipping_address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        FulfilmentOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="unique_product_per_order",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_at_least_one",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="order_item_price_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.product.sku} x {self.quantity}"
