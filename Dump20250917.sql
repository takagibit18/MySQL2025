-- MySQL dump 10.13  Distrib 8.0.38, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: airline_booking
-- ------------------------------------------------------
-- Server version	9.0.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `changes`
--

DROP TABLE IF EXISTS `changes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `changes` (
  `改签ID` char(20) NOT NULL,
  `原订单号` char(20) NOT NULL,
  `新订单号` char(20) NOT NULL,
  `乘客ID` char(18) NOT NULL,
  `工号` char(10) NOT NULL,
  `改签时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `改签费用` decimal(10,2) NOT NULL,
  `改签原因` varchar(200) NOT NULL,
  `改签状态` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`改签ID`),
  KEY `乘客ID` (`乘客ID`),
  KEY `工号` (`工号`),
  KEY `idx_change_original` (`原订单号`),
  KEY `idx_change_new` (`新订单号`),
  KEY `idx_change_datetime` (`改签时间`),
  KEY `idx_change_status` (`改签状态`),
  CONSTRAINT `changes_ibfk_1` FOREIGN KEY (`原订单号`) REFERENCES `orders` (`订单号`),
  CONSTRAINT `changes_ibfk_2` FOREIGN KEY (`新订单号`) REFERENCES `orders` (`订单号`),
  CONSTRAINT `changes_ibfk_3` FOREIGN KEY (`乘客ID`) REFERENCES `passengers` (`乘客ID`),
  CONSTRAINT `changes_ibfk_4` FOREIGN KEY (`工号`) REFERENCES `staff` (`工号`),
  CONSTRAINT `chk_change_fee` CHECK ((`改签费用` >= 0)),
  CONSTRAINT `chk_change_status` CHECK ((`改签状态` in (0,1,2)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changes`
--

LOCK TABLES `changes` WRITE;
/*!40000 ALTER TABLE `changes` DISABLE KEYS */;
INSERT INTO `changes` VALUES ('CHG2024032001','ORD202403200001','ORD202403200002','110101199001011234','EMP0000001','2024-03-19 18:00:00',100.00,'时间调整',1);
/*!40000 ALTER TABLE `changes` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `after_change_success` AFTER UPDATE ON `changes` FOR EACH ROW BEGIN
    IF NEW.改签状态 = 1 AND OLD.改签状态 <> 1 THEN
        -- 释放原座位
        UPDATE Seats s
        JOIN OrderDetails od ON od.航班号 = s.航班号 AND od.座位号 = s.座位号
        SET s.座位状态 = 0
        WHERE od.订单号 = NEW.原订单号;
        
        -- 占用新座位
        UPDATE Seats s
        JOIN OrderDetails od ON od.航班号 = s.航班号 AND od.座位号 = s.座位号
        SET s.座位状态 = 1
        WHERE od.订单号 = NEW.新订单号;
        
        -- 更新原订单明细状态
        UPDATE OrderDetails
        SET 明细状态 = 3
        WHERE 订单号 = NEW.原订单号;
        
        -- 更新新订单明细状态
        UPDATE OrderDetails
        SET 明细状态 = 2
        WHERE 订单号 = NEW.新订单号;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `flights`
--

DROP TABLE IF EXISTS `flights`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flights` (
  `航班号` char(10) NOT NULL,
  `飞机号` varchar(20) NOT NULL,
  `起飞时间` datetime NOT NULL,
  `到达时间` datetime NOT NULL,
  `经济舱价格` decimal(10,2) NOT NULL,
  `商务舱价格` decimal(10,2) NOT NULL,
  `头等舱价格` decimal(10,2) NOT NULL,
  `航班状态` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`航班号`),
  KEY `idx_flight_departure` (`起飞时间`),
  KEY `idx_flight_status` (`航班状态`),
  KEY `idx_flight_datetime` (`起飞时间`,`航班状态`),
  CONSTRAINT `chk_flight_prices` CHECK (((`经济舱价格` > 0) and (`商务舱价格` > `经济舱价格`) and (`头等舱价格` > `商务舱价格`))),
  CONSTRAINT `chk_flight_status` CHECK ((`航班状态` in (0,1,2,3,4))),
  CONSTRAINT `chk_flight_times` CHECK ((`到达时间` > `起飞时间`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flights`
--

LOCK TABLES `flights` WRITE;
/*!40000 ALTER TABLE `flights` DISABLE KEYS */;
INSERT INTO `flights` VALUES ('CA1234','B737-001','2024-03-20 08:00:00','2024-03-20 10:00:00',800.00,2000.00,3000.00,0),('CA1235','B737-002','2024-03-20 09:00:00','2024-03-20 12:00:00',1000.00,2500.00,3500.00,0),('CA1236','B737-003','2024-03-20 10:00:00','2024-03-20 12:30:00',900.00,2200.00,3200.00,0),('CA1237','B737-004','2024-03-20 11:00:00','2024-03-20 14:00:00',1200.00,2800.00,3800.00,0);
/*!40000 ALTER TABLE `flights` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `after_flight_takeoff` AFTER UPDATE ON `flights` FOR EACH ROW BEGIN
    IF NEW.航班状态 = 1 AND OLD.航班状态 <> 1 THEN
        -- 获取受影响的订单号
        CREATE TEMPORARY TABLE IF NOT EXISTS temp_affected_orders AS
        SELECT DISTINCT 订单号
        FROM OrderDetails
        WHERE 航班号 = NEW.航班号 AND 明细状态 = 2;
        
        -- 更新订单主表状态
        UPDATE Orders o
        JOIN temp_affected_orders t ON o.订单号 = t.订单号
        SET o.订单状态 = 4;
        
        -- 更新订单明细状态
        UPDATE OrderDetails
        SET 明细状态 = 4
        WHERE 航班号 = NEW.航班号 AND 明细状态 = 2;
        
        -- 删除临时表
        DROP TEMPORARY TABLE IF EXISTS temp_affected_orders;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `after_flight_cancel` AFTER UPDATE ON `flights` FOR EACH ROW BEGIN
    IF NEW.航班状态 = 3 AND OLD.航班状态 <> 3 THEN
        -- 获取受影响的订单
        CREATE TEMPORARY TABLE IF NOT EXISTS temp_affected_orders AS
        SELECT DISTINCT od.订单号, o.总金额
        FROM OrderDetails od
        JOIN Orders o ON o.订单号 = od.订单号
        WHERE od.航班号 = NEW.航班号 AND od.明细状态 IN (1, 2);
        
        -- 更新订单主表状态
        UPDATE Orders o
        JOIN temp_affected_orders t ON o.订单号 = t.订单号
        SET o.订单状态 = 3;
        
        -- 更新订单明细状态
        UPDATE OrderDetails
        SET 明细状态 = 3
        WHERE 航班号 = NEW.航班号 AND 明细状态 IN (1, 2);
        
        -- 释放所有座位
        UPDATE Seats
        SET 座位状态 = 0
        WHERE 航班号 = NEW.航班号;
        
        -- 创建退票记录
        INSERT INTO Refunds (退票ID, 订单号, 退票时间, 退票金额, 退票原因, 退票状态, 操作人ID)
        SELECT 
            CONCAT('R', DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'), LPAD(订单号, 6, '0')),
            订单号,
            NOW(),
            总金额,
            '航班取消自动退票',
            1,
            '系统自动'
        FROM temp_affected_orders;
        
        -- 删除临时表
        DROP TEMPORARY TABLE IF EXISTS temp_affected_orders;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `memberpoints`
--

DROP TABLE IF EXISTS `memberpoints`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `memberpoints` (
  `用户ID` char(18) NOT NULL,
  `积分余额` int NOT NULL DEFAULT '0',
  `创建时间` datetime DEFAULT CURRENT_TIMESTAMP,
  `更新时间` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`用户ID`),
  KEY `idx_points_user` (`用户ID`),
  KEY `idx_points_balance` (`积分余额`),
  CONSTRAINT `memberpoints_ibfk_1` FOREIGN KEY (`用户ID`) REFERENCES `users` (`用户ID`),
  CONSTRAINT `chk_points_balance` CHECK ((`积分余额` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `memberpoints`
--

LOCK TABLES `memberpoints` WRITE;
/*!40000 ALTER TABLE `memberpoints` DISABLE KEYS */;
/*!40000 ALTER TABLE `memberpoints` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orderdetails`
--

DROP TABLE IF EXISTS `orderdetails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orderdetails` (
  `明细ID` char(20) NOT NULL,
  `订单号` char(20) NOT NULL,
  `航班号` char(10) NOT NULL,
  `乘客ID` char(18) NOT NULL,
  `机票价格` decimal(10,2) NOT NULL,
  `座位类型` tinyint NOT NULL,
  PRIMARY KEY (`明细ID`),
  KEY `idx_orderdetail_order` (`订单号`),
  KEY `idx_orderdetail_flight` (`航班号`),
  KEY `idx_orderdetail_passenger` (`乘客ID`),
  KEY `idx_orderdetail_cabin` (`座位类型`),
  KEY `idx_orderdetail_composite` (`订单号`,`航班号`),
  CONSTRAINT `orderdetails_ibfk_1` FOREIGN KEY (`订单号`) REFERENCES `orders` (`订单号`),
  CONSTRAINT `orderdetails_ibfk_2` FOREIGN KEY (`航班号`) REFERENCES `flights` (`航班号`),
  CONSTRAINT `orderdetails_ibfk_3` FOREIGN KEY (`乘客ID`) REFERENCES `passengers` (`乘客ID`),
  CONSTRAINT `chk_orderdetail_amount` CHECK ((`机票价格` > 0)),
  CONSTRAINT `chk_orderdetail_cabin_type` CHECK ((`座位类型` in (1,2,3)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orderdetails`
--

LOCK TABLES `orderdetails` WRITE;
/*!40000 ALTER TABLE `orderdetails` DISABLE KEYS */;
INSERT INTO `orderdetails` VALUES ('DTL202403200001','ORD202403200001','CA1234','110101199001011234',3000.00,3),('DTL202403200002','ORD202403200002','CA1234','110101199001011235',2000.00,2),('DTL202403200003','ORD202403200003','CA1234','110101199001011236',800.00,1);
/*!40000 ALTER TABLE `orderdetails` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `订单号` char(20) NOT NULL,
  `用户ID` char(18) NOT NULL,
  `订单时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `订单总金额` decimal(10,2) NOT NULL,
  `支付状态` tinyint NOT NULL DEFAULT '0',
  `订单状态` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`订单号`),
  KEY `idx_order_user` (`用户ID`),
  KEY `idx_order_status` (`订单状态`),
  KEY `idx_order_payment` (`支付状态`),
  KEY `idx_order_amount` (`订单总金额`),
  KEY `idx_order_composite` (`用户ID`,`订单状态`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`用户ID`) REFERENCES `users` (`用户ID`),
  CONSTRAINT `chk_order_payment_status` CHECK ((`支付状态` in (0,1,2))),
  CONSTRAINT `chk_order_status` CHECK ((`订单状态` in (0,1,2,3,4))),
  CONSTRAINT `chk_order_total_amount` CHECK ((`订单总金额` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES ('ORD202403200001','110101199001011234','2024-03-19 14:00:00',3000.00,1,2),('ORD202403200002','110101199001011235','2024-03-19 15:00:00',2000.00,1,2),('ORD202403200003','110101199001011236','2024-03-19 16:00:00',800.00,1,2);
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `after_order_cancel` AFTER UPDATE ON `orders` FOR EACH ROW BEGIN
    IF NEW.订单状态 = 3 AND OLD.订单状态 <> 3 THEN
        -- 更新座位状态
        UPDATE Seats s
        JOIN OrderDetails od ON od.航班号 = s.航班号 AND od.座位号 = s.座位号
        SET s.座位状态 = 0
        WHERE od.订单号 = NEW.订单号;
        
        -- 更新订单明细状态
        UPDATE OrderDetails
        SET 明细状态 = 3
        WHERE 订单号 = NEW.订单号;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `after_order_complete` AFTER UPDATE ON `orders` FOR EACH ROW BEGIN
    IF NEW.订单状态 = 4 AND OLD.订单状态 <> 4 THEN
        -- 计算获得的积分（假设消费100元得1积分）
        SET @points = FLOOR(NEW.订单总金额 / 100);
        
        -- 更新用户积分
        UPDATE MemberPoints
        SET 积分余额 = 积分余额 + @points,
            更新时间 = NOW()
        WHERE 用户ID = NEW.用户ID;
        
        -- 记录积分变动
        INSERT INTO PointsHistory (
            用户ID, 
            变动类型, 
            变动积分, 
            变动原因, 
            关联订单号, 
            变动时间
        )
        VALUES (
            NEW.用户ID,
            1,
            @points,
            '订单完成奖励',
            NEW.订单号,
            NOW()
        );
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `passengers`
--

DROP TABLE IF EXISTS `passengers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `passengers` (
  `乘客ID` char(18) NOT NULL,
  `用户ID` char(18) NOT NULL,
  `姓名` varchar(20) NOT NULL,
  `性别` enum('男','女') NOT NULL,
  `出生日期` date NOT NULL,
  `证件类型` tinyint NOT NULL,
  `联系电话` char(11) NOT NULL,
  PRIMARY KEY (`乘客ID`),
  KEY `idx_passenger_user` (`用户ID`),
  KEY `idx_passenger_name` (`姓名`),
  CONSTRAINT `passengers_ibfk_1` FOREIGN KEY (`用户ID`) REFERENCES `users` (`用户ID`),
  CONSTRAINT `chk_passenger_gender` CHECK ((`性别` in (_utf8mb4'男',_utf8mb4'女'))),
  CONSTRAINT `chk_passenger_id_type` CHECK ((`证件类型` in (1,2,3))),
  CONSTRAINT `chk_passenger_phone` CHECK (regexp_like(`联系电话`,_utf8mb4'^1[3-9][0-9]{9}$'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `passengers`
--

LOCK TABLES `passengers` WRITE;
/*!40000 ALTER TABLE `passengers` DISABLE KEYS */;
INSERT INTO `passengers` VALUES ('110101199001011234','110101199001011234','张三','男','1990-01-01',1,'13800138001'),('110101199001011235','110101199001011235','李四','女','1990-02-02',1,'13800138002'),('110101199001011236','110101199001011236','王五','男','1990-03-03',1,'13800138003'),('110101199001011238','110101199001011234','张小三','男','2010-01-01',1,'13800138001');
/*!40000 ALTER TABLE `passengers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `支付ID` char(16) NOT NULL,
  `订单号` char(20) NOT NULL,
  `支付金额` decimal(10,2) NOT NULL,
  `支付方式` tinyint NOT NULL,
  `支付时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `支付状态` tinyint NOT NULL DEFAULT '0',
  `交易流水号` varchar(64) NOT NULL,
  PRIMARY KEY (`支付ID`),
  KEY `idx_payment_order` (`订单号`),
  KEY `idx_payment_datetime` (`支付时间`),
  KEY `idx_payment_status` (`支付状态`),
  KEY `idx_payment_method` (`支付方式`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`订单号`) REFERENCES `orders` (`订单号`),
  CONSTRAINT `chk_payment_amount` CHECK ((`支付金额` > 0)),
  CONSTRAINT `chk_payment_method` CHECK ((`支付方式` in (1,2,3))),
  CONSTRAINT `chk_payment_status` CHECK ((`支付状态` in (0,1,2)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
INSERT INTO `payments` VALUES ('PAY2024032001','ORD202403200001',3000.00,1,'2024-03-19 14:01:00',1,'TRX202403200001'),('PAY2024032002','ORD202403200002',2000.00,2,'2024-03-19 15:01:00',1,'TRX202403200002'),('PAY2024032003','ORD202403200003',800.00,1,'2024-03-19 16:01:00',1,'TRX202403200003');
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `after_payment_success` AFTER UPDATE ON `payments` FOR EACH ROW BEGIN
    IF NEW.支付状态 = 1 AND OLD.支付状态 <> 1 THEN
        UPDATE Seats s
        JOIN Orders o ON o.航班号 = s.航班号 AND o.座位号 = s.座位号
        SET s.座位状态 = 1
        WHERE o.订单号 = NEW.订单号;
        
        UPDATE Orders
        SET 订单状态 = 2
        WHERE 订单号 = NEW.订单号;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `pointshistory`
--

DROP TABLE IF EXISTS `pointshistory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pointshistory` (
  `记录ID` bigint NOT NULL AUTO_INCREMENT,
  `用户ID` char(18) NOT NULL,
  `变动类型` tinyint NOT NULL COMMENT '1:增加 2:减少',
  `变动积分` int NOT NULL,
  `变动原因` varchar(100) NOT NULL,
  `关联订单号` char(20) DEFAULT NULL,
  `变动时间` datetime NOT NULL,
  PRIMARY KEY (`记录ID`),
  KEY `idx_points_history_user` (`用户ID`),
  KEY `idx_points_history_order` (`关联订单号`),
  KEY `idx_points_history_datetime` (`变动时间`),
  CONSTRAINT `pointshistory_ibfk_1` FOREIGN KEY (`用户ID`) REFERENCES `users` (`用户ID`),
  CONSTRAINT `pointshistory_ibfk_2` FOREIGN KEY (`关联订单号`) REFERENCES `orders` (`订单号`),
  CONSTRAINT `chk_points_change` CHECK ((`变动积分` > 0)),
  CONSTRAINT `chk_points_type` CHECK ((`变动类型` in (1,2)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pointshistory`
--

LOCK TABLES `pointshistory` WRITE;
/*!40000 ALTER TABLE `pointshistory` DISABLE KEYS */;
/*!40000 ALTER TABLE `pointshistory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `refunds`
--

DROP TABLE IF EXISTS `refunds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `refunds` (
  `退票ID` char(20) NOT NULL,
  `订单号` char(20) NOT NULL,
  `乘客ID` char(18) NOT NULL,
  `工号` char(10) NOT NULL,
  `退票时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `退票金额` decimal(10,2) NOT NULL,
  `退票原因` varchar(200) NOT NULL,
  `退票状态` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`退票ID`),
  KEY `乘客ID` (`乘客ID`),
  KEY `工号` (`工号`),
  KEY `idx_refund_order` (`订单号`),
  KEY `idx_refund_datetime` (`退票时间`),
  KEY `idx_refund_status` (`退票状态`),
  CONSTRAINT `refunds_ibfk_1` FOREIGN KEY (`订单号`) REFERENCES `orders` (`订单号`),
  CONSTRAINT `refunds_ibfk_2` FOREIGN KEY (`乘客ID`) REFERENCES `passengers` (`乘客ID`),
  CONSTRAINT `refunds_ibfk_3` FOREIGN KEY (`工号`) REFERENCES `staff` (`工号`),
  CONSTRAINT `chk_refund_amount` CHECK ((`退票金额` >= 0)),
  CONSTRAINT `chk_refund_status` CHECK ((`退票状态` in (0,1,2)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `refunds`
--

LOCK TABLES `refunds` WRITE;
/*!40000 ALTER TABLE `refunds` DISABLE KEYS */;
INSERT INTO `refunds` VALUES ('REF2024032001','ORD202403200003','110101199001011236','EMP0000002','2024-03-19 19:00:00',700.00,'个人原因',1);
/*!40000 ALTER TABLE `refunds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `routes`
--

DROP TABLE IF EXISTS `routes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `routes` (
  `航线ID` int NOT NULL AUTO_INCREMENT,
  `起飞机场` varchar(20) NOT NULL,
  `落地机场` varchar(20) NOT NULL,
  `距离` int NOT NULL,
  `航线状态` tinyint NOT NULL DEFAULT '1',
  `航班号` char(10) DEFAULT NULL,
  PRIMARY KEY (`航线ID`),
  KEY `idx_route_cities` (`起飞机场`,`落地机场`),
  KEY `idx_route_status` (`航线状态`),
  KEY `航班号` (`航班号`),
  CONSTRAINT `routes_ibfk_1` FOREIGN KEY (`航班号`) REFERENCES `flights` (`航班号`),
  CONSTRAINT `chk_route_distance` CHECK ((`距离` > 0)),
  CONSTRAINT `chk_route_status` CHECK ((`航线状态` in (0,1)))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `routes`
--

LOCK TABLES `routes` WRITE;
/*!40000 ALTER TABLE `routes` DISABLE KEYS */;
INSERT INTO `routes` VALUES (1,'北京','上海',1200,1,NULL),(2,'北京','广州',1800,1,NULL),(3,'上海','广州',1300,1,NULL),(4,'北京','深圳',2000,1,NULL);
/*!40000 ALTER TABLE `routes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seats`
--

DROP TABLE IF EXISTS `seats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seats` (
  `航班号` char(10) NOT NULL,
  `座位号` varchar(10) NOT NULL,
  `座位类型` tinyint NOT NULL,
  `座位状态` tinyint NOT NULL DEFAULT '0',
  `价格` decimal(10,2) NOT NULL,
  PRIMARY KEY (`航班号`,`座位号`),
  KEY `idx_seat_flight` (`航班号`),
  KEY `idx_seat_type` (`座位类型`),
  KEY `idx_seat_status` (`座位状态`),
  KEY `idx_seat_composite` (`航班号`,`座位类型`,`座位状态`),
  CONSTRAINT `seats_ibfk_1` FOREIGN KEY (`航班号`) REFERENCES `flights` (`航班号`),
  CONSTRAINT `chk_seat_price` CHECK ((`价格` > 0)),
  CONSTRAINT `chk_seat_status` CHECK ((`座位状态` in (0,1,2))),
  CONSTRAINT `chk_seat_type` CHECK ((`座位类型` in (1,2,3)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seats`
--

LOCK TABLES `seats` WRITE;
/*!40000 ALTER TABLE `seats` DISABLE KEYS */;
INSERT INTO `seats` VALUES ('CA1234','A1',3,0,3000.00),('CA1234','B1',2,0,2000.00),('CA1234','C1',1,0,800.00),('CA1235','A1',3,0,3500.00),('CA1235','B1',2,0,2500.00),('CA1235','C1',1,0,1000.00);
/*!40000 ALTER TABLE `seats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff`
--

DROP TABLE IF EXISTS `staff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff` (
  `工号` char(10) NOT NULL,
  `姓名` varchar(20) NOT NULL,
  `密码` varchar(20) NOT NULL,
  `性别` enum('男','女') NOT NULL,
  `联系电话` char(11) NOT NULL,
  `邮箱` varchar(30) NOT NULL,
  `部门` varchar(20) NOT NULL,
  `职位` varchar(20) NOT NULL,
  `入职时间` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`工号`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff`
--

LOCK TABLES `staff` WRITE;
/*!40000 ALTER TABLE `staff` DISABLE KEYS */;
INSERT INTO `staff` VALUES ('EMP0000001','张工','staff123','男','13900139001','zhanggong@airline.com','客服部','客服专员','2023-01-01 09:00:00'),('EMP0000002','李工','staff123','女','13900139002','ligong@airline.com','售票部','售票员','2023-01-01 09:00:00'),('EMP0000003','王工','staff123','男','13900139003','wanggong@airline.com','运营部','运营主管','2023-01-01 09:00:00');
/*!40000 ALTER TABLE `staff` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `用户ID` char(18) NOT NULL,
  `用户名` varchar(20) NOT NULL,
  `密码` varchar(20) NOT NULL,
  `姓名` varchar(20) NOT NULL,
  `性别` enum('男','女') NOT NULL,
  `手机号` char(11) NOT NULL,
  `邮箱` varchar(30) NOT NULL,
  `会员等级` tinyint NOT NULL DEFAULT '0',
  PRIMARY KEY (`用户ID`),
  UNIQUE KEY `idx_user_phone` (`手机号`),
  UNIQUE KEY `idx_user_email` (`邮箱`),
  KEY `idx_user_name` (`姓名`),
  KEY `idx_user_member_level` (`会员等级`),
  CONSTRAINT `chk_member_level` CHECK ((`会员等级` between 0 and 5)),
  CONSTRAINT `chk_user_email` CHECK (regexp_like(`邮箱`,_utf8mb4'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$')),
  CONSTRAINT `chk_user_gender` CHECK ((`性别` in (_utf8mb4'男',_utf8mb4'女'))),
  CONSTRAINT `chk_user_phone` CHECK (regexp_like(`手机号`,_utf8mb4'^1[3-9][0-9]{9}$'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('110101199001011234','user1','password123','张三','男','13800138001','zhangsan@email.com',1),('110101199001011235','user2','password123','李四','女','13800138002','lisi@email.com',0),('110101199001011236','user3','password123','王五','男','13800138003','wangwu@email.com',2),('110101199001011237','user4','password123','赵六','女','13800138004','zhaoliu@email.com',1);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `after_user_create` AFTER INSERT ON `users` FOR EACH ROW BEGIN
    INSERT INTO MemberPoints (用户ID, 积分余额, 创建时间)
    VALUES (NEW.用户ID, 0, NOW());
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Dumping events for database 'airline_booking'
--

--
-- Dumping routines for database 'airline_booking'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-17 14:52:35
