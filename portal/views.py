from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection


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
    user_id = request.session.get("user_id")
    if not user_id:
        return None, JsonResponse({"error": "未登录"}, status=401)
    return user_id, None


@require_GET
def index(request):
    return JsonResponse({"message": "用户端 - 航班查询/登录/注册"})


@require_GET
def login_page(request):
    return render(request, "portal/login.html")


@require_GET
def register_page(request):
    return render(request, "portal/register.html")


@require_GET
def search_page(request):
    dep = request.GET.get("dep")
    arr = request.GET.get("arr")
    date = request.GET.get("date")
    flights = []
    if dep and arr and date:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT f.航班号, f.起飞时间, f.到达时间, f.经济舱价格, f.商务舱价格, f.头等舱价格, f.航班状态
                FROM flights f
                JOIN routes r ON f.航线ID = r.航线ID
                WHERE r.出发城市 = %s AND r.到达城市 = %s
                  AND DATE(f.起飞时间) = %s
                ORDER BY f.起飞时间
                """,
                [dep, arr, date],
            )
            cols = [c[0] for c in cur.description]
            flights = [dict(zip(cols, r)) for r in cur.fetchall()]
    return render(request, "portal/search.html", {"dep": dep, "arr": arr, "date": date, "flights": flights})


@require_GET
def orders_page(request):
    user_id = request.session.get("user_id")
    orders = []
    if user_id:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT o.订单号, o.订单时间, o.订单总金额, o.支付状态, o.订单状态,
                       od.航班号, od.机票价格, od.座位类型
                FROM orders o
                LEFT JOIN orderdetails od ON od.订单号 = o.订单号
                WHERE o.用户ID = %s
                ORDER BY o.订单时间 DESC
                """,
                [user_id],
            )
            cols = [c[0] for c in cur.description]
            orders = [dict(zip(cols, r)) for r in cur.fetchall()]
    return render(request, "portal/orders.html", {"orders": orders})


@require_GET
def profile_page(request):
    user_id = request.session.get("user_id")
    user = None
    if user_id:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT 用户ID, 用户名, 姓名, 性别, 手机号, 邮箱, 会员等级 FROM users WHERE 用户ID=%s",
                [user_id],
            )
            row = cur.fetchone()
            if row:
                cols = ["用户ID","用户名","姓名","性别","手机号","邮箱","会员等级"]
                user = dict(zip(cols, row))
    return render(request, "portal/profile.html", {"user": user})


@csrf_exempt
@require_POST
def update_profile(request):
    user_id, err = require_login(request)
    if err:
        return err
    data = parse_json(request)
    name = data.get("name")
    gender = data.get("gender")
    phone = data.get("phone")
    email = data.get("email")
    if not all([name, gender, phone, email]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            UPDATE users SET 姓名=%s, 性别=%s, 手机号=%s, 邮箱=%s WHERE 用户ID=%s
            """,
            [name, gender, phone, email, user_id],
        )
    return JsonResponse({"ok": True})


@require_GET
def passengers_page(request):
    user_id = request.session.get("user_id")
    passengers = []
    if user_id:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT 乘客ID, 姓名, 性别, 出生日期, 证件类型, 联系电话 FROM passengers WHERE 用户ID=%s ORDER BY 姓名",
                [user_id],
            )
            cols = [c[0] for c in cur.description]
            passengers = [dict(zip(cols, r)) for r in cur.fetchall()]
    return render(request, "portal/passengers.html", {"passengers": passengers})


@csrf_exempt
@require_POST
def passengers_create(request):
    user_id, err = require_login(request)
    if err:
        return err
    data = parse_json(request)
    passenger_id = data.get("passenger_id")
    name = data.get("name")
    gender = data.get("gender")
    birthday = data.get("birthday")
    id_type = data.get("id_type", 1)
    phone = data.get("phone")
    if not all([passenger_id, name, gender, birthday, phone]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO passengers(乘客ID, 用户ID, 姓名, 性别, 出生日期, 证件类型, 联系电话)
                VALUES(%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE 姓名=VALUES(姓名), 性别=VALUES(性别), 出生日期=VALUES(出生日期), 证件类型=VALUES(证件类型), 联系电话=VALUES(联系电话)
                """,
                [passenger_id, user_id, name, gender, birthday, int(id_type or 1), phone],
            )
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_POST
def passengers_delete(request):
    user_id, err = require_login(request)
    if err:
        return err
    data = parse_json(request)
    passenger_id = data.get("passenger_id")
    if not passenger_id:
        return JsonResponse({"error": "缺少乘客ID"}, status=400)
    with connection.cursor() as cur:
        cur.execute("DELETE FROM passengers WHERE 乘客ID=%s AND 用户ID=%s", [passenger_id, user_id])
    return JsonResponse({"ok": True})


