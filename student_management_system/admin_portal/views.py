from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from functools import wraps
from .forms import StudentForm, TeacherForm, CourseForm, ClassForm


def require_admin_login(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("admin_id"):
            return HttpResponseRedirect("/admin_portal/ui/login")
        return view_func(request, *args, **kwargs)
    return wrapper


def parse_json(request):
    data = getattr(request, "json", None)
    if data is not None:
        return data
    import json
    try:
        return json.loads(request.body or b"{}")
    except Exception:
        return {}


@require_GET
def index(request):
    if request.session.get("admin_id"):
        return HttpResponseRedirect("/admin_portal/ui")
    return HttpResponseRedirect("/admin_portal/ui/login")


@require_GET
def ui_login(request):
    if request.session.get("admin_id"):
        return HttpResponseRedirect("/admin_portal/ui")
    return render(request, "admin/login.html")


@csrf_exempt
@require_POST
def api_login(request):
    try:
        # 支持表单提交
        if request.content_type and request.content_type.startswith("application/x-www-form-urlencoded"):
            admin_id = request.POST.get("admin_id")
            password = request.POST.get("password")
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT 管理员ID, 姓名 FROM admins WHERE 管理员ID=%s AND 密码=%s AND 状态=1",
                    [admin_id, password],
                )
                row = cur.fetchone()
            if not row:
                return HttpResponseRedirect("/admin_portal/ui/login")
            request.session["admin_id"] = row[0]
            request.session["admin_name"] = row[1]
            return HttpResponseRedirect("/admin_portal/ui")
        
        # JSON提交
        data = parse_json(request)
        admin_id = data.get("admin_id")
        password = data.get("password")
        if not admin_id or not password:
            return JsonResponse({"error": "缺少管理员ID或密码"}, status=400)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT 管理员ID, 姓名 FROM admins WHERE 管理员ID=%s AND 密码=%s AND 状态=1",
                [admin_id, password],
            )
            row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "管理员ID或密码错误"}, status=401)
        request.session["admin_id"] = row[0]
        request.session["admin_name"] = row[1]
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": f"服务器错误: {str(e)}"}, status=500)


@csrf_exempt
@require_POST
def api_logout(request):
    request.session.flush()
    return JsonResponse({"ok": True})


@require_admin_login
@require_GET
def ui_home(request):
    return render(request, "admin/ui_home.html")


@require_admin_login
@require_GET
def ui_students(request):
    return render(request, "admin/students.html")


@require_admin_login
@require_GET
def ui_teachers(request):
    return render(request, "admin/teachers.html")


@require_admin_login
@require_GET
def ui_courses(request):
    return render(request, "admin/courses.html")


@require_admin_login
@require_GET
def ui_classes(request):
    return render(request, "admin/classes.html")


@require_admin_login
@require_GET
def ui_add(request):
    """ModelForm示例页面"""
    form = StudentForm()
    return render(request, "admin/add.html", {"form": form})


@require_admin_login
@require_GET
def ui_auth(request):
    """认证和授权页面"""
    return render(request, "admin/auth.html")


@require_admin_login
@require_GET
def list_students(request):
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 学号, 姓名, 性别, 出生日期, 手机号, 邮箱, 班级ID, 入学日期, 状态
               FROM students
               ORDER BY 学号""",
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_admin_login
@require_GET
def get_student_detail(request):
    student_id = request.GET.get("学号")
    if not student_id:
        return JsonResponse({"error": "缺少学号"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 学号, 姓名, 性别, 出生日期, 手机号, 邮箱, 班级ID, 入学日期, 密码, 状态
               FROM students WHERE 学号=%s""",
            [student_id],
        )
        row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "学生不存在"}, status=404)
        cols = ["学号", "姓名", "性别", "出生日期", "手机号", "邮箱", "班级ID", "入学日期", "密码", "状态"]
        item = dict(zip(cols, row))
    return JsonResponse({"item": item})


