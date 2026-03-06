-- 学生管理系统数据库设计
-- 数据库名称: student_management

CREATE DATABASE IF NOT EXISTS student_management DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE student_management;

-- 1. 学生表
DROP TABLE IF EXISTS `students`;
CREATE TABLE `students` (
  `学号` char(12) NOT NULL COMMENT '学号',
  `姓名` varchar(50) NOT NULL COMMENT '姓名',
  `性别` char(1) NOT NULL COMMENT '性别：M-男，F-女',
  `出生日期` date NOT NULL COMMENT '出生日期',
  `手机号` char(11) NOT NULL COMMENT '手机号',
  `邮箱` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `班级ID` char(10) DEFAULT NULL COMMENT '班级ID',
  `入学日期` date NOT NULL COMMENT '入学日期',
  `密码` varchar(100) NOT NULL DEFAULT '123456' COMMENT '登录密码',
  `状态` tinyint NOT NULL DEFAULT 1 COMMENT '状态：1-在校，0-离校',
  PRIMARY KEY (`学号`),
  KEY `idx_class` (`班级ID`),
  KEY `idx_status` (`状态`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生表';

-- 2. 教师表
DROP TABLE IF EXISTS `teachers`;
CREATE TABLE `teachers` (
  `工号` char(10) NOT NULL COMMENT '工号',
  `姓名` varchar(50) NOT NULL COMMENT '姓名',
  `性别` char(1) NOT NULL COMMENT '性别：M-男，F-女',
  `手机号` char(11) NOT NULL COMMENT '手机号',
  `邮箱` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `职称` varchar(20) DEFAULT NULL COMMENT '职称',
  `部门` varchar(50) DEFAULT NULL COMMENT '所属部门',
  `密码` varchar(100) NOT NULL DEFAULT '123456' COMMENT '登录密码',
  `状态` tinyint NOT NULL DEFAULT 1 COMMENT '状态：1-在职，0-离职',
  PRIMARY KEY (`工号`),
  KEY `idx_status` (`状态`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师表';

-- 3. 管理员表
DROP TABLE IF EXISTS `admins`;
CREATE TABLE `admins` (
  `管理员ID` char(10) NOT NULL COMMENT '管理员ID',
  `用户名` varchar(50) NOT NULL COMMENT '用户名',
  `姓名` varchar(50) NOT NULL COMMENT '姓名',
  `密码` varchar(100) NOT NULL DEFAULT 'admin123' COMMENT '登录密码',
  `角色` varchar(20) NOT NULL DEFAULT '管理员' COMMENT '角色',
  `状态` tinyint NOT NULL DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
  PRIMARY KEY (`管理员ID`),
  UNIQUE KEY `idx_username` (`用户名`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

-- 4. 班级表
DROP TABLE IF EXISTS `classes`;
CREATE TABLE `classes` (
  `班级ID` char(10) NOT NULL COMMENT '班级ID',
  `班级名称` varchar(50) NOT NULL COMMENT '班级名称',
  `专业` varchar(50) DEFAULT NULL COMMENT '专业',
  `年级` varchar(10) DEFAULT NULL COMMENT '年级',
  `班主任工号` char(10) DEFAULT NULL COMMENT '班主任工号',
  `创建时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`班级ID`),
  KEY `idx_teacher` (`班主任工号`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级表';

-- 5. 课程表
DROP TABLE IF EXISTS `courses`;
CREATE TABLE `courses` (
  `课程ID` char(10) NOT NULL COMMENT '课程ID',
  `课程名称` varchar(100) NOT NULL COMMENT '课程名称',
  `课程代码` varchar(20) DEFAULT NULL COMMENT '课程代码',
  `学分` decimal(3,1) NOT NULL DEFAULT 0 COMMENT '学分',
  `授课教师工号` char(10) DEFAULT NULL COMMENT '授课教师工号',
  `上课时间` varchar(100) DEFAULT NULL COMMENT '上课时间',
  `上课地点` varchar(50) DEFAULT NULL COMMENT '上课地点',
  `课程状态` tinyint NOT NULL DEFAULT 1 COMMENT '课程状态：1-开课，0-停课',
  PRIMARY KEY (`课程ID`),
  KEY `idx_teacher` (`授课教师工号`),
  KEY `idx_status` (`课程状态`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程表';

-- 6. 选课表
DROP TABLE IF EXISTS `enrollments`;
CREATE TABLE `enrollments` (
  `选课ID` char(15) NOT NULL COMMENT '选课ID',
  `学号` char(12) NOT NULL COMMENT '学号',
  `课程ID` char(10) NOT NULL COMMENT '课程ID',
  `选课时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '选课时间',
  `成绩` decimal(5,2) DEFAULT NULL COMMENT '成绩',
  `选课状态` tinyint NOT NULL DEFAULT 1 COMMENT '选课状态：1-已选，2-已退选，3-已完成',
  PRIMARY KEY (`选课ID`),
  KEY `idx_student` (`学号`),
  KEY `idx_course` (`课程ID`),
  UNIQUE KEY `idx_student_course` (`学号`, `课程ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='选课表';

-- 7. 成绩表
DROP TABLE IF EXISTS `grades`;
CREATE TABLE `grades` (
  `成绩ID` char(15) NOT NULL COMMENT '成绩ID',
  `学号` char(12) NOT NULL COMMENT '学号',
  `课程ID` char(10) NOT NULL COMMENT '课程ID',
  `平时成绩` decimal(5,2) DEFAULT NULL COMMENT '平时成绩',
  `期末成绩` decimal(5,2) DEFAULT NULL COMMENT '期末成绩',
  `总成绩` decimal(5,2) DEFAULT NULL COMMENT '总成绩',
  `成绩等级` varchar(10) DEFAULT NULL COMMENT '成绩等级：A/B/C/D/F',
  `录入时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
  `录入教师工号` char(10) DEFAULT NULL COMMENT '录入教师工号',
  PRIMARY KEY (`成绩ID`),
  KEY `idx_student` (`学号`),
  KEY `idx_course` (`课程ID`),
  KEY `idx_teacher` (`录入教师工号`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成绩表';

-- 8. 考勤表
DROP TABLE IF EXISTS `attendances`;
CREATE TABLE `attendances` (
  `考勤ID` char(15) NOT NULL COMMENT '考勤ID',
  `学号` char(12) NOT NULL COMMENT '学号',
  `课程ID` char(10) NOT NULL COMMENT '课程ID',
  `考勤日期` date NOT NULL COMMENT '考勤日期',
  `考勤状态` tinyint NOT NULL COMMENT '考勤状态：1-出勤，2-迟到，3-早退，4-缺勤',
  `备注` varchar(200) DEFAULT NULL COMMENT '备注',
  `记录教师工号` char(10) DEFAULT NULL COMMENT '记录教师工号',
  PRIMARY KEY (`考勤ID`),
  KEY `idx_student` (`学号`),
  KEY `idx_course` (`课程ID`),
  KEY `idx_date` (`考勤日期`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考勤表';

-- 外键约束
ALTER TABLE `students` ADD CONSTRAINT `fk_student_class` FOREIGN KEY (`班级ID`) REFERENCES `classes` (`班级ID`) ON DELETE SET NULL;
ALTER TABLE `classes` ADD CONSTRAINT `fk_class_teacher` FOREIGN KEY (`班主任工号`) REFERENCES `teachers` (`工号`) ON DELETE SET NULL;
ALTER TABLE `courses` ADD CONSTRAINT `fk_course_teacher` FOREIGN KEY (`授课教师工号`) REFERENCES `teachers` (`工号`) ON DELETE SET NULL;
ALTER TABLE `enrollments` ADD CONSTRAINT `fk_enrollment_student` FOREIGN KEY (`学号`) REFERENCES `students` (`学号`) ON DELETE CASCADE;
ALTER TABLE `enrollments` ADD CONSTRAINT `fk_enrollment_course` FOREIGN KEY (`课程ID`) REFERENCES `courses` (`课程ID`) ON DELETE CASCADE;
ALTER TABLE `grades` ADD CONSTRAINT `fk_grade_student` FOREIGN KEY (`学号`) REFERENCES `students` (`学号`) ON DELETE CASCADE;
ALTER TABLE `grades` ADD CONSTRAINT `fk_grade_course` FOREIGN KEY (`课程ID`) REFERENCES `courses` (`课程ID`) ON DELETE CASCADE;
ALTER TABLE `grades` ADD CONSTRAINT `fk_grade_teacher` FOREIGN KEY (`录入教师工号`) REFERENCES `teachers` (`工号`) ON DELETE SET NULL;
ALTER TABLE `attendances` ADD CONSTRAINT `fk_attendance_student` FOREIGN KEY (`学号`) REFERENCES `students` (`学号`) ON DELETE CASCADE;
ALTER TABLE `attendances` ADD CONSTRAINT `fk_attendance_course` FOREIGN KEY (`课程ID`) REFERENCES `courses` (`课程ID`) ON DELETE CASCADE;
ALTER TABLE `attendances` ADD CONSTRAINT `fk_attendance_teacher` FOREIGN KEY (`记录教师工号`) REFERENCES `teachers` (`工号`) ON DELETE SET NULL;

-- 插入测试数据
-- 插入管理员
INSERT INTO `admins` (`管理员ID`, `用户名`, `姓名`, `密码`, `角色`) VALUES
('ADMIN001', 'admin', '系统管理员', 'admin123', '管理员');

-- 插入教师
INSERT INTO `teachers` (`工号`, `姓名`, `性别`, `手机号`, `邮箱`, `职称`, `部门`, `密码`) VALUES
('T001', '张老师', 'M', '13800138001', 'zhang@example.com', '教授', '计算机学院', '123456'),
('T002', '李老师', 'F', '13800138002', 'li@example.com', '副教授', '数学学院', '123456'),
('T003', '王老师', 'M', '13800138003', 'wang@example.com', '讲师', '计算机学院', '123456');

-- 插入班级
INSERT INTO `classes` (`班级ID`, `班级名称`, `专业`, `年级`, `班主任工号`) VALUES
('C2021001', '计算机2021-1班', '计算机科学与技术', '2021', 'T001'),
('C2021002', '计算机2021-2班', '计算机科学与技术', '2021', 'T002'),
('C2022001', '数学2022-1班', '数学与应用数学', '2022', 'T002');

-- 插入学生
INSERT INTO `students` (`学号`, `姓名`, `性别`, `出生日期`, `手机号`, `邮箱`, `班级ID`, `入学日期`, `密码`) VALUES
('2021001001', '张三', 'M', '2003-05-15', '13900139001', 'zhangsan@example.com', 'C2021001', '2021-09-01', '123456'),
('2021001002', '李四', 'F', '2003-08-20', '13900139002', 'lisi@example.com', 'C2021001', '2021-09-01', '123456'),
('2021002001', '王五', 'M', '2003-03-10', '13900139003', 'wangwu@example.com', 'C2021002', '2021-09-01', '123456'),
('2022001001', '赵六', 'F', '2004-06-25', '13900139004', 'zhaoliu@example.com', 'C2022001', '2022-09-01', '123456');

-- 插入课程
INSERT INTO `courses` (`课程ID`, `课程名称`, `课程代码`, `学分`, `授课教师工号`, `上课时间`, `上课地点`, `课程状态`) VALUES
('COURSE001', 'Python程序设计', 'CS101', 3.0, 'T001', '周一 8:00-10:00', '教学楼A101', 1),
('COURSE002', '数据库原理', 'CS201', 3.5, 'T001', '周三 14:00-16:00', '教学楼A102', 1),
('COURSE003', '高等数学', 'MATH101', 4.0, 'T002', '周二 10:00-12:00', '教学楼B201', 1),
('COURSE004', 'Django框架开发', 'CS301', 2.5, 'T003', '周四 14:00-16:00', '教学楼A103', 1);

-- 插入选课记录
INSERT INTO `enrollments` (`选课ID`, `学号`, `课程ID`, `选课时间`, `选课状态`) VALUES
('ENR2021001001', '2021001001', 'COURSE001', '2021-09-10 10:00:00', 1),
('ENR2021001002', '2021001001', 'COURSE002', '2021-09-10 10:05:00', 1),
('ENR2021002001', '2021001002', 'COURSE001', '2021-09-10 10:10:00', 1),
('ENR2021002002', '2021001002', 'COURSE003', '2021-09-10 10:15:00', 1);

-- 插入成绩记录
INSERT INTO `grades` (`成绩ID`, `学号`, `课程ID`, `平时成绩`, `期末成绩`, `总成绩`, `成绩等级`, `录入教师工号`) VALUES
('GRD2021001001', '2021001001', 'COURSE001', 85.0, 90.0, 88.0, 'B', 'T001'),
('GRD2021001002', '2021001001', 'COURSE002', 90.0, 95.0, 93.0, 'A', 'T001'),
('GRD2021002001', '2021001002', 'COURSE001', 80.0, 85.0, 83.0, 'B', 'T001');

-- 插入考勤记录
INSERT INTO `attendances` (`考勤ID`, `学号`, `课程ID`, `考勤日期`, `考勤状态`, `记录教师工号`) VALUES
('ATT2021001001', '2021001001', 'COURSE001', '2021-09-15', 1, 'T001'),
('ATT2021001002', '2021001001', 'COURSE001', '2021-09-22', 1, 'T001'),
('ATT2021002001', '2021001002', 'COURSE001', '2021-09-15', 2, 'T001'),
('ATT2021002002', '2021001002', 'COURSE001', '2021-09-22', 1, 'T001');

