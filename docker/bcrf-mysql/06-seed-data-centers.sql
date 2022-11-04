-- MySQL dump 10.13  Distrib 8.0.29, for macos12.2 (arm64)
--
-- Host: hm-prod-02.cluster-cylxi65xrqts.us-east-1.rds.amazonaws.com    Database: hm_uuid
-- ------------------------------------------------------
-- Server version	8.0.23

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
-- SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
-- SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

-- SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '';

--
-- Table structure for table `data_centers`
--

-- DROP TABLE IF EXISTS `data_centers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `data_centers` (
--  `UUID` char(32) NOT NULL,
--  `DC_UUID` varchar(40) NOT NULL,
--  `DC_CODE` varchar(8) NOT NULL,
--  PRIMARY KEY (`UUID`),
--  UNIQUE KEY `UNQ_DC_UUID` (`DC_UUID`),
--  UNIQUE KEY `UNQ_DC_CODE` (`DC_CODE`),
--  KEY `IDX_DC_All` (`UUID`,`DC_UUID`,`DC_CODE`),
--  CONSTRAINT `data_centers_ibfk_1` FOREIGN KEY (`UUID`) REFERENCES `uuids` (`UUID`) ON DELETE CASCADE ON UPDATE CASCADE
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `data_centers`
--

LOCK TABLES `data_centers` WRITE;
/*!40000 ALTER TABLE `data_centers` DISABLE KEYS */;
INSERT INTO `data_centers` VALUES ('064c38b0892796e09c0f9b190db00e88','69cb89c4-c870-11eb-b360-4dfdb5d10392','UPENN'),('0d95f60ff84f4c418fba431e1c086b55','972b2a76-c870-11eb-a8dc-35ce3d8786fe','PNNLNU'),('0e9710bb68be47fb5f7fd66791a22a01','0b8ca9fe-c870-11eb-b35e-4dfdb5d10392','TMCPNNL'),('175c116bc94856936f7e0c0ca2c7afdb','ab7db177-79ad-11ea-835a-0e41da796b5d','TTDCT'),('1c8988eb14bf41cc1e16ba4382bbc9d2','5bd084c8-edc2-11e8-802f-0e368f3075e8','TEST'),('247369d33f2a8a415fe6214a04d2b650','5c106f29-ea2d-11e9-85e8-0efb3ba9a670','RTIGE'),('26ffa4c0a8024903e35e10a236dfdb7c','ca46f893-79ad-11ea-b66c-0a990c2810ad','TTDHV'),('308a119b30f1e50821403455d66db241','9c4a56ca-79ac-11ea-8359-0e41da796b5d','RTIBD'),('31118485d44caf82d31bf70756cc6434','73bb26e4-ed43-11e8-8f19-0a7c1eab007a','VAN'),('3ccf474e9a7c79f224cccc236dd49182','f677f31f-79b0-11ea-8295-0a53601d30b5','TTDST'),('414d117732fc82c313642c566589dd75','ea9a6442-c870-11eb-bf37-f92c084a680e','YALE'),('5087ef3e0f768160834e16ba51619e40','878a6a26-c870-11eb-a8dc-35ce3d8786fe','TTDPNNL'),('6ade5fb57fd394af3a568582362bf666','b148f323-c870-11eb-b360-4dfdb5d10392','PSUCU'),('6d799ebd8184a6410ace00f0d8383ee6','f5af3a5a-e93c-11e9-8559-0efb3ba9a670','RTIST'),('73447f339c4e5f2469aa7a9d1e0af1bc','def5fd76-ed43-11e8-b56a-0e8017bdda58','STAN'),('8ea58808098defe90acfbc1124d70c32','03b3d854-ed44-11e8-8bce-0e368f3075e8','UCSD'),('a09d378e2bc7effd1ddd9cd0eef98661','1fe64d24-c870-11eb-9a03-a9c8d5e16226','UCSDFR'),('aab5ba72a5f6b1e317452d07ac3f837c','eb5c5345-79ad-11ea-bc85-0ef992ed7ca1','TTDPD'),('c6c5c803e421111b082c93ac92f75933','308f5ffc-ed43-11e8-b56a-0e8017bdda58','CALT'),('c776856d8b9e033f1861db3a7d7a46af','301615f9-c870-11eb-a8dc-35ce3d8786fe','UCONN'),('cb2f4839a3794de11cb0e976d259fb9d','07a29e4c-ed43-11e8-b56a-0e8017bdda58','UFL'),('cb8951825a910c577cf99805944b3b94','ee6f749f-c86f-11eb-b35e-4dfdb5d10392','CHOP'),('ec69ab7e306ed37f719b372783bf3204','177f92c0-c871-11eb-9a04-a9c8d5e16226','HCA'),('f9eaf827d8ca3f777f6e42404b867bf5','d62c4872-c870-11eb-a8dd-35ce3d8786fe','UCSDCOH'),('fb8603fe68eb47749adf7df3ca0c7398','76755cd8-79ad-11ea-8293-0a53601d30b5','RTINW');
/*!40000 ALTER TABLE `data_centers` ENABLE KEYS */;
UNLOCK TABLES;
-- SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-06-14  8:49:06