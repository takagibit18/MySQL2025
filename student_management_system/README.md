# 学生管理系统

基于Django框架开发的学生管理系统，参照机票预订系统的结构设计。本系统实现了学生、教师、管理员三个角色的完整功能，并自主设计开发了考勤管理模块。

## 项目结构

```
student_management_system/
├── student_site/                    # Django主项目配置
│   ├── __init__.py
│   ├── settings.py                  # 项目设置（数据库、静态文件、媒体文件等）
│   ├── urls.py                      # 主路由配置（包含各子应用路由）
│   └── wsgi.py                      # WSGI配置
│
├── student_portal/                  # 学生门户模块
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py                     # 学生端视图函数（登录、选课、成绩、考勤、请假申请等）
│   └── urls.py                      # 学生端路由配置
│
├── teacher_portal/                  # 教师门户模块
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py                     # 教师端视图函数（登录、课程管理、成绩管理、考勤管理、请假审批等）
│   └── urls.py                      # 教师端路由配置
│
├── admin_portal/                    # 管理员门户模块
│   ├── __init__.py
│   ├── apps.py
│   ├── forms.py                     # ModelForm表单定义
│   ├── views.py                     # 管理员端视图函数（学生/教师/班级/课程管理、认证授权等）
│   └── urls.py                      # 管理员端路由配置
│
├── templates/                       # 模板文件目录
│   ├── base.html                    # 基础模板（学生端）
│   ├── admin/                       # 管理员端模板
│   │   ├── base_admin.html          # 管理员基础模板
│   │   ├── login.html               # 管理员登录页
│   │   ├── ui_home.html             # 管理员首页
│   │   ├── students.html            # 学生管理页
│   │   ├── teachers.html            # 教师管理页
│   │   ├── classes.html             # 班级管理页
│   │   ├── courses.html             # 课程管理页
│   │   ├── auth.html                # 认证和授权页
│   │   └── add.html                 # ModelForm示例页
│   ├── student/                     # 学生端模板
│   │   ├── login.html               # 学生登录页
│   │   ├── profile.html             # 个人信息页
│   │   ├── courses.html             # 选课管理页
│   │   ├── grades.html              # 成绩查询页
│   │   ├── attendance.html          # 考勤查询和请假申请页
│   │   ├── articles.html            # Django模板示例页
│   │   └── articles_login.html      # Django表单示例页
│   └── teacher/                     # 教师端模板
│       ├── base_teacher.html        # 教师基础模板
│       ├── login.html               # 教师登录页
│       ├── ui_home.html             # 教师首页
│       ├── courses.html             # 我的课程页
│       ├── students.html            # 查看学生名单页
│       ├── grades.html              # 成绩管理页（支持Excel导入）
│       ├── attendance.html          # 考勤管理页（点名功能）
│       └── leave_requests.html      # 请假申请查看和审批页
│
├── static/                          # 静态文件目录
│   └── img/                         # 图片资源
│       ├── img.png                  # 导航栏Logo（登录后）
│       ├── img_1.png               # 登录页Logo
│       └── ddc3e173e4ba499e74d300280d64a07.png
│
├── media/                           # 媒体文件目录（用户上传的文件）
│   └── medical_certificates/        # 病假条图片存储目录
│
├── database.sql                     # 数据库SQL脚本（基础表结构）
├── 考勤模块数据库扩展.sql            # 考勤模块数据库扩展SQL
├── 数据库ER图说明.md                 # 数据库ER图说明文档
├── generate_grade_excel.py          # 生成成绩导入Excel示例文件的脚本
├── manage.py                        # Django管理脚本
└── README.md                        # 本文件
```

## 实现思路

### 整体架构设计

本系统采用**多应用模块化架构**，参照机票预订系统的设计模式：

1. **分离式设计**：学生、教师、管理员三个角色分别使用独立的Django应用（student_portal、teacher_portal、admin_portal）
2. **统一配置**：所有应用共享student_site主项目配置
3. **模板继承**：使用Django模板继承机制，每个角色有独立的基础模板
4. **路由分离**：每个应用有独立的路由文件，通过主路由include包含

### 技术栈

