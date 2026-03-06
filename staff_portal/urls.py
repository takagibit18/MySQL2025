from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    # UI pages
    path("ui/login", views.ui_login),
    path("ui", views.ui_home),
    path("ui/orders", views.ui_orders),
    path("ui/flights", views.ui_flights),
    path("ui/stats", views.ui_stats),
    # Auth APIs
    path("api/login", views.api_login),
    path("api/logout", views.api_logout),
    # APIs
    path("user", views.get_user_by_idcard),
    path("assist-change", views.assist_change_ticket),
    path("refund", views.create_refund),
    path("orders/list", views.list_all_orders),
    path("orders/detail", views.get_order_detail),
    path("flights/list", views.list_flights),
    path("flights/available", views.list_available_flights),
    path("seats/update", views.update_seat_status),
    path("stats/route-income", views.stats_route_income),
    path("stats/load-factor", views.stats_load_factor),
]
