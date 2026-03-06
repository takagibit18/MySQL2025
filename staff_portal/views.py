from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from functools import wraps


def require_staff_login(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("staff_id"):
            return HttpResponseRedirect("/staff/ui/login")
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
    if request.session.get("staff_id"):
        return HttpResponseRedirect("/staff/ui")
    return HttpResponseRedirect("/staff/ui/login")


@require_GET
def ui_login(request):
    if request.session.get("staff_id"):
        return HttpResponseRedirect("/staff/ui")
    return render(request, "staff/login.html")


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
                "SELECT 工号, 姓名 FROM staff WHERE 工号=%s AND 密码=%s",
                [emp_id, password],
            )
            row = cur.fetchone()
        if not row:
            return JsonResponse({"error": "工号或密码错误"}, status=401)
        request.session["staff_id"] = row[0]
        request.session["staff_name"] = row[1]
        request.session.save()
        if request.content_type and request.content_type.startswith("application/x-www-form-urlencoded"):
            return HttpResponseRedirect("/staff/ui")
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


@require_staff_login
@require_GET
def ui_home(request):
    return render(request, "staff/ui_home.html")


@require_staff_login
@require_GET
def ui_orders(request):
    return render(request, "staff/orders.html")


@require_staff_login
@require_GET
def ui_flights(request):
    return render(request, "staff/flights.html")


@require_staff_login
@require_GET
def ui_stats(request):
    return render(request, "staff/stats.html")


