## 面向生产环境的 SQL 入门指南（基于机票预订系统）

本指南结合本项目中的机票预订系统，介绍一些**在生产环境中需要注意的 SQL 与数据库设计基础知识**，适合已经会写简单 CRUD 的同学进阶。

---

### 一、字段命名与类型选择

- **统一命名规范**
  - **推荐**：统一使用英文 + 下划线，如 `flight_no`、`user_id`、`created_at`。
  - **问题示例**：本项目大量使用中文列名，如 `航班号`、`订单状态`，阅读直观但：
    - 很多 ORM/工具对中文列名支持不好。
    - SQL 需要频繁加反引号、转义，容易写错。
  - **实践建议**：对外展示用中文，对内表结构统一英文命名。

- **类型选择要表达“约束”**
  - 金额：`DECIMAL(10,2)`，避免用 `FLOAT/DOUBLE` 存钱。
  - 标识符：`CHAR(n)` 适合固定长度的订单号、会员号，`VARCHAR` 适合变长字符串。
  - 时间：`DATETIME`/`TIMESTAMP`，配合时区策略统一管理。
  - 布尔值：多数用 `TINYINT(1)` 或 `BOOLEAN`，但要在注释里写清 0/1 含义。

- **CHECK 约束体现业务规则**
  - 示例：`flights` 表中价格与时间约束：
    - 价格约束：经济舱 < 商务舱 < 头等舱。
    - 时间约束：到达时间 > 起飞时间。
  - 示例 SQL：
    ```sql
    CONSTRAINT `chk_flights_time_order` CHECK (`arrival_time` > `departure_time`),
    CONSTRAINT `chk_flights_prices` CHECK (
      `price_economy` > 0
      AND `price_business` > `price_economy`
      AND `price_first` > `price_business`
    )
    ```

---

### 二、状态字段的设计与管理

- **不要直接用 1/2/3 这种“魔法数字”**
  - 本项目最初用 `tinyint` 存 `航班状态`（0 待起飞，1 已起飞，2 延误，3 取消，4 到达），问题在于：
    - **没有统一文档/枚举表**，含义散落在代码、模板里。
    - 新人看到库里的“3”完全不知道表示什么。

- **两种更好的设计方式**
  - **方案 A：使用 ENUM 存语义值**
    ```sql
    `status` ENUM('SCHEDULED','AIRBORNE','ARRIVED','DELAYED','CANCELLED')
      NOT NULL DEFAULT 'SCHEDULED'
    ```
    - 优点：直接一眼看懂；避免魔法数字；查询结果易读。
  - **方案 B：使用字典表 + 外键**
    - 字典表：
      ```sql
      CREATE TABLE `flight_status` (
        `code` VARCHAR(20) PRIMARY KEY,
        `name_zh` VARCHAR(20) NOT NULL,
        `is_terminal` TINYINT(1) NOT NULL DEFAULT 0,
        `sort_order` INT NOT NULL DEFAULT 0
      );
      ```
    - 业务表引用：
      ```sql
      `status_code` VARCHAR(20) NOT NULL,
      CONSTRAINT `fk_flights_status`
        FOREIGN KEY (`status_code`) REFERENCES `flight_status` (`code`)
      ```
    - 优点：可扩展（增加状态只改字典表）、可配置（多语言、是否终态、排序等）。

- **状态字段和业务流程要匹配**
  - 订单/支付/航班等多个状态字段，需要：
    - 定义**合法状态集合**。
    - 设计**状态机/状态流转图**（哪些状态能转到哪些状态）。
    - 在代码或数据库层防止非法状态转换（如已取消订单不能再支付）。

---

### 三、索引设计基础

- **为什么要加索引？**
  - 减少全表扫描，提高查询速度。
  - 支持常用查询场景（搜索航班、查用户订单、过滤状态等）。

- **结合查询场景设计索引**
  - 本项目中典型查询：根据起飞时间、航班状态查询未来航班列表。
  - 示例索引：
    ```sql
    INDEX `idx_flights_departure_time` (`departure_time`),
    INDEX `idx_flights_status` (`status`),
    INDEX `idx_flights_departure_status` (`departure_time`, `status`)
    ```
  - 经验：
    - **where 条件经常出现的字段**要考虑单列或组合索引。
    - 组合索引的**顺序很重要**，一般把过滤性更强、排序使用的字段放前面。

