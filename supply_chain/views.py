
from django.db import connection
from django.db.utils import DatabaseError
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    Product,
    Warehouse,
    StockLevel,
    FulfilmentOrder,
)
from .serializers import (
    ProductSerializer,
    WarehouseSerializer,
    StockLevelSerializer,
    FulfilmentOrderSerializer,
)
from .permissions import IsAdminOrReadOnly, IsAdminOrOrderOwner


START_TIME = timezone.now()


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["is_active"]
    search_fields = ["sku", "name", "description"]
    ordering_fields = ["name", "unit_price", "created_at"]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["code", "name", "location"]
    ordering_fields = ["name", "code"]


class StockLevelViewSet(viewsets.ModelViewSet):
    queryset = StockLevel.objects.select_related(
        "product", "warehouse"
    )
    serializer_class = StockLevelSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["product", "warehouse"]
    ordering_fields = ["quantity", "updated_at"]


class FulfilmentOrderViewSet(viewsets.ModelViewSet):
    serializer_class = FulfilmentOrderSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOrderOwner]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "updated_at"]

    def get_queryset(self):
        queryset = FulfilmentOrder.objects.select_related(
            "created_by"
        ).prefetch_related("items__product")

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return Response({
            "status": "healthy",
            "database": "connected",
            "uptime_seconds": int(
                (timezone.now() - START_TIME).total_seconds()
            ),
        })
    except DatabaseError:
        return Response({
            "status": "unhealthy",
            "database": "disconnected",
        }, status=503)
