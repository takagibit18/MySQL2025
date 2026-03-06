from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("ui/login", views.login_page),
    path("ui/register", views.register_page),
    path("ui/search", views.search_page),
    path("ui/orders", views.orders_page),
    path("ui/order-detail", views.order_detail_page),
    path("ui/profile", views.profile_page),
    path("ui/passengers", views.passengers_page),

    path("api/register", views.register),
    path("api/login", views.login),
    path("api/logout", views.logout),
    path("api/update-profile", views.update_profile),
    path("api/passengers/create", views.passengers_create),
    path("api/passengers/delete", views.passengers_delete),
    path("api/search-flights", views.search_flights),
    path("api/list-seats", views.list_seats),
    path("api/create-order", views.create_order),
    path("api/passengers/list", views.passengers_list),
    path("api/passengers/update", views.passengers_update),
    path("api/order-detail", views.order_detail),
    path("api/order-history", views.order_history),
    path("api/cancel-order", views.cancel_order),
    path("api/pay-order", views.pay_order),
    path("api/create-change-request", views.create_change_request),
    path("api/confirm-change", views.confirm_change),
    path("api/user-refund", views.user_refund),
]
