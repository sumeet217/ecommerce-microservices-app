"""Orders app URL configuration."""

from django.urls import path

from .views import CancelOrderView, OrderDetailView, OrderListView, PlaceOrderView

app_name = "orders"

urlpatterns = [
    path("place/", PlaceOrderView.as_view(), name="place"),
    path("", OrderListView.as_view(), name="list"),
    path("<int:order_id>/", OrderDetailView.as_view(), name="detail"),
    path("<int:order_id>/cancel/", CancelOrderView.as_view(), name="cancel"),
]
