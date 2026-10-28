
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProductViewSet,
    WarehouseViewSet,
    StockLevelViewSet,
    FulfilmentOrderViewSet,
    health_check,
)

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("warehouses", WarehouseViewSet, basename="warehouse")
router.register("stock-levels", StockLevelViewSet, basename="stock-level")
router.register("orders", FulfilmentOrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("health/", health_check, name="health-check"),
]