- **不要乱建索引**
  - 索引也占空间，也会拖慢 `INSERT/UPDATE/DELETE`。
  - 生产环境中要通过慢查询日志/执行计划分析，再决定是否需要新索引。

---

### 四、外键与数据完整性

- **外键的作用**
  - 防止出现“孤儿数据”：比如订单指向不存在的用户、改签记录指向不存在的订单。
  - 本项目中 `changes` 表正确使用了外键：
    ```sql
    CONSTRAINT `changes_ibfk_1` FOREIGN KEY (`原订单号`) REFERENCES `orders` (`订单号`),
    CONSTRAINT `changes_ibfk_2` FOREIGN KEY (`新订单号`) REFERENCES `orders` (`订单号`),
    CONSTRAINT `changes_ibfk_3` FOREIGN KEY (`乘客ID`) REFERENCES `passengers` (`乘客ID`)
    ```

- **什么时候用外键，什么时候只用约定？**
  - 小型/中型系统：**推荐用外键**明确约束，避免数据质量问题。
  - 超大规模系统：有些团队会移除外键，改用应用层保证，但这对工程要求更高。
  - 对入门阶段：**先学会合理用外键**，再讨论“去外键”的优化。

---

### 五、事务与并发控制（入门级）

- **事务的基本原则**
  - 一组操作要么全部成功，要么全部失败（ACID）。
  - 比如：本项目中“创建订单 + 占用座位”应该放在同一个事务内。

- **典型错误**
  - 在 `create_order` 逻辑中，先更新座位，再插入订单，没有事务保护：
    - 更新座位成功，插入订单失败 → 数据不一致。
    - 多个用户并发下单，同一座位可能被多次占用。

- **入门实践建议**
  - 应用层使用事务封装关键业务流程：
    - 开始事务 → 多个 SQL 操作 → 检查结果 → commit/rollback。
  - 不要在生产环境中把多个强相关操作拆成“多个独立请求/脚本”去跑。

---

### 六、安全：SQL 注入防护

- **危险写法**
  - 直接拼接字符串构造 SQL，比如：
    ```python
    sql = f"SELECT * FROM flights WHERE 航班号 = '{flight_no}'"
    cur.execute(sql)
    ```
  - 在生产环境中极易导致 SQL 注入。

- **正确做法：参数化查询**
  - 以 Python + MySQL 为例：
    ```python
    sql = "SELECT * FROM flights WHERE flight_no = %s"
    cur.execute(sql, [flight_no])
    ```
  - 原则：**永远不要把用户输入直接拼到 SQL 字符串里**。

---

### 七、表结构变更与兼容性思维

- **生产环境变更要考虑“渐进式迁移”**
  - 示例：把 `flights.航班状态` 从 `tinyint` 改为 `ENUM`/字典表。
  - 推荐流程：
    1. 新增新字段（如 `status_code`），保留旧字段。
    2. 写脚本迁移数据（tinyint → 语义码）。
    3. 修改应用代码，逐步改为只用新字段。
    4. 确认无依赖后再删除旧字段。
  - 在本项目里，我们之前给出的改造 SQL 就采用了这种思路。

---

### 八、如何在项目中“自解释”你的数据库

- **善用注释与文档**
  - 表级、字段级 `COMMENT` 写清业务含义。
  - 状态类字段配套枚举表/字典表。
  - 为复杂触发器、存储过程写设计文档，说明业务目的、输入输出、副作用。

- **为常用查询封装视图**
  - 示例：给航班加上状态中文名视图：
    ```sql
    CREATE VIEW v_flights AS
    SELECT f.*,
           s.name_zh AS status_name_zh
    FROM flights f
    JOIN flight_status s ON s.code = f.status_code;
    ```
  - 这样新同学只要 `SELECT * FROM v_flights`，马上能看懂状态含义。

---

### 九、小结

- **从一开始就为“维护者”设计数据库**：命名规范、字段类型、状态设计、外键、注释，都在帮未来的你和同事节省时间。
- **能在库里看懂的东西，就不要只写在代码里或脑子里**：用 CHECK、外键、字典表、视图，把业务规则“写进”数据库。
- **生产环境变更要有兼容思维**：多用新增字段 + 数据迁移 + 逐步切换的方式，而不是一次性“硬改”。

这些都是基于本项目中已经出现的真实问题抽出来的入门级经验，你可以在后续迭代中逐步把现有表结构和 SQL 改造得更接近这些实践。