- **后端框架**：Django 5.0.7
- **数据库**：MySQL 8.0（使用原生SQL，不使用ORM）
- **前端框架**：Bootstrap 5.3.3
- **JavaScript**：原生JS + Fetch API（AJAX异步请求）
- **文件存储**：Django MEDIA目录（用于上传文件）

### 核心实现机制

#### 1. 会话管理（Session-Based Authentication）

所有角色使用Django Session实现登录状态管理：
- 登录成功后，在`request.session`中存储用户ID和姓名
- 使用装饰器`@require_login`、`@require_teacher_login`、`@require_admin_login`保护需要登录的视图
- 会话数据存储在数据库`django_session`表中

#### 2. 数据库操作

采用原生SQL操作，不使用Django ORM：
- 使用`django.db.connection`获取数据库连接
- 使用`cursor.execute()`执行SQL语句
- 手动处理数据转换和错误处理

#### 3. 前后端交互

采用AJAX异步请求模式：
- 前端使用Fetch API发送请求
- 后端返回JSON格式数据
- 前端动态更新页面内容，无需刷新

#### 4. 文件上传处理

- 使用Django的`request.FILES`接收上传文件
- 文件保存在`MEDIA_ROOT`目录下
- 通过`MEDIA_URL`配置访问路径

---

## 考勤管理模块详细设计

考勤管理模块是本系统自主设计开发的核心模块，实现了完整的考勤管理流程，包括教师点名、学生请假申请、教师审批等功能。

### 一、模块功能设计

#### 1. 教师端考勤管理（点名功能）

**功能特性：**
- **学生列表展示**：选择课程和日期后，展示该课程的所有学生列表
- **头像点击切换**：点击学生头像可以循环切换考勤状态（出勤→迟到→早退→缺勤→请假→出勤）
- **状态标签选择**：点击状态标签显示下拉菜单，可直接选择状态
- **一键全到**：一键将所有学生设置为出勤状态
- **批量选择**：支持全选/取消全选学生
- **批量保存**：只保存选中的学生考勤记录
- **单独保存**：每行有独立的保存按钮
- **行内编辑**：备注信息可直接在表格中编辑

**技术实现：**
- **前端技术**：
  - 复杂表格操作：使用JavaScript动态生成表格，支持行内编辑
  - 批量选择：使用复选框实现全选/单选功能
  - 状态流转UI：不同状态显示不同颜色的Tag标签
  - 头像交互：使用CSS3动画效果，点击头像切换状态
  - AJAX异步提交：使用Fetch API发送POST请求保存数据

- **后端技术**：
  - 视图函数：`add_attendance()` - 单个保存，`batch_attendance()` - 批量保存
  - 数据库操作：使用原生SQL插入/更新考勤记录
  - ID生成：`ATT{学号后6位}{时间戳后6位}` = 15位唯一ID

**访问地址：** `http://127.0.0.1:8000/teacher/ui/attendance`

**关键代码位置：**
- 前端模板：`templates/teacher/attendance.html`
- 后端视图：`teacher_portal/views.py` - `add_attendance()`, `batch_attendance()`
- 路由配置：`teacher_portal/urls.py` - `path("attendance/add", ...)`, `path("attendance/batch", ...)`

#### 2. 学生端请假申请功能

**功能特性：**
- **在线填写请假单**：选择课程、请假类型、日期范围、填写请假理由
- **病假条图片上传**：
  - 支持图片预览功能
  - 病假类型必须上传图片（可选，已改为非必填）
  - 支持jpg、png格式，最大20MB
  - 图片保存在`media/medical_certificates/`目录
- **查看请假记录**：显示请假申请的审批状态和历史记录

**技术实现：**
- **前端技术**：
  - 文件上传：使用HTML5的`<input type="file">`元素
  - 图片预览：使用FileReader API实现客户端预览
  - 表单验证：HTML5客户端验证 + JavaScript服务端验证
  - FormData提交：使用FormData对象发送文件数据

- **后端技术**：
  - 视图函数：`submit_leave_request()` - 提交请假申请
  - 文件处理：使用Django的`request.FILES`接收文件
  - 文件存储：保存到`MEDIA_ROOT/medical_certificates/`目录
  - ID生成：`LV{学号后8位}{时间戳后5位}` = 15位唯一ID
  - 数据库操作：插入请假申请记录到`leave_requests`表

**访问地址：** `http://127.0.0.1:8000/ui/attendance`

