from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from functools import wraps
import time


def require_teacher_login(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("teacher_id"):
            return HttpResponseRedirect("/teacher/ui/login")
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
    if request.session.get("teacher_id"):
        return HttpResponseRedirect("/teacher/ui")
    return HttpResponseRedirect("/teacher/ui/login")


@require_GET
def ui_login(request):
    if request.session.get("teacher_id"):
        return HttpResponseRedirect("/teacher/ui")
    return render(request, "teacher/login.html")


@csrf_exempt
@require_POST
def api_login(request):
    try:
        # 支持表单提交
        if request.content_type and request.content_type.startswith("application/x-www-form-urlencoded"):
            teacher_id = request.POST.get("teacher_id")
            password = request.POST.get("password")
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT 工号, 姓名 FROM teachers WHERE 工号=%s AND 密码=%s AND 状态=1",
                    [teacher_id, password],
                )
                row = cur.fetchone()
            if not row:
                return HttpResponseRedirect("/teacher/ui/login")
            request.session["teacher_id"] = row[0]
            request.session["teacher_name"] = row[1]
            return HttpResponseRedirect("/teacher/ui")
        
        # JSON提交
        data = parse_json(request)
        teacher_id = data.get("teacher_id")
        password = data.get("password")
        if not teacher_id or not password:
            return JsonResponse({"error": "缺少工号或密码"}, status=400)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT 工号, 姓名 FROM teachers WHERE 工号=%s AND 密码=%s AND 状态=1",
                [teacher_id, password],
            )
            row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "工号或密码错误"}, status=401)
        request.session["teacher_id"] = row[0]
        request.session["teacher_name"] = row[1]
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": f"服务器错误: {str(e)}"}, status=500)


@csrf_exempt
@require_POST
def api_logout(request):
    request.session.flush()
    return JsonResponse({"ok": True})


@require_teacher_login
@require_GET
def ui_home(request):
    return render(request, "teacher/ui_home.html")


@require_teacher_login
@require_GET
def ui_courses(request):
    return render(request, "teacher/courses.html")


@require_teacher_login
@require_GET
def ui_students(request):
    return render(request, "teacher/students.html")


@require_teacher_login
@require_GET
def ui_grades(request):
    return render(request, "teacher/grades.html")


@require_teacher_login
@require_GET
def ui_attendance(request):
    return render(request, "teacher/attendance.html")