@require_admin_login
@csrf_exempt
@require_POST
def save_student(request):
    """使用ModelForm风格保存学生"""
    data = parse_json(request)
    form = StudentForm(data)
    if not form.is_valid():
        return JsonResponse({"error": "表单验证失败", "errors": form.errors}, status=400)
    
    student_id = data.get("学号")
    try:
        with connection.cursor() as cur:
            # 检查是否存在
            cur.execute("SELECT 学号 FROM students WHERE 学号=%s", [student_id])
            exists = cur.fetchone()
            if exists:
                # 更新
                cur.execute(
                    """UPDATE students SET 姓名=%s, 性别=%s, 出生日期=%s, 手机号=%s, 邮箱=%s, 
                       班级ID=%s, 入学日期=%s, 密码=%s, 状态=%s WHERE 学号=%s""",
                    [data.get("姓名"), data.get("性别"), data.get("出生日期"), data.get("手机号"),
                     data.get("邮箱"), data.get("班级ID") or None, data.get("入学日期"), 
                     data.get("密码"), int(data.get("状态", 1)), student_id],
                )
            else:
                # 插入
                cur.execute(
                    """INSERT INTO students(学号, 姓名, 性别, 出生日期, 手机号, 邮箱, 班级ID, 入学日期, 密码, 状态)
                       VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    [student_id, data.get("姓名"), data.get("性别"), data.get("出生日期"), 
                     data.get("手机号"), data.get("邮箱"), data.get("班级ID") or None, 
                     data.get("入学日期"), data.get("密码"), int(data.get("状态", 1))],
                )
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_admin_login
@csrf_exempt
@require_POST
def delete_student(request):
    data = parse_json(request)
    student_id = data.get("学号")
    if not student_id:
        return JsonResponse({"error": "缺少学号"}, status=400)
    try:
        with connection.cursor() as cur:
            cur.execute("DELETE FROM students WHERE 学号=%s", [student_id])
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_admin_login
@require_GET
def list_teachers(request):
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 工号, 姓名, 性别, 手机号, 邮箱, 职称, 部门, 状态
               FROM teachers
               ORDER BY 工号""",
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_admin_login
@require_GET
def get_teacher_detail(request):
    teacher_id = request.GET.get("工号")
    if not teacher_id:
        return JsonResponse({"error": "缺少工号"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 工号, 姓名, 性别, 手机号, 邮箱, 职称, 部门, 密码, 状态
               FROM teachers WHERE 工号=%s""",
            [teacher_id],
        )
        row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "教师不存在"}, status=404)
        cols = ["工号", "姓名", "性别", "手机号", "邮箱", "职称", "部门", "密码", "状态"]
        item = dict(zip(cols, row))
    return JsonResponse({"item": item})


@require_admin_login
@csrf_exempt
@require_POST
def save_teacher(request):
    data = parse_json(request)
    form = TeacherForm(data)
    if not form.is_valid():
        return JsonResponse({"error": "表单验证失败", "errors": form.errors}, status=400)
    
    teacher_id = data.get("工号")
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 工号 FROM teachers WHERE 工号=%s", [teacher_id])
            exists = cur.fetchone()
            if exists:
                cur.execute(
                    """UPDATE teachers SET 姓名=%s, 性别=%s, 手机号=%s, 邮箱=%s, 职称=%s, 部门=%s, 密码=%s, 状态=%s WHERE 工号=%s""",
                    [data.get("姓名"), data.get("性别"), data.get("手机号"), data.get("邮箱"),
                     data.get("职称"), data.get("部门"), data.get("密码"), int(data.get("状态", 1)), teacher_id],
                )
            else:
                cur.execute(
                    """INSERT INTO teachers(工号, 姓名, 性别, 手机号, 邮箱, 职称, 部门, 密码, 状态)
                       VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    [teacher_id, data.get("姓名"), data.get("性别"), data.get("手机号"), 
                     data.get("邮箱"), data.get("职称"), data.get("部门"), data.get("密码"), int(data.get("状态", 1))],
                )
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_admin_login
@csrf_exempt
@require_POST
def delete_teacher(request):
    data = parse_json(request)
    teacher_id = data.get("工号")
    if not teacher_id:
        return JsonResponse({"error": "缺少工号"}, status=400)
    try:
        with connection.cursor() as cur:
            cur.execute("DELETE FROM teachers WHERE 工号=%s", [teacher_id])
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_admin_login
@require_GET
def list_courses(request):
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 课程ID, 课程名称, 课程代码, 学分, 授课教师工号, 上课时间, 上课地点, 课程状态
               FROM courses
               ORDER BY 课程代码""",
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_admin_login
@require_GET
def get_course_detail(request):
    course_id = request.GET.get("课程ID")
    if not course_id:
        return JsonResponse({"error": "缺少课程ID"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 课程ID, 课程名称, 课程代码, 学分, 授课教师工号, 上课时间, 上课地点, 课程状态
               FROM courses WHERE 课程ID=%s""",
            [course_id],
        )
        row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "课程不存在"}, status=404)
        cols = ["课程ID", "课程名称", "课程代码", "学分", "授课教师工号", "上课时间", "上课地点", "课程状态"]
        item = dict(zip(cols, row))
    return JsonResponse({"item": item})