**关键代码位置：**
- 前端模板：`templates/student/attendance.html`
- 后端视图：`student_portal/views.py` - `submit_leave_request()`
- 路由配置：`student_portal/urls.py` - `path("api/leave-request", ...)`

#### 3. 教师端请假审批功能

**功能特性：**
- **查看请假申请**：查看自己课程的所有请假申请
- **筛选功能**：可按课程和状态筛选（全部/待审批/已通过/已拒绝）
- **审批操作**：
  - **通过申请**：填写审批意见（可选），自动为请假期间创建考勤记录（状态为请假）
  - **拒绝申请**：必须填写审批意见
- **查看详情**：显示学生信息、课程信息、请假理由、病假条图片（可点击放大）

**技术实现：**
- **前端技术**：
  - 动态表格：使用JavaScript动态生成表格
  - 模态框：使用Bootstrap Modal显示详情
  - 状态筛选：使用按钮组实现状态切换
  - 图片查看：点击图片在新窗口打开大图

- **后端技术**：
  - 视图函数：
    - `list_leave_requests()` - 列出请假申请（支持课程和状态筛选）
    - `get_leave_request_detail()` - 获取请假申请详情
    - `update_leave_status()` - 更新审批状态
  - 权限验证：只能审批自己课程的请假申请
  - 自动创建考勤记录：审批通过时，为请假期间的每一天创建考勤记录
  - 数据库操作：更新`leave_requests`表，插入`attendances`表记录

**访问地址：** `http://127.0.0.1:8000/teacher/ui/leave-requests`

**关键代码位置：**
- 前端模板：`templates/teacher/leave_requests.html`
- 后端视图：`teacher_portal/views.py` - `list_leave_requests()`, `get_leave_request_detail()`, `update_leave_status()`
- 路由配置：`teacher_portal/urls.py` - `path("leave-requests/list", ...)`, `path("leave-requests/detail", ...)`, `path("leave-requests/update-status", ...)`

### 二、数据库设计

#### 1. 考勤表（attendances）扩展

**基础字段：**
- `考勤ID` (CHAR(15), PK) - 主键
- `学号` (CHAR(12), FK) - 外键关联students表
- `课程ID` (CHAR(10), FK) - 外键关联courses表
- `考勤日期` (DATE) - 考勤日期
- `考勤状态` (TINYINT) - 1-出勤，2-迟到，3-早退，4-缺勤，5-请假
- `备注` (VARCHAR(200)) - 备注信息
- `记录教师工号` (CHAR(10), FK) - 外键关联teachers表

**扩展字段（考勤模块）：**
- `请假申请ID` (CHAR(15)) - 关联的请假申请ID
- `审批状态` (TINYINT) - 0-未审批，1-已通过，2-已拒绝
- `审批时间` (DATETIME) - 审批时间
- `审批人ID` (CHAR(10)) - 审批人ID（教师工号）

#### 2. 请假申请表（leave_requests）

**字段设计：**
- `请假申请ID` (CHAR(15), PK) - 主键，格式：LV{学号后8位}{时间戳后5位}
- `学号` (CHAR(12), FK) - 外键关联students表
- `课程ID` (CHAR(10), FK) - 外键关联courses表
- `请假类型` (VARCHAR(20)) - 病假、事假、其他
- `开始日期` (DATE) - 请假开始日期
- `结束日期` (DATE) - 请假结束日期
- `请假理由` (TEXT) - 请假理由
- `病假条图片` (VARCHAR(255)) - 病假条图片路径（存储在media目录）
- `申请时间` (DATETIME) - 申请时间
- `审批状态` (TINYINT) - 0-待审批，1-已通过，2-已拒绝
- `审批时间` (DATETIME) - 审批时间
- `审批人ID` (CHAR(10)) - 审批人ID（教师工号）
- `审批意见` (VARCHAR(500)) - 审批意见

**索引设计：**
- 主键索引：`请假申请ID`
- 普通索引：`学号`、`课程ID`、`审批状态`、`(开始日期, 结束日期)`
- 外键约束：`学号` → `students.学号`，`课程ID` → `courses.课程ID`

### 三、业务流程设计

#### 1. 考勤点名流程

