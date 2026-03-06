from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    # UI pages
    path("ui/login", views.ui_login),
    path("ui", views.ui_home),
    path("ui/users", views.ui_users),
    path("ui/staff", views.ui_staff),
    path("ui/flights", views.ui_flights),
    path("ui/logs", views.ui_logs),
    # Auth APIs
    path("api/login", views.api_login),
    path("api/logout", views.api_logout),
    # APIs
    path("flights", views.create_flight),
    path("flights/list", views.list_flights),
    path("flights/detail", views.get_flight_detail),
    path("flights/update", views.update_flight),
    path("flights/status", views.update_flight_status),
    path("flights/delete", views.delete_flight),
    path("flights/create-seats", views.create_seats_for_flight),
    path("routes/list", views.list_routes),
    path("stats/route-income", views.stats_route_income),
    path("stats/load-factor", views.stats_load_factor),
    path("users/list", views.list_users),
    path("users/save", views.save_user),
    path("users/delete", views.delete_user),
    path("staff/list", views.list_staff),
    path("staff/save", views.save_staff),
    path("logs/list", views.list_logs),
]