@require_GET
def passengers_list(request):
    user_id, err = require_login(request)
    if err:
        return err
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 乘客ID, 姓名, 性别, 出生日期, 证件类型, 联系电话 FROM passengers WHERE 用户ID=%s ORDER BY 姓名",
            [user_id],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def passengers_update(request):
    user_id, err = require_login(request)
    if err:
        return err
    data = parse_json(request)
    passenger_id = data.get("passenger_id")
    name = data.get("name")
    gender = data.get("gender")
    birthday = data.get("birthday")
    phone = data.get("phone")
    if not all([passenger_id, name, gender, birthday, phone]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            UPDATE passengers SET 姓名=%s, 性别=%s, 出生日期=%s, 联系电话=%s
            WHERE 乘客ID=%s AND 用户ID=%s
            """,
            [name, gender, birthday, phone, passenger_id, user_id],
        )
    return JsonResponse({"ok": True})
@csrf_exempt
@require_POST
def register(request):
    data = parse_json(request)
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    gender = data.get("gender")
    phone = data.get("phone")
    email = data.get("email")
    user_id = data.get("user_id")
    if not all([username, password, name, gender, phone, email, user_id]):
        return JsonResponse({"error": "缺少必要字段"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users(用户ID, 用户名, 密码, 姓名, 性别, 手机号, 邮箱, 会员等级)
            VALUES(%s,%s,%s,%s,%s,%s,%s, %s)
            """,
            [user_id, username, password, name, gender, phone, email, 0],
        )
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def login(request):
    # 允许表单登录
    if request.content_type and request.content_type.startswith("application/x-www-form-urlencoded"):
        username = request.POST.get("username")
        password = request.POST.get("password")
        with connection.cursor() as cur:
            cur.execute(
                "SELECT 用户ID, 用户名 FROM users WHERE 用户名=%s AND 密码=%s",
                [username, password],
            )
            row = cur.fetchone()
        if not row:
            return HttpResponseRedirect("/ui/login")
        request.session["user_id"] = row[0]
        request.session["username"] = row[1]
        return HttpResponseRedirect("/ui/search")

    data = parse_json(request)
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return JsonResponse({"error": "缺少用户名或密码"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 用户ID, 用户名 FROM users WHERE 用户名=%s AND 密码=%s",
            [username, password],
        )
        row = cur.fetchone()
    if not row:
        return JsonResponse({"error": "用户名或密码错误"}, status=401)
    request.session["user_id"] = row[0]
    request.session["username"] = row[1]
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def logout(request):
    request.session.flush()
    return JsonResponse({"ok": True})


@require_GET
def search_flights(request):
    dep = request.GET.get("dep")
    arr = request.GET.get("arr")
    date = request.GET.get("date")
    if not all([dep, arr, date]):
        return JsonResponse({"error": "缺少查询条件"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT f.航班号, f.起飞时间, f.到达时间, f.经济舱价格, f.商务舱价格, f.头等舱价格, f.航班状态
            FROM flights f
            JOIN routes r ON f.航线ID = r.航线ID
            WHERE r.出发城市 = %s AND r.到达城市 = %s
              AND DATE(f.起飞时间) = %s
            ORDER BY f.起飞时间
            """,
            [dep, arr, date],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@require_GET
def list_seats(request):
    flight_no = request.GET.get("flight_no")
    if not flight_no:
        return JsonResponse({"error": "缺少航班号"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 座位号, 座位类型, 座位状态, 价格
            FROM seats WHERE 航班号=%s
            ORDER BY 座位号
            """,
            [flight_no],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def create_order(request):
    data = parse_json(request)
    user_id, err = require_login(request)
    if err:
        return err
    order_no = data.get("order_no")
    flight_no = data.get("flight_no")
    passenger_id = data.get("passenger_id")
    price = data.get("price")
    cabin = data.get("cabin_type")
    seat_no = data.get("seat_no")
    # order_no 若未提供则自动生成
    if not order_no:
        import time
        order_no = f"ORD{int(time.time())}"
    if not all([flight_no, passenger_id, price, cabin, seat_no]):
        return JsonResponse({"error": "参数不完整"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE seats SET 座位状态=1 WHERE 航班号=%s AND 座位号=%s AND 座位状态=0",
            [flight_no, seat_no],
        )
        if cur.rowcount == 0:
            return JsonResponse({"error": "座位已被占用或不存在"}, status=409)
        cur.execute(
            """
            INSERT INTO orders(订单号, 用户ID, 订单总金额, 支付状态, 订单状态)
            VALUES(%s,%s,%s, 0, 1)
            """,
            [order_no, user_id, price],
        )
        cur.execute(
            """
            INSERT INTO orderdetails(明细ID, 订单号, 航班号, 乘客ID, 机票价格, 座位类型, 座位号, 明细状态)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            [f"DTL{order_no}", order_no, flight_no, passenger_id, price, cabin, seat_no, 2],
        )
    return JsonResponse({"ok": True, "order_no": order_no})


@csrf_exempt
@require_POST
def pay_order(request):
    data = parse_json(request)
    order_no = data.get("order_no")
    amount = data.get("amount")
    method = data.get("method", 1)
    if not all([order_no, amount]):
        return JsonResponse({"error": "参数不完整"}, status=400)
    import time
    pay_id = f"PAY{int(time.time())}"
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO payments(支付ID, 订单号, 支付金额, 支付方式, 支付状态, 交易流水号)
            VALUES(%s,%s,%s,%s, 1, %s)
            """,
            [pay_id, order_no, amount, method, f"TRX{pay_id}"],
        )
        cur.execute("UPDATE orders SET 支付状态=1, 订单状态=2 WHERE 订单号=%s", [order_no])
    return JsonResponse({"ok": True, "pay_id": pay_id})


@require_GET
def order_detail_page(request):
    """订单详情页面"""
    order_no = request.GET.get("order_no")
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("/ui/login")
    if not order_no:
        return render(request, "portal/order_detail.html", {"error": "缺少订单号"})
    
    with connection.cursor() as cur:
        # 获取订单基本信息
        cur.execute(
            """
            SELECT o.订单号, o.订单时间, o.订单总金额, o.支付状态, o.订单状态
            FROM orders o
            WHERE o.订单号=%s AND o.用户ID=%s
            """,
            [order_no, user_id],
        )
        cols = [c[0] for c in cur.description]
        order = cur.fetchone()
        if not order:
            return render(request, "portal/order_detail.html", {"error": "未找到订单或无权限"})
        order = dict(zip(cols, order))
        
        # 获取订单明细（可能有多条）
        cur.execute(
            """
            SELECT od.明细ID, od.航班号, od.乘客ID, od.机票价格, od.座位类型, od.座位号, od.明细状态,
                   p.姓名 AS 乘客姓名, p.性别 AS 乘客性别,
                   f.起飞时间, f.到达时间, f.航班状态,
                   r.出发城市, r.到达城市,
                   CASE od.座位类型 WHEN 1 THEN '经济舱' WHEN 2 THEN '商务舱' WHEN 3 THEN '头等舱' END AS 舱位名称,
                   CASE od.明细状态 WHEN 1 THEN '待支付' WHEN 2 THEN '待出行' WHEN 3 THEN '已取消' WHEN 4 THEN '已出行' END AS 明细状态名称
            FROM orderdetails od
            LEFT JOIN passengers p ON p.乘客ID = od.乘客ID
            LEFT JOIN flights f ON f.航班号 = od.航班号
            LEFT JOIN routes r ON r.航线ID = f.航线ID
            WHERE od.订单号 = %s
            ORDER BY od.明细ID
            """,
            [order_no],
        )
        cols = [c[0] for c in cur.description]
        details = [dict(zip(cols, r)) for r in cur.fetchall()]
        order["details"] = details
        
        # 获取支付信息
        cur.execute(
            """
            SELECT 支付ID, 支付金额, 支付方式, 支付时间, 支付状态, 交易流水号,
                   CASE 支付方式 WHEN 1 THEN '支付宝' WHEN 2 THEN '微信' WHEN 3 THEN '银行卡' END AS 支付方式名称,
                   CASE 支付状态 WHEN 0 THEN '待支付' WHEN 1 THEN '支付成功' WHEN 2 THEN '支付失败' END AS 支付状态名称
            FROM payments
            WHERE 订单号 = %s
            ORDER BY 支付时间 DESC
            LIMIT 1
            """,
            [order_no],
        )
        cols = [c[0] for c in cur.description]
        payment = cur.fetchone()
        if payment:
            order["payment"] = dict(zip(cols, payment))
        else:
            order["payment"] = None
        
        # 状态文本映射
        status_map = {
            0: "待支付", 1: "已支付待确认", 2: "已确认待出行", 3: "已取消", 4: "已完成"
        }
        order["订单状态文本"] = status_map.get(order["订单状态"], "未知")
        order["支付状态文本"] = "已支付" if order["支付状态"] == 1 else "未支付"
    
    return render(request, "portal/order_detail.html", {"order": order})


@require_GET
def order_detail(request):
    """订单详情API（返回JSON）"""
    order_no = request.GET.get("order_no")
    user_id, err = require_login(request)
    if err:
        return err
    if not order_no:
        return JsonResponse({"error": "缺少订单号"}, status=400)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT o.订单号, o.订单时间, o.订单总金额, o.支付状态, o.订单状态,
                   od.航班号, od.机票价格, od.座位类型
            FROM orders o
            LEFT JOIN orderdetails od ON od.订单号 = o.订单号
            WHERE o.订单号=%s AND o.用户ID=%s
            """,
            [order_no, user_id],
        )
        cols = [c[0] for c in cur.description]
        row = cur.fetchone()
    if not row:
        return JsonResponse({"error": "未找到订单或无权限"}, status=404)
    return JsonResponse(dict(zip(cols, row)))


@require_GET
def order_history(request):
    user_id, err = require_login(request)
    if err:
        return err
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT o.订单号, o.订单时间, o.订单总金额, o.支付状态, o.订单状态,
                   od.航班号, od.机票价格, od.座位类型
            FROM orders o
            LEFT JOIN orderdetails od ON od.订单号 = o.订单号
            WHERE o.用户ID = %s
            ORDER BY o.订单时间 DESC
            """,
            [user_id],
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return JsonResponse({"items": rows})


@csrf_exempt
@require_POST
def cancel_order(request):
    data = parse_json(request)
    order_no = data.get("order_no")
    user_id, err = require_login(request)
    if err:
        return err
    if not order_no:
        return JsonResponse({"error": "缺少订单号"}, status=400)
    with connection.cursor() as cur:
        cur.execute("SELECT 用户ID FROM orders WHERE 订单号=%s", [order_no])
        row = cur.fetchone()
        if not row or row[0] != user_id:
            return JsonResponse({"error": "订单不存在或不属于当前用户"}, status=403)
        cur.execute("UPDATE orders SET 订单状态=3 WHERE 订单号=%s", [order_no])
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def create_change_request(request):
    data = parse_json(request)
    original_order = data.get("original_order")
    new_order = data.get("new_order")
    passenger_id = data.get("passenger_id")
    staff_id = data.get("staff_id") or "EMP0000001"
    fee = data.get("fee", 0)
    reason = data.get("reason", "用户发起改签")
    if not all([original_order, new_order, passenger_id]):
        return JsonResponse({"error": "参数不完整"}, status=400)
    import time
    change_id = data.get("change_id") or f"CHG{int(time.time())}"
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO changes(改签ID, 原订单号, 新订单号, 乘客ID, 工号, 改签费用, 改签原因, 改签状态)
            VALUES(%s,%s,%s,%s,%s,%s,%s, %s)
            """,
            [change_id, original_order, new_order, passenger_id, staff_id, fee, reason, 0],
        )
    return JsonResponse({"ok": True, "change_id": change_id})


@csrf_exempt
@require_POST
def confirm_change(request):
    data = parse_json(request)
    change_id = data.get("change_id")
    if not change_id:
        return JsonResponse({"error": "缺少改签ID"}, status=400)
    with connection.cursor() as cur:
        cur.execute("UPDATE changes SET 改签状态=1 WHERE 改签ID=%s", [change_id])
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def user_refund(request):
    data = parse_json(request)
    order_no = data.get("order_no")
    passenger_id = data.get("passenger_id")
    amount = data.get("amount", 0)
    if not all([order_no, passenger_id]):
        return JsonResponse({"error": "参数不完整"}, status=400)
    import time
    refund_id = f"REF{int(time.time())}"
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO refunds(退票ID, 订单号, 乘客ID, 工号, 退票金额, 退票原因, 退票状态)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            """,
            [refund_id, order_no, passenger_id, "用户自助", amount, "用户申请退票", 1],
        )
        cur.execute("UPDATE orders SET 订单状态=3 WHERE 订单号=%s", [order_no])
    return JsonResponse({"ok": True, "refund_id": refund_id})
