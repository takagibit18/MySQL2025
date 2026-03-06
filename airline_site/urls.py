from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health),
    path("", include("portal.urls")),
    path("staff/", include("staff_portal.urls")),
    path("sysadmin/", include("admin_portal.urls")),
]
