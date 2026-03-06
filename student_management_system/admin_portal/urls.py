from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    # UI页面
    path("ui/login", views.ui_login),
    path("ui", views.ui_home),
    path("ui/students", views.ui_students),
    path("ui/teachers", views.ui_teachers),
    path("ui/courses", views.ui_courses),
    path("ui/classes", views.ui_classes),
    path("ui/add", views.ui_add),  # ModelForm示例页面
    # Auth APIs
    path("api/login", views.api_login),
    path("api/logout", views.api_logout),
    # APIs
    path("students/list", views.list_students),
    path("students/detail", views.get_student_detail),
    path("students/save", views.save_student),
    path("students/delete", views.delete_student),
    path("teachers/list", views.list_teachers),
    path("teachers/detail", views.get_teacher_detail),
    path("teachers/save", views.save_teacher),
    path("teachers/delete", views.delete_teacher),
    path("courses/list", views.list_courses),
    path("courses/detail", views.get_course_detail),
    path("courses/save", views.save_course),
    path("courses/delete", views.delete_course),
    path("classes/list", views.list_classes),
    path("classes/detail", views.get_class_detail),
    path("classes/save", views.save_class),
    path("classes/delete", views.delete_class),
    # 认证和授权
    path("ui/auth", views.ui_auth),
    path("auth/users/list", views.list_auth_users),
    path("auth/groups/list", views.list_auth_groups),
    path("auth/user/permissions", views.get_user_permissions),
    path("auth/user/permissions/save", views.save_user_permissions),
    path("auth/group/permissions", views.get_group_permissions),
    path("auth/group/permissions/save", views.save_group_permissions),
]