```
教师登录
  ↓
选择课程和日期
  ↓
加载学生列表
  ↓
点击头像切换状态 / 点击状态标签选择状态
  ↓
填写备注（可选）
  ↓
选择要保存的学生（批量选择）
  ↓
点击"批量保存"或"保存"（单个）
  ↓
后端验证数据
  ↓
保存到数据库
  ↓
返回成功提示
```

#### 2. 请假申请流程

```
学生登录
  ↓
进入考勤查询页面
  ↓
点击"申请请假"
  ↓
填写请假信息：
  - 选择课程
  - 选择请假类型
  - 选择日期范围
  - 填写请假理由
  - 上传病假条（病假可选）
  ↓
提交申请
  ↓
后端保存请假申请
  ↓
返回成功提示
  ↓
状态：待审批
```

#### 3. 请假审批流程

```
教师登录
  ↓
进入请假申请页面
  ↓
查看请假申请列表
  ↓
点击"查看详情"
  ↓
查看请假信息：
  - 学生信息
  - 课程信息
  - 请假理由
  - 病假条图片
  ↓
填写审批意见
  ↓
选择操作：
  - 通过：自动创建考勤记录（状态为请假）
  - 拒绝：必须填写审批意见
  ↓
后端更新审批状态
  ↓
如果通过，自动创建考勤记录
  ↓
返回成功提示
```

### 四、技术难点与解决方案

#### 1. 复杂表格操作

**难点：** 实现行内编辑、批量选择、状态切换等功能

**解决方案：**
- 使用JavaScript动态生成表格HTML
- 为每个单元格添加唯一ID（如`status_${index}`）
- 使用事件委托处理点击事件
- 维护一个数据数组，同步更新DOM和数组

#### 2. 文件上传与预览

**难点：** 实现图片上传、预览、存储

**解决方案：**
- 使用HTML5 FileReader API实现客户端预览
- 使用Django的`request.FILES`接收文件
- 使用`MEDIA_ROOT`和`MEDIA_URL`配置文件存储和访问
- 生成唯一文件名避免冲突

#### 3. 状态流转UI设计

**难点：** 不同状态显示不同颜色，状态切换流畅

**解决方案：**
- 使用CSS类定义不同状态的颜色样式
- 使用JavaScript动态切换CSS类
- 使用CSS3 transition实现平滑过渡效果

#### 4. 批量操作性能优化

**难点：** 批量保存时避免重复插入

**解决方案：**
- 使用`ON DUPLICATE KEY UPDATE`或先查询后更新
- 对于考勤记录，先检查是否存在，存在则更新，不存在则插入
- 使用事务确保数据一致性

#### 5. 权限控制

**难点：** 确保教师只能操作自己课程的请假申请

**解决方案：**
- 在SQL查询中添加条件：`WHERE c.授课教师工号=%s`
- 在更新前验证权限：查询请假申请是否属于该教师的课程
- 使用装饰器统一处理权限验证

### 五、模块特色功能

1. **头像点击切换状态**：创新的交互方式，点击头像循环切换考勤状态
2. **一键全到**：快速设置所有学生为出勤状态
3. **批量选择保存**：支持选择部分学生进行批量保存
4. **图片预览**：上传前可以预览图片，提升用户体验
5. **自动创建考勤记录**：审批通过时自动为请假期间创建考勤记录
6. **状态流转UI**：不同状态使用不同颜色的Tag标签，直观清晰

---

## 第一部分：Django框架基础

### 一、路由系统（URL Routing）

路由系统是Django的核心功能之一，负责将用户访问的URL地址映射到对应的视图函数。

**在本项目中的实现：**

**① 基础路由配置**
```python
# student_site/urls.py - 主路由文件
urlpatterns = [
    path("", include("student_portal.urls")),  # 包含子路由
    path("teacher/", include("teacher_portal.urls")),
    path("admin_portal/", include("admin_portal.urls")),
]
```

**② 路由参数传递**
```python
# student_portal/urls.py
path("articles/<int:year>/<int:month>/<str:slug>/", views.article_detail),
```

**访问示例：**
- 路由参数示例：`http://127.0.0.1:8000/articles/2020/05/python/`
- 基础路由示例：`http://127.0.0.1:8000/articles/`
- 表单示例：`http://127.0.0.1:8000/articles/login`

### 二、基于函数的视图（Function-Based Views）

