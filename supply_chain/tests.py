
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    Product,
    Warehouse,
    StockLevel,
    FulfilmentOrder,
    OrderItem,
)

User = get_user_model()


class SupplyChainModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="customer",
            password="TestPass123!",
        )
        self.product = Product.objects.create(
            sku="TEST-001",
            name="Test Laptop",
            unit_price=Decimal("1000.00"),
        )
        self.warehouse = Warehouse.objects.create(
            code="WH-001",
            name="Main Warehouse",
            location="Johannesburg",
        )

    def test_product_string_and_ordering(self):
        self.assertEqual(str(self.product), "TEST-001 - Test Laptop")
        self.assertEqual(Product.objects.first(), self.product)

    def test_warehouse_string(self):
        self.assertEqual(str(self.warehouse), "WH-001 - Main Warehouse")

    def test_stock_level_relationships(self):
        stock = StockLevel.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=10,
            reserved_quantity=3,
        )
        self.assertEqual(stock.product, self.product)
        self.assertEqual(stock.warehouse, self.warehouse)
        self.assertEqual(str(stock), "TEST-001 at WH-001")

    def test_duplicate_product_warehouse_stock_is_rejected(self):
        StockLevel.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=10,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StockLevel.objects.create(
                    product=self.product,
                    warehouse=self.warehouse,
                    quantity=5,
                )

    def test_reserved_stock_cannot_exceed_quantity(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StockLevel.objects.create(
                    product=self.product,
                    warehouse=self.warehouse,
                    quantity=2,
                    reserved_quantity=5,
                )

    def test_order_and_order_item_relationships(self):
        order = FulfilmentOrder.objects.create(
            created_by=self.user,
            shipping_address="Test address",
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=Decimal("1000.00"),
        )
        self.assertEqual(order.products.count(), 1)
        self.assertEqual(order.items.first(), item)
        self.assertEqual(str(item), "TEST-001 x 2")
        self.assertIn("pending", str(order))

    def test_order_item_quantity_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                order = FulfilmentOrder.objects.create(
                    created_by=self.user,
                    shipping_address="Test address",
                )
                OrderItem.objects.create(
                    order=order,
                    product=self.product,
                    quantity=0,
                    unit_price=Decimal("1000.00"),
                )


class SupplyChainAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="adminuser",
            password="AdminPass123!",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="standarduser",
            password="UserPass123!",
        )
        self.product = Product.objects.create(
            sku="API-001",
            name="API Laptop",
            unit_price=Decimal("1500.00"),
        )
        self.warehouse = Warehouse.objects.create(
            code="API-WH",
            name="API Warehouse",
            location="Cape Town",
        )

    def test_health_endpoint(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "healthy")
        self.assertEqual(response.data["database"], "connected")
        self.assertIn("uptime_seconds", response.data)

    def test_api_health_endpoint(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_product_request_is_rejected(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.data)

    def test_standard_user_can_list_products(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_standard_user_cannot_create_product(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/products/",
            {
                "sku": "DENIED-001",
                "name": "Denied Product",
                "unit_price": "100.00",
                "reorder_level": 5,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_product(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/products/",
            {
                "sku": "NEW-001",
                "name": "New Product",
                "unit_price": "200.00",
                "reorder_level": 5,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_admin_can_update_and_delete_product(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/products/{self.product.id}/",
            {"name": "Updated Laptop"},
        )
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Updated Laptop")

        response = self.client.delete(
            f"/api/products/{self.product.id}/"
        )
        self.assertEqual(response.status_code, 204)

    def test_product_validation_returns_standard_error(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/products/",
            {
                "sku": "BAD-001",
                "name": "Invalid Price",
                "unit_price": "-5.00",
                "reorder_level": 1,
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_admin_can_manage_warehouses(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/warehouses/",
            {
                "code": "WH-NEW",
                "name": "New Warehouse",
                "location": "Durban",
            },
        )
        self.assertEqual(response.status_code, 201)

        warehouse_id = response.data["id"]
        response = self.client.get(f"/api/warehouses/{warehouse_id}/")
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_stock_level(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/stock-levels/",
            {
                "product": self.product.id,
                "warehouse": self.warehouse.id,
                "quantity": 20,
                "reserved_quantity": 2,
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_standard_user_can_create_and_list_own_orders(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/orders/",
            {"shipping_address": "My delivery address"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created_by"], self.user.username)

        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_users_cannot_see_other_users_orders(self):
        other_user = User.objects.create_user(
            username="anotheruser",
            password="AnotherPass123!",
        )
        FulfilmentOrder.objects.create(
            created_by=other_user,
            shipping_address="Private address",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_jwt_token_endpoint(self):
        response = self.client.post(
            "/api/token/",
            {
                "username": "adminuser",
                "password": "AdminPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_api_schema_endpoint(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)
