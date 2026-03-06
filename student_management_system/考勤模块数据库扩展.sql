-- 考勤管理模块数据库扩展
-- 请执行以下SQL语句扩展数据库

USE student_management;

-- 1. 扩展考勤表，添加请假相关字段
ALTER TABLE `attendances` 
ADD COLUMN `请假申请ID` char(15) DEFAULT NULL COMMENT '关联的请假申请ID' AFTER `考勤状态`,
ADD COLUMN `审批状态` tinyint DEFAULT 0 COMMENT '审批状态：0-未审批，1-已通过，2-已拒绝' AFTER `请假申请ID`,
ADD COLUMN `审批时间` datetime DEFAULT NULL COMMENT '审批时间' AFTER `审批状态`,
ADD COLUMN `审批人ID` char(10) DEFAULT NULL COMMENT '审批人ID（管理员）' AFTER `审批时间`,
ADD KEY `idx_leave_request` (`请假申请ID`);

-- 2. 创建请假申请表
DROP TABLE IF EXISTS `leave_requests`;
CREATE TABLE `leave_requests` (
  `请假申请ID` char(15) NOT NULL COMMENT '请假申请ID',
  `学号` char(12) NOT NULL COMMENT '学号',
  `课程ID` char(10) NOT NULL COMMENT '课程ID',
  `请假类型` varchar(20) NOT NULL COMMENT '请假类型：病假、事假、其他',
  `开始日期` date NOT NULL COMMENT '请假开始日期',
  `结束日期` date NOT NULL COMMENT '请假结束日期',
  `请假理由` text COMMENT '请假理由',
  `病假条图片` varchar(255) DEFAULT NULL COMMENT '病假条图片路径',
  `申请时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
  `审批状态` tinyint NOT NULL DEFAULT 0 COMMENT '审批状态：0-待审批，1-已通过，2-已拒绝',
  `审批时间` datetime DEFAULT NULL COMMENT '审批时间',
  `审批人ID` char(10) DEFAULT NULL COMMENT '审批人ID（管理员）',
  `审批意见` varchar(500) DEFAULT NULL COMMENT '审批意见',
  PRIMARY KEY (`请假申请ID`),
  KEY `idx_student` (`学号`),
  KEY `idx_course` (`课程ID`),
  KEY `idx_status` (`审批状态`),
  KEY `idx_date` (`开始日期`, `结束日期`),
  CONSTRAINT `fk_leave_student` FOREIGN KEY (`学号`) REFERENCES `students` (`学号`) ON DELETE CASCADE,
  CONSTRAINT `fk_leave_course` FOREIGN KEY (`课程ID`) REFERENCES `courses` (`课程ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='请假申请表';