视图函数是Django处理HTTP请求的核心。每个视图函数接收一个`request`对象，然后返回一个`HttpResponse`对象。

**访问示例：**
- JSON视图：`http://127.0.0.1:8000/articles/current`
- 模板视图：`http://127.0.0.1:8000/articles/`

### 三、Django模板系统（Template System）

模板系统将HTML页面设计和Python业务逻辑分离。

**访问示例：**
- 文章列表页面：`http://127.0.0.1:8000/articles/`

### 四、表单处理（Form Handling）

表单是Web应用中用户与服务器交互的重要方式。

**访问示例：**
- 表单示例页面：`http://127.0.0.1:8000/articles/login`
- 实际登录页面：`http://127.0.0.1:8000/ui/login`

---

## 第二部分：Django框架进阶

### 一、会话实现登录（Session-Based Authentication）

会话（Session）是一种在服务器端存储用户状态信息的机制。

**访问示例：**
- 登录页面：`http://127.0.0.1:8000/ui/login`
- 登录后访问个人信息：`http://127.0.0.1:8000/ui/profile`

### 二、ModelForm（模型表单）

ModelForm是Django提供的一个高级功能，它可以根据数据库模型自动生成表单。

**访问示例：**
- ModelForm示例页面：`http://127.0.0.1:8000/admin_portal/ui/add`

---

## 第三部分：学生管理系统功能

### 学生模块功能
- 学生登录（使用会话）
- 个人信息查看
- 选课管理（选课、退选，支持7天退选限制）
- 成绩查询
- 考勤查询
- **请假申请**（在线填写、图片上传、状态查询）

### 教师模块功能
- 教师登录（使用会话）
- 我的课程管理
- 查看学生名单
- 成绩录入和管理（支持Excel批量导入）
- **考勤管理**（点名功能：头像点击切换、批量选择、一键全到）
- **请假申请查看和审批**

### 管理员模块功能
- 管理员登录（使用会话）
- 学生管理（更改：添加/删除/修改属性）
- 教师管理（更改：添加/删除/修改属性）
- 班级管理（更改：添加/删除/修改属性）
- 课程管理（更改：添加/删除/修改属性）
- 认证和授权（用户权限、权限组管理）
- ModelForm示例页面

---

## 数据库设计

数据库SQL脚本位于`database.sql`和`考勤模块数据库扩展.sql`，包含以下表：

### 基础表（database.sql）
1. **students** - 学生表
2. **teachers** - 教师表
3. **admins** - 管理员表
4. **classes** - 班级表
5. **courses** - 课程表
6. **enrollments** - 选课表
7. **grades** - 成绩表
8. **attendances** - 考勤表（基础字段）

### 考勤模块扩展表（考勤模块数据库扩展.sql）
1. **attendances表扩展** - 添加请假相关字段
2. **leave_requests** - 请假申请表

详细的数据库设计说明请参考`数据库ER图说明.md`文件。

---

## 安装和运行

### 1. 创建数据库

```bash
# 创建基础数据库和表
mysql -u root -p < database.sql

# 扩展考勤模块（执行扩展SQL）
mysql -u root -p < 考勤模块数据库扩展.sql
```

### 2. 安装依赖

```bash
pip install django mysqlclient openpyxl pandas
```

### 3. 配置数据库连接

编辑`student_site/settings.py`中的数据库配置：
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "student_management",
        "USER": "root",
        "PASSWORD": "your_password",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}
