from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from pathlib import Path
import time
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def parse_json(request):
    data = getattr(request, "json", None)
    if data is not None:
        return data
    import json
    try:
        return json.loads(request.body or b"{}")
    except Exception:
        return {}


def require_login(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return None, JsonResponse({"error": "未登录"}, status=401)
    return student_id, None


# 第一部分：Django框架基础
# 1. 路由示例 - 支持include包含路由
@require_GET
def index(request):
    return JsonResponse({"message": "学生管理系统 - 学生端"})


# 路由示例：articles/2020/05/python/
@require_GET
def article_detail(request, year, month, slug):
    return JsonResponse({
        "message": "文章详情",
        "year": year,
        "month": month,
        "slug": slug,
        "url": f"/articles/{year}/{month}/{slug}/"
    })


# 2. 基于函数的视图
@require_GET
def current_article(request):
    return JsonResponse({
        "message": "当前文章",
        "title": "Django框架基础",
        "content": "这是一个基于函数的视图示例"
    })


# 3. Django模板示例
@require_GET
def articles_list(request):
    articles = [
        {"id": 1, "title": "Django路由系统", "date": "2024-01-01"},
        {"id": 2, "title": "Django模板系统", "date": "2024-01-02"},
        {"id": 3, "title": "Django表单处理", "date": "2024-01-03"},
    ]
    return render(request, "student/articles.html", {"articles": articles})


# 4. 表单示例
@require_GET
def articles_login(request):
    """表单示例页面 - 展示Django表单功能"""
    return render(request, "student/articles_login.html")


@require_GET
def login_page(request):
    return render(request, "student/login.html")


# 第二部分：Django框架进阶
# 1. 使用会话实现登录
@csrf_exempt
@require_POST
def login(request):
    # 优先检查POST数据（表单提交，包括multipart/form-data和application/x-www-form-urlencoded）
    if request.POST:
        student_id = request.POST.get("student_id")
        password = request.POST.get("password")
        if not student_id or not password:
            # 如果是表单提交，返回重定向；否则返回JSON错误
            if request.content_type and ("form" in request.content_type.lower() or not request.content_type):
                return HttpResponseRedirect("/ui/login?error=缺少学号或密码")
            return JsonResponse({"error": "缺少学号或密码"}, status=400)
        
        with connection.cursor() as cur:
            cur.execute(
                "SELECT 学号, 姓名 FROM students WHERE 学号=%s AND 密码=%s AND 状态=1",
                [student_id, password],
            )
            row = cur.fetchone()
        if not row:
            # 如果是表单提交，返回重定向；否则返回JSON错误
            if request.content_type and ("form" in request.content_type.lower() or not request.content_type):
                return HttpResponseRedirect("/ui/login?error=学号或密码错误")
            return JsonResponse({"error": "学号或密码错误"}, status=401)
        
        request.session["student_id"] = row[0]
        request.session["student_name"] = row[1]
        
        # 如果是表单提交，返回重定向；否则返回JSON
        if request.content_type and ("form" in request.content_type.lower() or not request.content_type):
            return HttpResponseRedirect("/ui/profile")
        return JsonResponse({"ok": True, "student_id": row[0], "student_name": row[1]})
    
    # 支持JSON提交
    data = parse_json(request)
    student_id = data.get("student_id")
    password = data.get("password")
    if not student_id or not password:
        return JsonResponse({"error": "缺少学号或密码"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 学号, 姓名 FROM students WHERE 学号=%s AND 密码=%s AND 状态=1",
            [student_id, password],
        )
        row = cur.fetchone()
    if not row:
        return JsonResponse({"error": "学号或密码错误"}, status=401)
    request.session["student_id"] = row[0]
    request.session["student_name"] = row[1]
    return JsonResponse({"ok": True, "student_id": row[0], "student_name": row[1]})


@csrf_exempt
@require_POST
def logout(request):
    request.session.flush()
    return JsonResponse({"ok": True})


# 学生功能页面
@require_GET
def profile_page(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("/ui/login")
    student = None
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 学号, 姓名, 性别, 出生日期, 手机号, 邮箱, 班级ID, 入学日期 
               FROM students WHERE 学号=%s""",
            [student_id],
        )
        row = cur.fetchone()
        if row:
            cols = ["学号", "姓名", "性别", "出生日期", "手机号", "邮箱", "班级ID", "入学日期"]
            student = dict(zip(cols, row))
            # 获取班级信息
            if student["班级ID"]:
                cur.execute(
                    "SELECT 班级名称, 专业, 年级 FROM classes WHERE 班级ID=%s",
                    [student["班级ID"]],
                )
                class_row = cur.fetchone()
                if class_row:
                    student["班级名称"] = class_row[0]
                    student["专业"] = class_row[1]
                    student["年级"] = class_row[2]
    return render(request, "student/profile.html", {"student": student})


@require_GET
def courses_page(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("/ui/login")
    return render(request, "student/courses.html")


@require_GET
def grades_page(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("/ui/login")
    return render(request, "student/grades.html")


@require_GET
def attendance_page(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("/ui/login")
    return render(request, "student/attendance.html")


@csrf_exempt
@require_POST
def update_profile(request):
    student_id, err = require_login(request)
    if err:
        return err
    data = parse_json(request)
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    if not all([name, phone, email]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE students SET 姓名=%s, 手机号=%s, 邮箱=%s WHERE 学号=%s",
            [name, phone, email, student_id],
        )
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def enroll_course(request):
    student_id, err = require_login(request)
    if err:
        return err
    data = parse_json(request)
    course_id = data.get("course_id")
    if not course_id:
        return JsonResponse({"error": "缺少课程ID"}, status=400)
    import time
    enrollment_id = f"ENR{student_id}{int(time.time())}"
    try:
        with connection.cursor() as cur:
            cur.execute(
                """INSERT INTO enrollments(选课ID, 学号, 课程ID, 选课状态)
                   VALUES(%s, %s, %s, 1)""",
                [enrollment_id, student_id, course_id],
            )
        return JsonResponse({"ok": True, "enrollment_id": enrollment_id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_POST
def drop_course(request):
    student_id, err = require_login(request)
    if err:
        return err
    data = parse_json(request)
    course_id = data.get("course_id")
    if not course_id:
        return JsonResponse({"error": "缺少课程ID"}, status=400)
    
    with connection.cursor() as cur:
        # 检查选课时间是否超过7天
        cur.execute(
            """SELECT 选课时间, DATEDIFF(NOW(), 选课时间) as 天数 
               FROM enrollments 
               WHERE 学号=%s AND 课程ID=%s AND 选课状态=1""",
            [student_id, course_id],
        )
        row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "未找到该选课记录"}, status=400)
        
        days_diff = row[1]  # 选课至今的天数
        if days_diff > 7:
            return JsonResponse({
                "error": f"选课已超过7天（已{days_diff}天），无法退选。如需退选请联系教务处。"
            }, status=400)
        
        # 执行退选
        cur.execute(
            "UPDATE enrollments SET 选课状态=2 WHERE 学号=%s AND 课程ID=%s",
            [student_id, course_id],
        )
    return JsonResponse({"ok": True})


@require_GET
def my_courses(request):
    student_id, err = require_login(request)
    if err:
        return err
    with connection.cursor() as cur:
        cur.execute(
            """SELECT e.课程ID, c.课程名称, c.课程代码, c.学分, c.上课时间, c.上课地点,
                      t.姓名 AS 教师姓名, e.选课时间, e.选课状态,
                      DATEDIFF(NOW(), e.选课时间) as 选课天数,
                      CASE WHEN DATEDIFF(NOW(), e.选课时间) > 7 THEN 0 ELSE 1 END as 可退选
               FROM enrollments e
               JOIN courses c ON e.课程ID = c.课程ID
               LEFT JOIN teachers t ON c.授课教师工号 = t.工号
               WHERE e.学号=%s AND e.选课状态=1
               ORDER BY e.选课时间 DESC""",
            [student_id],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def my_grades(request):
    student_id, err = require_login(request)
    if err:
        return err
    with connection.cursor() as cur:
        cur.execute(
            """SELECT g.课程ID, c.课程名称, c.课程代码, c.学分,
                      g.平时成绩, g.期末成绩, g.总成绩, g.录入时间
               FROM grades g
               JOIN courses c ON g.课程ID = c.课程ID
               WHERE g.学号=%s
               ORDER BY g.录入时间 DESC""",
            [student_id],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def my_attendance(request):
    student_id, err = require_login(request)
    if err:
        return err
    course_id = request.GET.get("course_id")
    with connection.cursor() as cur:
        if course_id:
            cur.execute(
                """SELECT a.考勤ID, a.课程ID, c.课程名称, a.考勤日期, a.考勤状态, a.备注
                   FROM attendances a
                   JOIN courses c ON a.课程ID = c.课程ID
                   WHERE a.学号=%s AND a.课程ID=%s
                   ORDER BY a.考勤日期 DESC""",
                [student_id, course_id],
            )
        else:
            cur.execute(
                """SELECT a.考勤ID, a.课程ID, c.课程名称, a.考勤日期, a.考勤状态, a.备注
                   FROM attendances a
                   JOIN courses c ON a.课程ID = c.课程ID
                   WHERE a.学号=%s
                   ORDER BY a.考勤日期 DESC""",
                [student_id],
            )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def my_leave_requests(request):
    """获取我的请假申请列表"""
    student_id, err = require_login(request)
    if err:
        return err
    with connection.cursor() as cur:
        cur.execute(
            """SELECT l.请假申请ID, l.课程ID, c.课程名称, l.请假类型, l.开始日期, l.结束日期, 
                      l.请假理由, l.病假条图片, l.申请时间, l.审批状态, l.审批时间, l.审批意见
               FROM leave_requests l
               JOIN courses c ON l.课程ID = c.课程ID
               WHERE l.学号=%s
               ORDER BY l.申请时间 DESC""",
            [student_id],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def submit_leave_request(request):
    """提交请假申请"""
    student_id, err = require_login(request)
    if err:
        return err
    
    course_id = request.POST.get("course_id")
    leave_type = request.POST.get("leave_type")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")
    reason = request.POST.get("reason")
    medical_file = request.FILES.get("medical_certificate")
    
    if not all([course_id, leave_type, start_date, end_date, reason]):
        return JsonResponse({"error": "请填写完整信息"}, status=400)
    
    # 病假条图片改为可选，不再强制要求
    
    # 保存图片
    image_path = None
    if medical_file:
        import os
        import time
        from django.conf import settings
        # 使用MEDIA目录存储上传的文件
        upload_dir = settings.MEDIA_ROOT / "medical_certificates"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = os.path.splitext(medical_file.name)[1]
        filename = f"{student_id}_{int(time.time())}{file_ext}"
        file_path = upload_dir / filename
        
        with open(file_path, 'wb+') as destination:
            for chunk in medical_file.chunks():
                destination.write(chunk)
        
        # 使用MEDIA_URL访问文件
        image_path = f"{settings.MEDIA_URL}medical_certificates/{filename}"
    
    import time
    # 生成15位ID: LV(2) + 学号后8位(8) + 时间戳后5位(5) = 15位
    timestamp = str(int(time.time()))
    leave_id = f"LV{student_id[-8:]}{timestamp[-5:]}"
    
    try:
        with connection.cursor() as cur:
            cur.execute(
                """INSERT INTO leave_requests(请假申请ID, 学号, 课程ID, 请假类型, 开始日期, 结束日期, 请假理由, 病假条图片)
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s)""",
                [leave_id, student_id, course_id, leave_type, start_date, end_date, reason, image_path],
            )
        return JsonResponse({"ok": True, "leave_id": leave_id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