@require_GET
def get_user_by_idcard(request):
    idcard = request.GET.get("idcard")
    if not idcard:
        return JsonResponse({"error": "缺少身份证号"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 用户ID, 用户名, 姓名, 性别, 手机号, 邮箱, 会员等级 FROM users WHERE 用户ID=%s",
            [idcard],
        )
        row = cur.fetchone()
    if not row:
        return JsonResponse({"error": "未找到该用户"}, status=404)
    cols = ["用户ID", "用户名", "姓名", "性别", "手机号", "邮箱", "会员等级"]
    return JsonResponse(dict(zip(cols, row)))


@require_GET
def list_all_orders(request):
    keyword = request.GET.get("q", "").strip()
    sql = (
        """
        SELECT o.订单号, o.用户ID, o.订单时间, o.订单总金额, o.支付状态, o.订单状态,
               od.航班号, od.机票价格, od.座位类型
        FROM orders o
        LEFT JOIN orderdetails od ON od.订单号 = o.订单号
        {where}
        ORDER BY o.订单时间 DESC LIMIT 200
        """
    )
    where = ""
    params = []
    if keyword:
        where = "WHERE o.订单号 = %s OR o.用户ID = %s"
        params = [keyword, keyword]
    with connection.cursor() as cur:
        cur.execute(sql.format(where=where), params)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def assist_change_ticket(request):
    import json
    import time
    data = json.loads(request.body or b"{}")
    original_order = data.get("original_order")
    new_flight_no = data.get("new_flight_no")
    cabin_type = data.get("cabin_type")  # 1=经济舱, 2=商务舱, 3=头等舱
    staff_id = request.session.get("staff_id")
    fee = data.get("fee", 0)
    reason = data.get("reason", "工作人员协助改签")
    
    if not all([original_order, new_flight_no, cabin_type]) or not staff_id:
        return JsonResponse({"error": "参数不完整"}, status=400)
    
    cabin_type = int(cabin_type)
    if cabin_type not in [1, 2, 3]:
        return JsonResponse({"error": "舱位类型无效（1=经济舱, 2=商务舱, 3=头等舱）"}, status=400)
    
    with connection.cursor() as cur:
        # 1. 获取原订单信息
        cur.execute(
            """
            SELECT o.用户ID, o.订单总金额, od.乘客ID, od.航班号 AS 原航班号, od.座位号 AS 原座位号
            FROM orders o
            JOIN orderdetails od ON od.订单号 = o.订单号
            WHERE o.订单号 = %s AND od.明细状态 IN (1, 2)
            LIMIT 1
            """,
            [original_order],
        )
        order_info = cur.fetchone()
        if not order_info:
            return JsonResponse({"error": "原订单不存在或状态不允许改签"}, status=404)
        
        user_id, original_amount, passenger_id, old_flight_no, old_seat_no = order_info
        
        # 2. 查找新航班的可用座位（相同舱位类型，状态为0）
        cur.execute(
            """
            SELECT 座位号, 价格
            FROM seats
            WHERE 航班号 = %s AND 座位类型 = %s AND 座位状态 = 0
            ORDER BY 座位号
            LIMIT 1
            """,
            [new_flight_no, cabin_type],
        )
        seat_info = cur.fetchone()
        if not seat_info:
            return JsonResponse({"error": "新航班没有可用座位（该舱位类型）"}, status=409)
        
        new_seat_no, new_price = seat_info
        
        # 3. 生成新订单号
        new_order_no = f"ORD{int(time.time())}"
        
        # 4. 占用新座位
        cur.execute(
            "UPDATE seats SET 座位状态=1 WHERE 航班号=%s AND 座位号=%s AND 座位状态=0",
            [new_flight_no, new_seat_no],
        )
        if cur.rowcount == 0:
            return JsonResponse({"error": "座位已被占用，请重试"}, status=409)
        
        # 5. 创建新订单
        cur.execute(
            """
            INSERT INTO orders(订单号, 用户ID, 订单总金额, 支付状态, 订单状态)
            VALUES(%s, %s, %s, 0, 1)
            """,
            [new_order_no, user_id, new_price],
        )
        
        # 6. 创建新订单明细
        cur.execute(
            """
            INSERT INTO orderdetails(明细ID, 订单号, 航班号, 乘客ID, 机票价格, 座位类型, 座位号, 明细状态)
            VALUES(%s, %s, %s, %s, %s, %s, %s, 2)
            """,
            [f"DTL{new_order_no}", new_order_no, new_flight_no, passenger_id, new_price, cabin_type, new_seat_no],
        )
        
        # 7. 创建改签记录
        change_id = f"CHG{int(time.time())}"
        cur.execute(
            """
            INSERT INTO changes(改签ID, 原订单号, 新订单号, 乘客ID, 工号, 改签费用, 改签原因, 改签状态)
            VALUES(%s, %s, %s, %s, %s, %s, %s, 1)
            """,
            [change_id, original_order, new_order_no, passenger_id, staff_id, fee, reason],
        )
        
        # 8. 更新原订单明细状态为已改签（3）
        cur.execute(
            "UPDATE orderdetails SET 明细状态=3 WHERE 订单号=%s AND 明细状态 IN (1, 2)",
            [original_order],
        )
        
        # 9. 释放原座位（如果原订单明细状态已改为3，触发器会自动释放，但这里手动释放更安全）
        cur.execute(
            "UPDATE seats SET 座位状态=0 WHERE 航班号=%s AND 座位号=%s",
            [old_flight_no, old_seat_no],
        )
    
    return JsonResponse({
        "ok": True,
        "change_id": change_id,
        "new_order_no": new_order_no,
        "new_seat_no": new_seat_no,
        "new_price": float(new_price)
    })


@csrf_exempt
@require_POST
def create_refund(request):
    import json
    data = json.loads(request.body or b"{}")
    refund_id = data.get("refund_id")
    order_no = data.get("order_no")
    passenger_id = data.get("passenger_id")
    staff_id = data.get("staff_id")
    amount = data.get("amount", 0)
    reason = data.get("reason", "工作人员代办退票")
    if not all([order_no, passenger_id, staff_id]):
        return JsonResponse({"error": "参数不完整"}, status=400)
    refund_id = refund_id or f"REF{order_no}"
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO refunds(退票ID, 订单号, 乘客ID, 工号, 退票金额, 退票原因, 退票状态)
            VALUES(%s,%s,%s,%s,%s,%s, %s)
            """,
            [refund_id, order_no, passenger_id, staff_id, amount, reason, 1],
        )
        cur.execute("UPDATE orders SET 订单状态=3 WHERE 订单号=%s", [order_no])
    return JsonResponse({"ok": True, "refund_id": refund_id})


@require_GET
def list_flights(request):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 航班号, 起飞时间, 到达时间, 航班状态 FROM flights ORDER BY 起飞时间 DESC LIMIT 200"
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def update_seat_status(request):
    import json
    data = json.loads(request.body or b"{}")
    flight_no = data.get("flight_no")
    seat_no = data.get("seat_no")
    status = data.get("status")
    if not all([flight_no, seat_no]) or status is None:
        return JsonResponse({"error": "参数不完整"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE seats SET 座位状态=%s WHERE 航班号=%s AND 座位号=%s",
            [status, flight_no, seat_no],
        )
    return JsonResponse({"ok": True})


@require_GET
def stats_route_income(request):
    """航线收入统计"""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT r.出发城市, r.到达城市, SUM(od.机票价格) AS 收入
            FROM routes r
            JOIN flights f ON f.航线ID = r.航线ID
            JOIN orderdetails od ON od.航班号 = f.航班号
            WHERE od.明细状态 IN (2, 4)  -- 只统计已确认待出行和已出行的订单
            GROUP BY r.出发城市, r.到达城市
            ORDER BY 收入 DESC
            """
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def stats_load_factor(request):
    """客座率统计"""
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
def get_order_detail(request):
    """获取订单详情（用于改签时获取原订单信息）"""
    order_no = request.GET.get("order_no")
    if not order_no:
        return JsonResponse({"error": "缺少订单号"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT o.订单号, o.用户ID, o.订单总金额, o.订单状态,
                   od.航班号, od.乘客ID, od.座位类型, od.座位号, od.明细状态
            FROM orders o
            JOIN orderdetails od ON od.订单号 = o.订单号
            WHERE o.订单号 = %s
            LIMIT 1
            """,
            [order_no],
        )
        row = cur.fetchone()
    if not row:
        return JsonResponse({"error": "未找到订单"}, status=404)
    cols = ["订单号", "用户ID", "订单总金额", "订单状态", "航班号", "乘客ID", "座位类型", "座位号", "明细状态"]
    return JsonResponse(dict(zip(cols, row)))


@require_GET
def list_available_flights(request):
    """获取可用航班列表（用于改签时选择新航班）"""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT f.航班号, f.起飞时间, f.到达时间, f.经济舱价格, f.商务舱价格, f.头等舱价格, f.航班状态,
                   r.出发城市, r.到达城市
            FROM flights f
            JOIN routes r ON f.航线ID = r.航线ID
            WHERE f.航班状态 = 0 AND f.起飞时间 > NOW()
            ORDER BY f.起飞时间
            LIMIT 100
            """
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})