```

### 4. 运行服务器

```bash
cd student_management_system
python manage.py runserver
```

### 5. 访问系统

- **学生端**：http://127.0.0.1:8000/ui/login
- **教师端**：http://127.0.0.1:8000/teacher/ui/login
- **管理员端**：http://127.0.0.1:8000/admin_portal/ui/login

---

## 测试账号

### 学生账号
- 学号：`2021001001`
- 密码：`123456`

### 教师账号
- 工号：`T001`
- 密码：`123456`

### 管理员账号
- 管理员ID：`ADMIN001`
- 密码：`admin123`

---

## 路由说明

### 学生端路由
- `/` - 首页
- `/articles/` - 文章列表（模板示例）
- `/articles/<year>/<month>/<slug>/` - 文章详情（路由参数示例）
- `/articles/current` - 当前文章（JSON视图示例）
- `/articles/login` - 表单功能示例页面
- `/ui/login` - 登录页面
- `/ui/profile` - 个人信息
- `/ui/courses` - 选课管理
- `/ui/grades` - 成绩查询
- `/ui/attendance` - 考勤查询和请假申请

### 教师端路由
- `/teacher/ui/login` - 教师登录
- `/teacher/ui` - 教师首页
- `/teacher/ui/courses` - 我的课程
- `/teacher/ui/students` - 查看学生名单
- `/teacher/ui/grades` - 成绩管理（支持Excel导入）
- `/teacher/ui/attendance` - 考勤管理（点名功能）
- `/teacher/ui/leave-requests` - 请假申请查看和审批

### 管理员端路由
- `/admin_portal/ui/login` - 管理员登录
- `/admin_portal/ui` - 管理员首页
- `/admin_portal/ui/students` - 学生管理
- `/admin_portal/ui/teachers` - 教师管理
- `/admin_portal/ui/classes` - 班级管理
- `/admin_portal/ui/courses` - 课程管理
- `/admin_portal/ui/auth` - 认证和授权
- `/admin_portal/ui/add` - ModelForm示例

---

## 技术特点

1. **模块化设计**：参照机票预订系统，采用多模块架构
2. **会话管理**：使用Django Session实现用户登录状态管理
3. **表单处理**：使用Django Form和ModelForm进行表单验证
4. **模板系统**：使用Django模板继承和模板变量
5. **路由系统**：支持路由参数和include包含路由
6. **数据库操作**：使用原生SQL进行数据库操作
7. **文件上传**：使用Django MEDIA目录存储上传文件
8. **AJAX异步**：使用Fetch API实现前后端异步交互

---

## 开发环境要求

- Python 3.8+
- Django 5.0.7
- MySQL 8.0+
- Bootstrap 5.3.3
- 浏览器（Chrome、Firefox等）

---

## 注意事项

1. 数据库部分只需执行SQL脚本创建，不需要使用Django的migrate命令
2. 确保MySQL服务已启动
3. 修改数据库连接配置以匹配你的环境
4. 首次运行前需要执行`database.sql`和`考勤模块数据库扩展.sql`创建数据库和表结构
5. 确保`media`目录有写入权限（用于存储上传的文件）
6. 静态文件通过Django的`STATIC_URL`配置访问

---

## 考勤模块使用说明

### 教师端考勤管理

1. **登录教师端**（工号：T001，密码：123456）
2. **进入考勤管理**：导航栏 → "考勤管理"
3. **选择课程和日期**：选择要考勤的课程和日期
4. **加载学生列表**：点击"加载学生列表"按钮
5. **进行点名**：
   - 点击学生头像切换状态
   - 或点击状态标签选择状态
   - 填写备注（可选）
   - 选择要保存的学生（批量选择）
   - 点击"批量保存"或"保存"按钮

### 学生端请假申请

1. **登录学生端**（学号：2021001001，密码：123456）
2. **进入考勤查询**：导航栏 → "考勤查询"
3. **申请请假**：点击"申请请假"按钮
4. **填写请假信息**：
   - 选择课程
   - 选择请假类型（病假、事假、其他）
   - 选择日期范围
   - 填写请假理由
   - 上传病假条图片（可选，最大20MB）
5. **提交申请**：点击"提交申请"按钮
6. **查看状态**：在请假记录列表中查看审批状态

### 教师端请假审批

1. **登录教师端**（工号：T001，密码：123456）
2. **进入请假申请**：导航栏 → "请假申请"
3. **查看申请列表**：可以按课程和状态筛选
4. **查看详情**：点击"查看详情"按钮
5. **审批操作**：
   - **通过**：填写审批意见（可选），点击"通过"按钮
   - **拒绝**：填写审批意见（必填），点击"拒绝"按钮
6. **自动创建考勤记录**：审批通过后，系统自动为请假期间创建考勤记录

---

## 项目特色

1. **完整的考勤管理流程**：从点名到请假申请到审批的完整闭环
2. **创新的交互设计**：头像点击切换状态、批量选择等
3. **文件上传功能**：支持图片上传和预览
4. **状态流转UI**：不同状态使用不同颜色的Tag标签
5. **Excel批量导入**：支持成绩批量导入
6. **权限控制**：严格的权限验证机制
