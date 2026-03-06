from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from functools import wraps


def require_admin_login(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("admin_id"):
            return HttpResponseRedirect("/sysadmin/ui/login")
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
        return HttpResponseRedirect("/sysadmin/ui")
    return HttpResponseRedirect("/sysadmin/ui/login")


@require_GET
def ui_login(request):
    if request.session.get("admin_id"):
        return HttpResponseRedirect("/sysadmin/ui")
    return render(request, "admin/login.html")


@csrf_exempt
@require_POST
def api_login(request):
    try:
        data = parse_json(request)
        emp_id = data.get("emp_id")
        password = data.get("password")
        if not emp_id or not password:
            return JsonResponse({"error": "缺少工号或密码"}, status=400)
        with connection.cursor() as cur:
            cur.execute(
                "SELECT 工号, 姓名 FROM staff WHERE 工号=%s AND 密码=%s AND 职位 LIKE '%%管理员%%'",
                [emp_id, password],
            )
            row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "工号或密码错误，或权限不足"}, status=401)
        request.session["admin_id"] = row[0]
        request.session["admin_name"] = row[1]
        request.session.save()
        if request.content_type and request.content_type.startswith("application/x-www-form-urlencoded"):
            return HttpResponseRedirect("/sysadmin/ui")
        return JsonResponse({"ok": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
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
def ui_users(request):
    return render(request, "admin/users.html")


@require_admin_login
@require_GET
def ui_staff(request):
    return render(request, "admin/staff.html")


@require_admin_login
@require_GET
def ui_flights(request):
    return render(request, "admin/flights.html")


@require_admin_login
@require_GET
def ui_logs(request):
    return render(request, "admin/logs.html")


@require_GET
def list_flights(request):
    """获取航班列表"""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT f.航班号, f.航线ID, f.飞机号, f.起飞时间, f.到达时间, 
                   f.经济舱价格, f.商务舱价格, f.头等舱价格, f.航班状态,
                   r.出发城市, r.到达城市
            FROM flights f
            LEFT JOIN routes r ON f.航线ID = r.航线ID
            ORDER BY f.起飞时间 DESC
            LIMIT 200
            """
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def list_routes(request):
    """获取航线列表（用于创建/修改航班时选择）"""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 航线ID, 出发城市, 到达城市, 距离 FROM routes WHERE 航线状态 = 1 ORDER BY 航线ID"
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def get_flight_detail(request):
    """获取航班详情"""
    flight_no = request.GET.get("flight_no")
    if not flight_no:
        return JsonResponse({"error": "缺少航班号"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT f.航班号, f.航线ID, f.飞机号, f.起飞时间, f.到达时间, 
                   f.经济舱价格, f.商务舱价格, f.头等舱价格, f.航班状态,
                   r.出发城市, r.到达城市
            FROM flights f
            LEFT JOIN routes r ON f.航线ID = r.航线ID
            WHERE f.航班号 = %s
            """,
            [flight_no],
        )
        row = cur.fetchone()
    if not row:
        return JsonResponse({"error": "未找到航班"}, status=404)
    cols = ["航班号", "航线ID", "飞机号", "起飞时间", "到达时间", "经济舱价格", "商务舱价格", "头等舱价格", "航班状态", "出发城市", "到达城市"]
    return JsonResponse(dict(zip(cols, row)))


@csrf_exempt
@require_POST
def create_flight(request):
    """创建新航班"""
    import json
    data = json.loads(request.body or b"{}")
    flight_no = data.get("flight_no")
    route_id = data.get("route_id")
    plane_no = data.get("plane_no")
    depart_time = data.get("depart_time")
    arrive_time = data.get("arrive_time")
    eco = data.get("eco_price")
    bus = data.get("bus_price")
    first = data.get("first_price")
    if not all([flight_no, route_id, plane_no, depart_time, arrive_time, eco, bus, first]):
        return JsonResponse({"error": "参数不完整，需要航班号、航线ID、飞机号、时间、价格"}, status=400)
    with connection.cursor() as cur:
        # 检查航班号是否已存在
        cur.execute("SELECT 航班号 FROM flights WHERE 航班号=%s", [flight_no])
        if cur.fetchone():
            return JsonResponse({"error": "航班号已存在"}, status=409)
        cur.execute(
            """
            INSERT INTO flights(航班号, 航线ID, 飞机号, 起飞时间, 到达时间, 经济舱价格, 商务舱价格, 头等舱价格, 航班状态)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s, 0)
            """,
            [flight_no, route_id, plane_no, depart_time, arrive_time, eco, bus, first],
        )
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def update_flight(request):
    """更新航班信息（可更新所有字段）"""
    import json
    data = json.loads(request.body or b"{}")
    flight_no = data.get("flight_no")
    if not flight_no:
        return JsonResponse({"error": "缺少航班号"}, status=400)
    
    # 构建更新字段
    updates = []
    params = []
    
    if "route_id" in data:
        updates.append("航线ID = %s")
        params.append(data["route_id"])
    if "plane_no" in data:
        updates.append("飞机号 = %s")
        params.append(data["plane_no"])
    if "depart_time" in data:
        updates.append("起飞时间 = %s")
        params.append(data["depart_time"])
    if "arrive_time" in data:
        updates.append("到达时间 = %s")
        params.append(data["arrive_time"])
    if "eco_price" in data:
        updates.append("经济舱价格 = %s")
        params.append(data["eco_price"])
    if "bus_price" in data:
        updates.append("商务舱价格 = %s")
        params.append(data["bus_price"])
    if "first_price" in data:
        updates.append("头等舱价格 = %s")
        params.append(data["first_price"])
    if "status" in data:
        updates.append("航班状态 = %s")
        params.append(data["status"])
    
    if not updates:
        return JsonResponse({"error": "没有要更新的字段"}, status=400)
    
    params.append(flight_no)
    
    with connection.cursor() as cur:
        cur.execute(
            f"UPDATE flights SET {', '.join(updates)} WHERE 航班号 = %s",
            params
        )
        if cur.rowcount == 0:
            return JsonResponse({"error": "航班不存在"}, status=404)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def update_flight_status(request):
    """更新航班状态（快捷接口）"""
    import json
    data = json.loads(request.body or b"{}")
    flight_no = data.get("flight_no")
    status = data.get("status")
    if flight_no is None or status is None:
        return JsonResponse({"error": "参数不完整"}, status=400)
    with connection.cursor() as cur:
        cur.execute("UPDATE flights SET 航班状态=%s WHERE 航班号=%s", [status, flight_no])
        if cur.rowcount == 0:
            return JsonResponse({"error": "航班不存在"}, status=404)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def delete_flight(request):
    """删除航班（谨慎操作）"""
    import json
    data = json.loads(request.body or b"{}")
    flight_no = data.get("flight_no")
    if not flight_no:
        return JsonResponse({"error": "缺少航班号"}, status=400)
    with connection.cursor() as cur:
        # 检查是否有订单关联
        cur.execute("SELECT COUNT(*) FROM orderdetails WHERE 航班号=%s", [flight_no])
        order_count = cur.fetchone()[0]
        if order_count > 0:
            return JsonResponse({"error": f"该航班已有 {order_count} 条订单记录，无法删除"}, status=409)
        cur.execute("DELETE FROM flights WHERE 航班号=%s", [flight_no])
        if cur.rowcount == 0:
            return JsonResponse({"error": "航班不存在"}, status=404)
    return JsonResponse({"ok": True})


@require_GET
def stats_route_income(request):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT r.出发城市, r.到达城市, SUM(od.机票价格) AS 收入
            FROM routes r
            JOIN flights f ON f.航线ID = r.航线ID
            JOIN orderdetails od ON od.航班号 = f.航班号
            GROUP BY r.出发城市, r.到达城市
            ORDER BY 收入 DESC
            """
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def stats_load_factor(request):
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT f.航班号,
                   SUM(CASE WHEN s.座位状态 = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS 客座率
            FROM flights f
            JOIN seats s ON s.航班号 = f.航班号
            GROUP BY f.航班号
            ORDER BY 客座率 DESC
            """
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def list_users(request):
    keyword = request.GET.get("q", "")
    where = ""
    params = []
    if keyword:
        where = "WHERE 用户ID=%s OR 用户名=%s OR 姓名=%s"
        params = [keyword, keyword, keyword]
    with connection.cursor() as cur:
        cur.execute(f"SELECT 用户ID, 用户名, 姓名, 性别, 手机号, 邮箱, 会员等级 FROM users {where} ORDER BY 姓名 LIMIT 200", params)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def save_user(request):
    import json
    data = json.loads(request.body or b"{}")
    user_id = data.get("用户ID")
    username = data.get("用户名")
    name = data.get("姓名")
    gender = data.get("性别")
    phone = data.get("手机号")
    email = data.get("邮箱")
    level = data.get("会员等级", 0)
    password = data.get("密码") or 'password123'
    if not all([user_id, username, name, gender, phone, email]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users(用户ID, 用户名, 密码, 姓名, 性别, 手机号, 邮箱, 会员等级)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE 用户名=VALUES(用户名), 姓名=VALUES(姓名), 性别=VALUES(性别), 手机号=VALUES(手机号), 邮箱=VALUES(邮箱), 会员等级=VALUES(会员等级)
            """,
            [user_id, username, password, name, gender, phone, email, int(level or 0)],
        )
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def delete_user(request):
    import json
    data = json.loads(request.body or b"{}")
    user_id = data.get("用户ID")
    if not user_id:
        return JsonResponse({"error": "缺少用户ID"}, status=400)
    with connection.cursor() as cur:
        cur.execute("DELETE FROM users WHERE 用户ID=%s", [user_id])
    return JsonResponse({"ok": True})


@require_GET
def list_staff(request):
    with connection.cursor() as cur:
        cur.execute("SELECT 工号, 姓名, 性别, 联系电话, 邮箱, 部门, 职位 FROM staff ORDER BY 入职时间 DESC")
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def save_staff(request):
    import json
    data = json.loads(request.body or b"{}")
    emp_id = data.get("工号")
    name = data.get("姓名")
    gender = data.get("性别")
    phone = data.get("联系电话")
    email = data.get("邮箱")
    dept = data.get("部门")
    title = data.get("职位")
    password = data.get("密码") or 'staff123'
    if not all([emp_id, name, gender, phone, email, dept, title]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO staff(工号, 姓名, 密码, 性别, 联系电话, 邮箱, 部门, 职位)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE 姓名=VALUES(姓名), 性别=VALUES(性别), 联系电话=VALUES(联系电话), 邮箱=VALUES(邮箱), 部门=VALUES(部门), 职位=VALUES(职位)
            """,
            [emp_id, name, password, gender, phone, email, dept, title],
        )
    return JsonResponse({"ok": True})


@require_GET
def list_logs(request):
    # 简化的“系统日志”：合并 refunds/changes/payments 的最近记录
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 'refund' AS 类型, 退票时间 AS 时间, 订单号 AS 关联, 退票金额 AS 数额, 退票原因 AS 描述 FROM refunds
            UNION ALL
            SELECT 'change', 改签时间, 新订单号, 改签费用, 改签原因 FROM changes
            UNION ALL
            SELECT 'payment', 支付时间, 订单号, 支付金额, CONCAT('方式', 支付方式) FROM payments
            ORDER BY 时间 DESC LIMIT 200
            """
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def create_seats_for_flight(request):
    """
    为指定航班批量生成基础座位布局：
    - 头等舱: 1排 A1-A4, 类型3
    - 商务舱: 1排 B1-B6, 类型2
    - 经济舱: 10排 C1-C30 (C1-C10为窗口/过道简化), 类型1
    价格按 flights 表三档价格写入。
    若座位已存在则跳过。
    """
    import json
    data = json.loads(request.body or b"{}")
    flight_no = data.get("flight_no")
    if not flight_no:
        return JsonResponse({"error": "缺少航班号"}, status=400)
    with connection.cursor() as cur:
        # 读取价格
        cur.execute(
            "SELECT 经济舱价格, 商务舱价格, 头等舱价格 FROM flights WHERE 航班号=%s",
            [flight_no],
        )
        price_row = cur.fetchone()
        if not price_row:
            return JsonResponse({"error": "航班不存在"}, status=404)
        eco_price, bus_price, first_price = price_row[0], price_row[1], price_row[2]

        # 头等舱
        for i in range(1, 5):
            cur.execute(
                """
                INSERT IGNORE INTO seats(航班号, 座位号, 座位类型, 座位状态, 价格)
                VALUES(%s,%s,3,0,%s)
                """,
                [flight_no, f"A{i}", first_price],
            )
        # 商务舱
        for i in range(1, 7):
            cur.execute(
                """
                INSERT IGNORE INTO seats(航班号, 座位号, 座位类型, 座位状态, 价格)
                VALUES(%s,%s,2,0,%s)
                """,
                [flight_no, f"B{i}", bus_price],
            )
        # 经济舱
        for i in range(1, 31):
            cur.execute(
                """
                INSERT IGNORE INTO seats(航班号, 座位号, 座位类型, 座位状态, 价格)
                VALUES(%s,%s,1,0,%s)
                """,
                [flight_no, f"C{i}", eco_price],
            )
    return JsonResponse({"ok": True})