@require_teacher_login
@require_GET
def list_courses(request):
    teacher_id = request.session.get("teacher_id")
    with connection.cursor() as cur:
        cur.execute(
            """SELECT c.课程ID, c.课程名称, c.课程代码, c.学分, c.上课时间, c.上课地点, c.课程状态,
                      COUNT(e.选课ID) as 选课人数
               FROM courses c
               LEFT JOIN enrollments e ON c.课程ID = e.课程ID AND e.选课状态=1
               WHERE c.授课教师工号=%s AND c.课程状态=1
               GROUP BY c.课程ID
               ORDER BY c.课程代码""",
            [teacher_id],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_teacher_login
@require_GET
def list_course_students(request):
    course_id = request.GET.get("course_id")
    if not course_id:
        return JsonResponse({"error": "缺少课程ID"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """SELECT s.学号, s.姓名, s.性别, s.手机号, e.选课时间,
                      g.平时成绩, g.期末成绩, g.总成绩
               FROM enrollments e
               JOIN students s ON e.学号 = s.学号
               LEFT JOIN grades g ON s.学号 = g.学号 AND g.课程ID = e.课程ID
               WHERE e.课程ID=%s AND e.选课状态=1
               ORDER BY s.学号""",
            [course_id],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_teacher_login
@require_GET
def list_students(request):
    course_id = request.GET.get("course_id")
    with connection.cursor() as cur:
        if course_id:
            cur.execute(
                """SELECT s.学号, s.姓名, s.性别, s.手机号, s.邮箱
                   FROM enrollments e
                   JOIN students s ON e.学号 = s.学号
                   WHERE e.课程ID=%s AND e.选课状态=1
                   ORDER BY s.学号""",
                [course_id],
            )
        else:
            cur.execute(
                """SELECT 学号, 姓名, 性别, 手机号, 邮箱
                   FROM students WHERE 状态=1
                   ORDER BY 学号""",
            )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_teacher_login
@csrf_exempt
@require_POST
def add_grade(request):
    teacher_id = request.session.get("teacher_id")
    data = parse_json(request)
    student_id = data.get("学号")
    course_id = data.get("课程ID")
    daily_score = data.get("平时成绩")
    final_score = data.get("期末成绩")
    total_score = data.get("总成绩")
    
    if not all([student_id, course_id]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    
    # 计算总成绩
    if total_score is None or total_score == '':
        if daily_score is not None and daily_score != '' and final_score is not None and final_score != '':
            try:
                total_score = float(daily_score) * 0.3 + float(final_score) * 0.7
            except (ValueError, TypeError):
                return JsonResponse({"error": "成绩格式错误"}, status=400)
        elif daily_score is not None and daily_score != '':
            # 只有平时成绩，总成绩设为平时成绩
            try:
                total_score = float(daily_score)
            except (ValueError, TypeError):
                return JsonResponse({"error": "成绩格式错误"}, status=400)
        elif final_score is not None and final_score != '':
            # 只有期末成绩，总成绩设为期末成绩
            try:
                total_score = float(final_score)
            except (ValueError, TypeError):
                return JsonResponse({"error": "成绩格式错误"}, status=400)
        else:
            return JsonResponse({"error": "请至少输入一项成绩"}, status=400)
    else:
        try:
            total_score = float(total_score)
        except (ValueError, TypeError):
            return JsonResponse({"error": "总成绩格式错误"}, status=400)
    
    # 转换成绩为浮点数或None
    try:
        daily_score = float(daily_score) if daily_score is not None and daily_score != '' else None
    except (ValueError, TypeError):
        daily_score = None
    
    try:
        final_score = float(final_score) if final_score is not None and final_score != '' else None
    except (ValueError, TypeError):
        final_score = None
    
    import time
    try:
        with connection.cursor() as cur:
            # 先检查是否已存在该学生的成绩记录
            cur.execute(
                "SELECT 成绩ID FROM grades WHERE 学号=%s AND 课程ID=%s",
                [student_id, course_id]
            )
            existing = cur.fetchone()
            
            if existing:
                # 更新现有记录
                grade_id = existing[0]
                cur.execute(
                    """UPDATE grades SET 平时成绩=%s, 期末成绩=%s, 总成绩=%s, 录入教师工号=%s
                       WHERE 学号=%s AND 课程ID=%s""",
                    [daily_score, final_score, total_score, teacher_id, student_id, course_id],
                )
            else:
                # 插入新记录
                grade_id = f"GRD{student_id[-6:]}{int(time.time())}"
                cur.execute(
                    """INSERT INTO grades(成绩ID, 学号, 课程ID, 平时成绩, 期末成绩, 总成绩, 录入教师工号)
                       VALUES(%s, %s, %s, %s, %s, %s, %s)""",
                    [grade_id, student_id, course_id, daily_score, final_score, total_score, teacher_id],
                )
        return JsonResponse({"ok": True, "grade_id": grade_id})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=400)


@require_teacher_login
@csrf_exempt
@require_POST
def update_grade(request):
    return add_grade(request)  # 使用相同的逻辑


@require_teacher_login
@csrf_exempt
@require_POST
def add_attendance(request):
    teacher_id = request.session.get("teacher_id")
    data = parse_json(request)
    student_id = data.get("学号")
    course_id = data.get("课程ID")
    attendance_date = data.get("考勤日期")
    attendance_status = data.get("考勤状态")  # 1-出勤，2-迟到，3-早退，4-缺勤
    remark = data.get("备注", "")
    
    if not all([student_id, course_id, attendance_date, attendance_status]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    
    import time
    # 生成15位ID: ATT(3) + 学号后6位(6) + 时间戳后6位(6) = 15位
    timestamp = str(int(time.time()))
    attendance_id = f"ATT{student_id[-6:]}{timestamp[-6:]}"
    try:
        with connection.cursor() as cur:
            cur.execute(
                """INSERT INTO attendances(考勤ID, 学号, 课程ID, 考勤日期, 考勤状态, 备注, 记录教师工号)
                   VALUES(%s, %s, %s, %s, %s, %s, %s)""",
                [attendance_id, student_id, course_id, attendance_date, attendance_status, remark, teacher_id],
            )
        return JsonResponse({"ok": True, "attendance_id": attendance_id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@require_teacher_login
@csrf_exempt
@require_POST
def batch_attendance(request):
    """批量保存考勤记录"""
    teacher_id = request.session.get("teacher_id")
    data = parse_json(request)
    attendances = data.get("attendances", [])
    
    if not attendances:
        return JsonResponse({"error": "没有考勤数据"}, status=400)
    
    success_count = 0
    error_messages = []
    
    with connection.cursor() as cur:
        for att in attendances:
            student_id = att.get("学号")
            course_id = att.get("课程ID")
            attendance_date = att.get("考勤日期")
            attendance_status = att.get("考勤状态")
            remark = att.get("备注", "")
            
            if not all([student_id, course_id, attendance_date, attendance_status]):
                error_messages.append(f"学号 {student_id} 数据不完整")
                continue
            
            attendance_id = f"ATT{student_id}{int(time.time())}"
            try:
                cur.execute(
                    """INSERT INTO attendances(考勤ID, 学号, 课程ID, 考勤日期, 考勤状态, 备注, 记录教师工号)
                       VALUES(%s, %s, %s, %s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE 考勤状态=VALUES(考勤状态), 备注=VALUES(备注), 记录教师工号=VALUES(记录教师工号)""",
                    [attendance_id, student_id, course_id, attendance_date, attendance_status, remark, teacher_id],
                )
                success_count += 1
            except Exception as e:
                error_messages.append(f"学号 {student_id} 保存失败：{str(e)}")
    
    result = {"ok": True, "count": success_count, "total": len(attendances)}
    if error_messages:
        result["errors"] = error_messages[:10]
    
    return JsonResponse(result)


@require_teacher_login
@csrf_exempt
@require_POST
def import_grades_excel(request):
    """Excel批量导入成绩"""
    teacher_id = request.session.get("teacher_id")
    course_id = request.POST.get("course_id")
    
    if not course_id:
        return JsonResponse({"error": "缺少课程ID"}, status=400)
    
    if 'excel_file' not in request.FILES:
        return JsonResponse({"error": "请选择Excel文件"}, status=400)
    
    excel_file = request.FILES['excel_file']
    
    # 检查文件扩展名
    if not excel_file.name.endswith(('.xlsx', '.xls')):
        return JsonResponse({"error": "请上传Excel文件（.xlsx或.xls格式）"}, status=400)
    
    try:
        # 尝试使用openpyxl读取Excel
        try:
            import openpyxl
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            # 读取数据（跳过第一行标题）
            rows = []
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not row[0]:  # 如果学号为空，跳过
                    continue
                try:
                    rows.append({
                        '学号': str(row[0]).strip(),
                        '平时成绩': float(row[1]) if row[1] is not None and row[1] != '' else None,
                        '期末成绩': float(row[2]) if row[2] is not None and row[2] != '' else None,
                        '总成绩': float(row[3]) if len(row) > 3 and row[3] is not None and row[3] != '' else None,
                    })
                except (ValueError, IndexError) as e:
                    # 跳过格式错误的行
                    continue
        except ImportError:
            # 如果没有openpyxl，尝试使用pandas
            try:
                import pandas as pd
                df = pd.read_excel(excel_file)
                rows = []
                for _, row in df.iterrows():
                    if pd.isna(row.iloc[0]):  # 学号为空
                        continue
                    try:
                        rows.append({
                            '学号': str(row.iloc[0]).strip(),
                            '平时成绩': float(row.iloc[1]) if len(row) > 1 and not pd.isna(row.iloc[1]) else None,
                            '期末成绩': float(row.iloc[2]) if len(row) > 2 and not pd.isna(row.iloc[2]) else None,
                            '总成绩': float(row.iloc[3]) if len(row) > 3 and not pd.isna(row.iloc[3]) else None,
                        })
                    except (ValueError, IndexError) as e:
                        # 跳过格式错误的行
                        continue
            except ImportError:
                return JsonResponse({"error": "请安装openpyxl或pandas库：pip install openpyxl pandas"}, status=400)
        
        if not rows:
            return JsonResponse({"error": "Excel文件中没有有效数据"}, status=400)
        
        # 批量插入成绩
        success_count = 0
        error_messages = []
        
        with connection.cursor() as cur:
            for row_data in rows:
                student_id = row_data['学号']
                daily_score = row_data['平时成绩']
                final_score = row_data['期末成绩']
                total_score = row_data['总成绩']
                
                # 验证学号是否存在
                cur.execute("SELECT 学号 FROM students WHERE 学号=%s", [student_id])
                if not cur.fetchone():
                    error_messages.append(f"学号 {student_id} 不存在")
                    continue
                
                # 验证是否选课
                cur.execute(
                    "SELECT 学号 FROM enrollments WHERE 学号=%s AND 课程ID=%s AND 选课状态=1",
                    [student_id, course_id]
                )
                if not cur.fetchone():
                    error_messages.append(f"学号 {student_id} 未选此课程")
                    continue
                
                # 计算总成绩（如果没有提供）
                if total_score is None:
                    if daily_score is not None and final_score is not None:
                        total_score = daily_score * 0.3 + final_score * 0.7
                    elif daily_score is not None:
                        # 只有平时成绩，总成绩等于平时成绩
                        total_score = daily_score
                    elif final_score is not None:
                        # 只有期末成绩，总成绩等于期末成绩
                        total_score = final_score
                    else:
                        error_messages.append(f"学号 {student_id} 缺少成绩数据")
                        continue
                
                # 检查是否已存在该学生的成绩记录
                cur.execute(
                    "SELECT 成绩ID FROM grades WHERE 学号=%s AND 课程ID=%s",
                    [student_id, course_id]
                )
                existing = cur.fetchone()
                
                try:
                    if existing:
                        # 更新现有记录（覆盖已有数据）
                        grade_id = existing[0]
                        cur.execute(
                            """UPDATE grades SET 平时成绩=%s, 期末成绩=%s, 总成绩=%s, 录入教师工号=%s
                               WHERE 学号=%s AND 课程ID=%s""",
                            [daily_score, final_score, total_score, teacher_id, student_id, course_id],
                        )
                        success_count += 1
                    else:
                        # 插入新记录
                        grade_id = f"GRD{student_id[-6:]}{int(time.time())}"
                        cur.execute(
                            """INSERT INTO grades(成绩ID, 学号, 课程ID, 平时成绩, 期末成绩, 总成绩, 录入教师工号)
                               VALUES(%s, %s, %s, %s, %s, %s, %s)""",
                            [grade_id, student_id, course_id, daily_score, final_score, total_score, teacher_id],
                        )
                        success_count += 1
                except Exception as e:
                    error_messages.append(f"学号 {student_id} 保存失败：{str(e)}")
        
        result = {
            "ok": True,
            "count": success_count,
            "total": len(rows)
        }
        if error_messages:
            result["errors"] = error_messages[:10]  # 最多返回10条错误信息
        if success_count == 0 and len(rows) > 0:
            result["warning"] = f"共读取{len(rows)}条数据，但成功导入0条。请检查错误信息。"
        elif success_count > 0:
            result["message"] = f"成功导入{success_count}条成绩记录（已覆盖已有数据）"
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({"error": f"导入失败：{str(e)}"}, status=400)


@require_teacher_login
@require_GET
def ui_leave_requests(request):
    """请假申请查看页面"""
    return render(request, "teacher/leave_requests.html")


@require_teacher_login
@require_GET
def list_leave_requests(request):
    """列出请假申请（教师查看自己课程的请假申请）"""
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        return JsonResponse({"error": "未登录或会话已过期"}, status=401)
    
    course_id = request.GET.get("course_id", "")
    status = request.GET.get("status", "")  # 0-待审批，1-已通过，2-已拒绝
    
    try:
        with connection.cursor() as cur:
            # 首先检查表是否存在（如果表不存在，会抛出异常）
            # 如果没有请假申请，返回空数组而不是错误
            if course_id:
                # 查看指定课程的请假申请
                if status:
                    cur.execute(
                        """SELECT l.请假申请ID, l.学号, s.姓名 as 学生姓名, l.课程ID, c.课程名称, 
                                  l.请假类型, l.开始日期, l.结束日期, l.请假理由, l.病假条图片,
                                  l.申请时间, l.审批状态, l.审批时间, l.审批意见
                           FROM leave_requests l
                           JOIN students s ON l.学号 = s.学号
                           JOIN courses c ON l.课程ID = c.课程ID
                           WHERE l.课程ID=%s AND l.审批状态=%s
                           ORDER BY l.申请时间 DESC""",
                        [course_id, int(status)],
                    )
                else:
                    cur.execute(
                        """SELECT l.请假申请ID, l.学号, s.姓名 as 学生姓名, l.课程ID, c.课程名称, 
                                  l.请假类型, l.开始日期, l.结束日期, l.请假理由, l.病假条图片,
                                  l.申请时间, l.审批状态, l.审批时间, l.审批意见
                           FROM leave_requests l
                           JOIN students s ON l.学号 = s.学号
                           JOIN courses c ON l.课程ID = c.课程ID
                           WHERE l.课程ID=%s
                           ORDER BY l.申请时间 DESC""",
                        [course_id],
                    )
            else:
                # 查看教师所有课程的请假申请
                if status:
                    cur.execute(
                        """SELECT l.请假申请ID, l.学号, s.姓名 as 学生姓名, l.课程ID, c.课程名称, 
                                  l.请假类型, l.开始日期, l.结束日期, l.请假理由, l.病假条图片,
                                  l.申请时间, l.审批状态, l.审批时间, l.审批意见
                           FROM leave_requests l
                           JOIN students s ON l.学号 = s.学号
                           JOIN courses c ON l.课程ID = c.课程ID
                           WHERE c.授课教师工号=%s AND l.审批状态=%s
                           ORDER BY l.申请时间 DESC""",
                        [teacher_id, int(status)],
                    )
                else:
                    cur.execute(
                        """SELECT l.请假申请ID, l.学号, s.姓名 as 学生姓名, l.课程ID, c.课程名称, 
                                  l.请假类型, l.开始日期, l.结束日期, l.请假理由, l.病假条图片,
                                  l.申请时间, l.审批状态, l.审批时间, l.审批意见
                           FROM leave_requests l
                           JOIN students s ON l.学号 = s.学号
                           JOIN courses c ON l.课程ID = c.课程ID
                           WHERE c.授课教师工号=%s
                           ORDER BY l.申请时间 DESC""",
                        [teacher_id],
                    )
            cols = [c[0] for c in cur.description] if cur.description else []
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return JsonResponse({"items": rows})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"查询失败: {str(e)}", "items": []}, status=500)


@require_teacher_login
@require_GET
def get_leave_request_detail(request):
    """获取请假申请详情"""
    leave_id = request.GET.get("请假申请ID")
    if not leave_id:
        return JsonResponse({"error": "缺少请假申请ID"}, status=400)
    try:
        with connection.cursor() as cur:
            cur.execute(
                """SELECT l.*, s.姓名 as 学生姓名, c.课程名称
                   FROM leave_requests l
                   JOIN students s ON l.学号 = s.学号
                   JOIN courses c ON l.课程ID = c.课程ID
                   WHERE l.请假申请ID=%s""",
                [leave_id],
            )
            row = cur.fetchone()
            if not row:
                return JsonResponse({"error": "请假申请不存在"}, status=404)
            cols = [c[0] for c in cur.description]
            item = dict(zip(cols, row))
        return JsonResponse({"item": item})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"查询失败: {str(e)}"}, status=500)


@require_teacher_login
@csrf_exempt
@require_POST
def update_leave_status(request):
    """更新请假申请状态（教师审批）"""
    teacher_id = request.session.get("teacher_id")
    if not teacher_id:
        return JsonResponse({"error": "未登录或会话已过期"}, status=401)
    
    data = parse_json(request)
    leave_id = data.get("请假申请ID")
    status = data.get("审批状态")  # 1-通过，2-拒绝
    comment = data.get("审批意见", "")
    
    if not leave_id or status not in [1, 2]:
        return JsonResponse({"error": "缺少必要参数"}, status=400)
    
    if status == 2 and not comment.strip():
        return JsonResponse({"error": "拒绝申请必须填写审批意见"}, status=400)
    
    try:
        with connection.cursor() as cur:
            # 验证该请假申请是否属于该教师的课程
            cur.execute(
                """SELECT l.请假申请ID, l.学号, l.课程ID, c.授课教师工号, l.开始日期, l.结束日期
                   FROM leave_requests l
                   JOIN courses c ON l.课程ID = c.课程ID
                   WHERE l.请假申请ID=%s AND c.授课教师工号=%s""",
                [leave_id, teacher_id],
            )
            leave_info = cur.fetchone()
            if not leave_info:
                return JsonResponse({"error": "无权操作此请假申请或申请不存在"}, status=403)
            
            # 更新请假申请状态
            cur.execute(
                """UPDATE leave_requests SET 审批状态=%s, 审批时间=NOW(), 审批人ID=%s, 审批意见=%s
                   WHERE 请假申请ID=%s""",
                [status, teacher_id, comment, leave_id],
            )
            
            # 如果审批通过，自动创建考勤记录（状态为请假）
            if status == 1:
                student_id, course_id, _, _, start_date, end_date = leave_info
                import datetime
                base_timestamp = int(time.time())
                start = datetime.datetime.strptime(str(start_date), '%Y-%m-%d')
                end = datetime.datetime.strptime(str(end_date), '%Y-%m-%d')
                current = start
                day_count = 0
                while current <= end:
                    attendance_id = f"ATT{student_id[-6:]}{base_timestamp}{day_count:02d}"
                    cur.execute(
                        """INSERT INTO attendances(考勤ID, 学号, 课程ID, 考勤日期, 考勤状态, 请假申请ID, 审批状态, 记录教师工号)
                           VALUES(%s, %s, %s, %s, 5, %s, 1, NULL)
                           ON DUPLICATE KEY UPDATE 考勤状态=5, 请假申请ID=%s, 审批状态=1""",
                        [attendance_id, student_id, course_id, current.date(), leave_id, leave_id],
                    )
                    current += datetime.timedelta(days=1)
                    day_count += 1
        
        return JsonResponse({"ok": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"更新失败: {str(e)}"}, status=500)

