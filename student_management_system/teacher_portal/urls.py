from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    # UI页面
    path("ui/login", views.ui_login),
    path("ui", views.ui_home),
    path("ui/courses", views.ui_courses),
    path("ui/students", views.ui_students),
    path("ui/grades", views.ui_grades),
    path("ui/attendance", views.ui_attendance),
    path("ui/leave-requests", views.ui_leave_requests),
    # Auth APIs
    path("api/login", views.api_login),
    path("api/logout", views.api_logout),
    # APIs
    path("courses/list", views.list_courses),
    path("courses/students", views.list_course_students),
    path("grades/add", views.add_grade),
    path("grades/update", views.update_grade),
    path("grades/import-excel", views.import_grades_excel),
    path("attendance/add", views.add_attendance),
    path("attendance/batch", views.batch_attendance),
    path("students/list", views.list_students),
    path("leave-requests/list", views.list_leave_requests),
    path("leave-requests/detail", views.get_leave_request_detail),
    path("leave-requests/update-status", views.update_leave_status),
]