@require_admin_login
@csrf_exempt
@require_POST
def save_course(request):
    data = parse_json(request)
    form = CourseForm(data)
    if not form.is_valid():
        return JsonResponse({"error": "表单验证失败", "errors": form.errors}, status=400)
    
    course_id = data.get("课程ID")
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 课程ID FROM courses WHERE 课程ID=%s", [course_id])
            exists = cur.fetchone()
            if exists:
                cur.execute(
                    """UPDATE courses SET 课程名称=%s, 课程代码=%s, 学分=%s, 授课教师工号=%s, 
                       上课时间=%s, 上课地点=%s, 课程状态=%s WHERE 课程ID=%s""",
                    [data.get("课程名称"), data.get("课程代码"), float(data.get("学分", 0)),
                     data.get("授课教师工号") or None, data.get("上课时间"), data.get("上课地点"),
                     int(data.get("课程状态", 1)), course_id],
                )
            else:
                cur.execute(
                    """INSERT INTO courses(课程ID, 课程名称, 课程代码, 学分, 授课教师工号, 上课时间, 上课地点, 课程状态)
                       VALUES(%s, %s, %s, %s, %s, %s, %s, %s)""",
                    [course_id, data.get("课程名称"), data.get("课程代码"), float(data.get("学分", 0)),
                     data.get("授课教师工号") or None, data.get("上课时间"), data.get("上课地点"), int(data.get("课程状态", 1))],
                )
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_admin_login
@csrf_exempt
@require_POST
def delete_course(request):
    data = parse_json(request)
    course_id = data.get("课程ID")
    if not course_id:
        return JsonResponse({"error": "缺少课程ID"}, status=400)
    try:
        with connection.cursor() as cur:
            cur.execute("DELETE FROM courses WHERE 课程ID=%s", [course_id])
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_admin_login
@require_GET
def list_classes(request):
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 班级ID, 班级名称, 专业, 年级, 班主任工号, 创建时间
               FROM classes
               ORDER BY 创建时间 DESC""",
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_admin_login
@require_GET
def get_class_detail(request):
    class_id = request.GET.get("班级ID")
    if not class_id:
        return JsonResponse({"error": "缺少班级ID"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """SELECT 班级ID, 班级名称, 专业, 年级, 班主任工号, 创建时间
               FROM classes WHERE 班级ID=%s""",
            [class_id],
        )
        row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "班级不存在"}, status=404)
        cols = ["班级ID", "班级名称", "专业", "年级", "班主任工号", "创建时间"]
        item = dict(zip(cols, row))
    return JsonResponse({"item": item})


@require_admin_login
@csrf_exempt
@require_POST
def save_class(request):
    data = parse_json(request)
    form = ClassForm(data)
    if not form.is_valid():
        return JsonResponse({"error": "表单验证失败", "errors": form.errors}, status=400)
    
    class_id = data.get("班级ID")
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 班级ID FROM classes WHERE 班级ID=%s", [class_id])
            exists = cur.fetchone()
            if exists:
                cur.execute(
                    """UPDATE classes SET 班级名称=%s, 专业=%s, 年级=%s, 班主任工号=%s WHERE 班级ID=%s""",
                    [data.get("班级名称"), data.get("专业"), data.get("年级"), 
                     data.get("班主任工号") or None, class_id],
                )
            else:
                cur.execute(
                    """INSERT INTO classes(班级ID, 班级名称, 专业, 年级, 班主任工号)
                       VALUES(%s, %s, %s, %s, %s)""",
                    [class_id, data.get("班级名称"), data.get("专业"), data.get("年级"), 
                     data.get("班主任工号") or None],
                )
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_admin_login
@csrf_exempt
@require_POST
def delete_class(request):
    data = parse_json(request)
    class_id = data.get("班级ID")
    if not class_id:
        return JsonResponse({"error": "缺少班级ID"}, status=400)
    try:
        with connection.cursor() as cur:
            cur.execute("DELETE FROM classes WHERE 班级ID=%s", [class_id])
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# 认证和授权相关视图
@require_admin_login
@require_GET
def list_auth_users(request):
    """列出所有用户（学生、教师、管理员）"""
    users = []
    with connection.cursor() as cur:
        # 学生
        cur.execute("SELECT 学号 as id, 姓名 as name, 'student' as type FROM students WHERE 状态=1")
        for row in cur.fetchall():
            users.append({"id": row[0], "name": row[1], "type": row[2]})
        # 教师
        cur.execute("SELECT 工号 as id, 姓名 as name, 'teacher' as type FROM teachers WHERE 状态=1")
        for row in cur.fetchall():
            users.append({"id": row[0], "name": row[1], "type": row[2]})
        # 管理员
        cur.execute("SELECT 管理员ID as id, 姓名 as name, 'admin' as type FROM admins WHERE 状态=1")
        for row in cur.fetchall():
            users.append({"id": row[0], "name": row[1], "type": row[2]})
    return JsonResponse({"items": users})


@require_admin_login
@require_GET
def list_auth_groups(request):
    """列出权限组"""
    groups = [
        {"id": "student", "name": "学生组", "description": "学生权限组"},
        {"id": "teacher", "name": "教师组", "description": "教师权限组"},
        {"id": "admin", "name": "管理员组", "description": "管理员权限组"},
    ]
    return JsonResponse({"items": groups})


@require_admin_login
@require_GET
def get_user_permissions(request):
    """获取用户权限"""
    user_id = request.GET.get("user_id")
    user_type = request.GET.get("user_type")
    if not user_id or not user_type:
        return JsonResponse({"error": "缺少参数"}, status=400)
    
    # 这里简化处理，实际应该从权限表读取
    permissions = {
        "student": ["view_profile", "view_courses", "view_grades", "enroll_course"],
        "teacher": ["view_courses", "manage_grades", "manage_attendance"],
        "admin": ["manage_students", "manage_teachers", "manage_courses", "manage_classes", "manage_auth"],
    }
    
    return JsonResponse({
        "user_id": user_id,
        "user_type": user_type,
        "permissions": permissions.get(user_type, [])
    })


@require_admin_login
@csrf_exempt
@require_POST
def save_user_permissions(request):
    """保存用户权限"""
    data = parse_json(request)
    user_id = data.get("user_id")
    user_type = data.get("user_type")
    permissions = data.get("permissions", [])
    
    # 这里简化处理，实际应该保存到权限表
    return JsonResponse({"ok": True, "message": "权限已保存"})


@require_admin_login
@require_GET
def get_group_permissions(request):
    """获取权限组权限"""
    group_id = request.GET.get("group_id")
    if not group_id:
        return JsonResponse({"error": "缺少权限组ID"}, status=400)
    
    permissions = {
        "student": ["view_profile", "view_courses", "view_grades", "enroll_course"],
        "teacher": ["view_courses", "manage_grades", "manage_attendance"],
        "admin": ["manage_students", "manage_teachers", "manage_courses", "manage_classes", "manage_auth"],
    }
    
    return JsonResponse({
        "group_id": group_id,
        "permissions": permissions.get(group_id, [])
    })


@require_admin_login
@csrf_exempt
@require_POST
def save_group_permissions(request):
    """保存权限组权限"""
    data = parse_json(request)
    group_id = data.get("group_id")
    permissions = data.get("permissions", [])
    
    # 这里简化处理，实际应该保存到权限表
    return JsonResponse({"ok": True, "message": "权限组权限已保存"})
