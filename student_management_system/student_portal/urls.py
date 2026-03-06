from django.urls import path
from . import views

urlpatterns = [
    # 首页和路由示例
    path("", views.index),
    path("articles/", views.articles_list),
    path("articles/<int:year>/<int:month>/<str:slug>/", views.article_detail),
    path("articles/current", views.current_article),
    path("articles/login", views.articles_login),  # 表单示例页面
    
    # UI页面
    path("ui/login", views.login_page),
    path("ui/profile", views.profile_page),
    path("ui/courses", views.courses_page),
    path("ui/grades", views.grades_page),
    path("ui/attendance", views.attendance_page),
    
    # API接口
    path("api/login", views.login),
    path("api/logout", views.logout),
    path("api/update-profile", views.update_profile),
    path("api/enroll-course", views.enroll_course),
    path("api/drop-course", views.drop_course),
    path("api/my-courses", views.my_courses),
    path("api/my-grades", views.my_grades),
    path("api/my-attendance", views.my_attendance),
    path("api/leave-request", views.submit_leave_request),
    path("api/my-leave-requests", views.my_leave_requests),
]

