"""UI Service — Root URL Configuration"""

from django.urls import path

from apps.store import views

urlpatterns = [
    path("",                          views.HomeView.as_view(),             name="home"),
    path("products/",                 views.ProductListView.as_view(),      name="product-list"),
    path("products/<int:product_id>/",views.ProductDetailView.as_view(),    name="product-detail"),
    path("cart/",                     views.CartView.as_view(),             name="cart"),
    path("cart/add/",                 views.CartAddView.as_view(),          name="cart-add"),
    path("cart/update/",              views.CartUpdateView.as_view(),       name="cart-update"),
    path("cart/remove/",              views.CartRemoveView.as_view(),       name="cart-remove"),
    path("cart/clear/",               views.CartClearView.as_view(),        name="cart-clear"),
    path("checkout/",                 views.CheckoutView.as_view(),         name="checkout"),
    path("orders/",                   views.OrderListView.as_view(),        name="order-list"),
    path("orders/<int:order_id>/",    views.OrderDetailView.as_view(),      name="order-detail"),
    path("orders/<int:order_id>/cancel/", views.OrderCancelView.as_view(), name="order-cancel"),
    path("orders/<int:order_id>/confirm/", views.OrderConfirmView.as_view(),name="order-confirm"),
]
