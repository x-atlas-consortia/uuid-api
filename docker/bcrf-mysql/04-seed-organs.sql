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
-- Table structure for table `organs`
--

-- DROP TABLE IF EXISTS `organs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
-- CREATE TABLE `organs` (
--  `DONOR_UUID` char(32) NOT NULL,
--  `ORGAN_CODE` varchar(8) NOT NULL,
--  `ORGAN_COUNT` int NOT NULL DEFAULT '0',
--  KEY `IDX_ORGAN_CODE` (`ORGAN_CODE`),
--  KEY `organs_ibfk_1` (`DONOR_UUID`),
--  CONSTRAINT `organs_ibfk_1` FOREIGN KEY (`DONOR_UUID`) REFERENCES `uuids` (`UUID`) ON DELETE CASCADE ON UPDATE CASCADE
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `organs`
--

LOCK TABLES `organs` WRITE;
/*!40000 ALTER TABLE `organs` DISABLE KEYS */;
INSERT INTO `organs` VALUES ('96a667104f92a38f5d4f97c38d94e738','LK',1),('3f66765e3561ee075f8b0d85c564b545','LY',6),('3f66765e3561ee075f8b0d85c564b545','SP',1),('3f66765e3561ee075f8b0d85c564b545','TH',1),('c624abbe9836c7e3b6a8d8216a316f30','LK',1),('4413c7ba71ae446a8d4080b5ebbaf7fb','RK',1),('dd258063b8389612a9596af734143906','LK',1),('2ef76fe31f322fb2349e97eb8ee549e8','LY',10),('2ef76fe31f322fb2349e97eb8ee549e8','TH',1),('2ef76fe31f322fb2349e97eb8ee549e8','SP',1),('1628b6f7eb615862322d6274a6bc9fa0','SI',1),('1628b6f7eb615862322d6274a6bc9fa0','LI',1),('23ca98ea477a00793a8d8b958e48b510','LK',1),('a3ab4491d04dff03fdd2cee5a2df70b3','SP',1),('a3ab4491d04dff03fdd2cee5a2df70b3','HT',1),('3c3c49c7d38960fc1f8275dcf4e412f9','RK',1),('461bbfdc353a2673e381f632510b0f17','LK',1),('4b257b9c1758a98af262c57bc0caa726','LY',13),('4b257b9c1758a98af262c57bc0caa726','SP',1),('14fe19053a863e17b397bf4acb465c03','LK',1),('c07f39795ed04df93bc60075e34fd654','RK',1),('6b955ebeafe9c351831bc36aa086575f','LK',1),('a4989d3a5aceca977e232224143cb0f8','RK',1),('2510644405f4e7fd86d31af0001b840f','LK',1),('aa97d20b4a8f3c1198826091bc5455d9','RK',1),('866a78fd1ac8d4db740ebbb49a205b8d','LK',1),('e0176e0fc05285de9c79eafed45dad7f','LY',8),('e0176e0fc05285de9c79eafed45dad7f','TH',1),('e0176e0fc05285de9c79eafed45dad7f','SP',1),('ab33ba540469ce7eea6ecc7a13b9075c','LK',1),('b8f375d33daa5228782abd838d851b8d','RK',1),('305cd429be1609fecb73abdc019f4aa1','LK',1),('a9175b3b41ef3cb88afa0cb1fff0f4e7','LI',1),('a9175b3b41ef3cb88afa0cb1fff0f4e7','SP',1),('a9175b3b41ef3cb88afa0cb1fff0f4e7','SI',1),('190aec1937701a97952b34cfac5529a3','HT',1),('282d80223fe5635b4c74afdbbce5f44f','LK',1),('50523a03d5db833e196a8fddc8a8d235','RK',1),('c16891deebece9ef23d7f7c13c81b671','LK',1),('9425aac9f557431786cfffbd6af985a4','RK',1),('4fd86bb6db7349c82d7bd50af5504a66','LK',1),('4021ec8b349b3eb2ddceef96dcd22251','LK',1),('8330ac373c5a1865478d4284f560e1aa','LK',1),('44be1ce06db790c05bc5a1d763420919','RK',1),('95a493ab959cc164a14d47fc61474d18','LK',1),('ae37546bb86625deed454ebb46cd7adc','LK',1),('4c795afb0b93b75e669ded72860bba89','RK',1),('2a88141ee11dfe080c01db3620a35a39','LK',1),('bb7bb27bdd18504d5ab0e7e1f54ecd97','RK',1),('3439871e0617807d2711465a249af9a5','RK',1),('8caefbd62ca7d7e944d56b8e73f1c57c','LK',1),('f8d963cab6bd10e2a4b8184ea8197fc1','RK',1),('a38b15989cc8d7cec59354b69a65d92b','RK',1),('0739c6eb8d0d51bfd244e3d5afb00aab','LK',1),('ab8258a97e0820c294d1f0ba2d261f61','LK',1),('d5d47e3cd48e28a932ea33d58f6feb00','LK',1),('d3ad6409d2ad37ef7dbcc90ccc199f68','LI',1),('d3ad6409d2ad37ef7dbcc90ccc199f68','SI',1),('a767eb82765b1a96a69e6fe28b6a387d','LK',1),('ca10ede410dee22a4eb8a1f8cbbd526b','LK',1),('ae36b667325281a00d66eed4c43c585f','RK',1),('48b15ba8abfaef4e70edfdf173649b6c','LK',1),('171fc88db789ff330b0d7a420b642a23','LK',1),('4397fcd072ac96299992b47da1dbae64','RL',1),('2fbcffe20abbb7b7d8efe3437e9d2811','RK',1),('3432d3713adbbb51f52973d137a0d7ed','RK',1),('06ce4ac9632a3f861913b51a9b1ad06d','RK',1),('bfbcdea6a2b709fd0d3aa71b5a47d924','LK',1),('731161efc308aa0e161e18be7aec2118','HT',1),('731161efc308aa0e161e18be7aec2118','LK',1),('c425c304499d4ff1485cbd0721a50159','LK',1),('4dd3bf97557acb0afee48d1a51677d03','TH',1),('d386672d8d067ee117a086710cfbde5a','LY',9),('d386672d8d067ee117a086710cfbde5a','TH',1),('d386672d8d067ee117a086710cfbde5a','SP',1),('1785aae4f0fb8f13a56d79957d1cbedf','SP',1),('95a62662006235867084078a1e10bebf','LY',11),('95a62662006235867084078a1e10bebf','SP',1),('95a62662006235867084078a1e10bebf','TH',1),('2dbd1449b42ce7f5c96db959db44b6dc','LY',10),('877c415e1e1d48b24e29f6f9522847a3','RK',1),('1e0b527a436936050455fe755dfbaba2','RK',1),('258d4da2e65a189db39d049eecbfca91','SK',1),('c37ed0a5fa384dceb5d8914e221e9f08','SK',1),('26cc9d6097a5193a5ca647d0b72a1627','SK',1),('56d58e095b39bace799a08131d331a99','SK',1),('e4e4ab805cb51f2c7f3f1f7010220598','SK',1),('b5b8b8272d214725072b616b5ca199d7','SK',1),('25fd10f300c96818d34ffbe38d52d134','SK',1),('65efcf004d21d8f2dbadf4bc5f97cb36','SK',1),('332a4331efa6b01784d6044f62bbc1a4','SK',1),('ab8f70d4776be3821f642e7f6495300c','SK',1),('63108adadd97a60ea7bdc84498384069','SK',1),('a0c1a06ebcacd9f4b274797e9ff6703c','SK',1),('2b715f960c8aad07508e8d706d1a799e','RK',1),('e5d3c8ea4ce06c7f1bca2c6419f49346','HT',1),('14aa5da0100e072b560ae411c9b8de06','HT',1),('14aa5da0100e072b560ae411c9b8de06','RL',1),('14aa5da0100e072b560ae411c9b8de06','PA',1),('03c321173b4a961964a4392bd241e561','SP',1),('03c321173b4a961964a4392bd241e561','LY',10),('be425f8a2963dda1d3a7a0c79de5e466','SI',1),('be425f8a2963dda1d3a7a0c79de5e466','LI',1),('909b44eb01033314b357a3692b583387','LI',1),('909b44eb01033314b357a3692b583387','SI',1),('79669218b9f27e3aa196b84c532d60d3','HT',1),('79669218b9f27e3aa196b84c532d60d3','SP',1),('79669218b9f27e3aa196b84c532d60d3','RL',1),('79669218b9f27e3aa196b84c532d60d3','PA',1),('4fc63b18451c435cb86ca301b4c25f5b','HT',1),('4fc63b18451c435cb86ca301b4c25f5b','PA',1),('07bf8cd878cb1cb3883c43c28acba466','HT',1),('f0aa7e5d01c0d40f0b284cbf85eb8d03','LV',1),('f0aa7e5d01c0d40f0b284cbf85eb8d03','HT',1),('9d25f15d3236251bc5adb07fe3c93872','HT',1),('0721f575bacb2afae07935f07b456c58','LV',1),('0721f575bacb2afae07935f07b456c58','HT',1),('7b12f4f595083d2cba794e78e5c929f1','HT',1),('a32f9fb2a344f2d1ad7c526aa362713c','TH',1),('72efe9be20ecdf685d479fa49fad81b6','LI',1),('5413c907ebaa5e66dcd88ecf45ffb7d0','BD',1),('e742ac485a0614e4114a26886ed0b444','LK',1),('4c99122862f4f34f80ee6d9cac36d61a','LK',1),('5c4208e2f2715c56ee8dc82b5f1b90c0','LK',1),('613776ac210f65a63462ce6f926f4557','RK',1),('da320fb2114ed3535ae97dde9abd7475','HT',1),('639066967d26730b60207e28f2d3f755','PL',1),('1dd8f2beaff92b4acd9a58d1bbe57125','PL',1),('91f68068441036ddc500b8cf4ada0fcc','PL',1),('81f55c02788008c4791a686a33b7cb31','PL',1),('fd607ecb9ca9dfab245d84d491f89601','PL',1),('3807eb744d0a4f035541b5d72a7d89bf','PL',1),('46488d059770e86d823e6d4095b95d3b','PL',1),('f815e75f1906dcf40ac7205219083ce2','PL',1),('bb1db3342bd5092fc28a967315f3cf44','PL',1),('848a39d6ec9a48cfaf9b6a9ed44868e2','PL',1),('f7b11d28e569e323eacc92cefc0bec24','PL',1),('0a6b7ef7a5e26475505e8f8564aa15c2','PL',1),('06d4bd504714be03ab2c8a49f3031f5b','PL',1),('32e2c2b8456624e40bcfc2aced7d08f2','PL',1),('acaf06701dce3af4df02c5f2f68096f6','PL',1),('1b52ca300fad097150586909d6c757a5','PL',1),('2fe50342126ec7bb2022cb34c24b0540','PL',1),('2e72853d283dcfbfd1b6535155fac8f7','PL',1),('470a1e7efdf8b34273d553a03af95e29','PL',1),('30a05ebef4b18710f669e7d55fc74652','PL',1),('0db3da0f7698a7380e49cd0adbccd18a','PL',1),('7c9a3c0bae92eaca02c573f4e98f92a2','PL',1),('e186d3009fc4b69ba6fa1727bbfd2156','PL',1),('7be792ef793c14570e6bc043246d0bbc','PL',1),('07cdcf7a151bc8f0ffab95f2fef365d7','PL',1),('5bea016355017b59418b7bc96fea059a','PL',1),('20fc336823ab141ab385053c9863f125','PL',1),('ba5af685d3b266183ec0a903beb0d8dc','PL',1),('eb70e04f5f58f3a5064dd1feebc7faa1','PL',1),('a0e57dd83f11752476d622a64f495814','PL',1),('ab29e9db4f65d7788fcb8962442a6438','PL',1),('eb2be1700728f518ea6d322855082c2e','PL',1),('356429aa137638d82d1f6a308d1b9f50','PL',1),('5c720a99748dd7458886b17462efe30a','PL',1),('cb518ddfe258bfd62bdd50e121a1f79f','PL',1),('ac6489ecc04c2a55cc20ed237a69d84b','PL',1),('f1caa0dcc9eecceffd364c5be99744d2','PL',1),('6a152306bc81179d7a1598b0d549147a','PL',1),('c171cd9c7a448acce0b8f43658c3a39a','PL',1),('56dffb6c9276eaa3a1c2be97be13ebe3','PL',1),('dab3ca946f147660e64df76eeb9a3019','PL',1),('76aaa3fda1464e4aa6333e2675350831','PL',1),('3e1c9c93b22629adc65c5cf61acec775','PL',1),('8210ae0e0c6c0ffc6c0c8de392ba788a','PL',1),('f6aad3599c384bcec6c5216ccb46d13f','PL',1),('d47e9f23f69c6483eebf35522d8ad15e','PL',1),('38587428db756f851c0cb5337f81405e','PL',1),('912da557e34ead1d62968f4336504483','PL',1),('8e6b7b430c8dfaa9f59af2f89ef47799','PL',1),('ee702a6aa459b70ba3446d3f5918372c','PL',1),('3344d2239568c83659614c58a2132d54','PL',1),('cf5e78b4471040ff4f1627cf139ca109','PL',1),('a6b2947ad30e3c0f7d0b97901ef089d9','PL',1),('5b8d90d5c9b7b9ce750efdb791506d8b','PL',1),('5e759beddd9f293ce7a22ce1733460a9','PL',1),('9ee215ee8fc2785020867ea7f15ccb12','PL',1),('5fbe42f4493a96c461f99f91761adf74','PL',1),('8bfba7cfb7d743521457c95deaa8bd83','PL',1),('64ee84d2235ec166d241ba747dc6418b','PL',1),('0f8fc4f0377495fa40a5e030e2cc6445','PL',1),('6ffb892af727ea0f36da40069437f84e','PL',1),('ff8e826009c339b73d142f4699d3b714','PL',1),('d896b5e7296c6967eaa70a28c01f7c73','PL',1),('7e1b407385a22cdaec8b3c1a28e3cc54','PL',1),('2e02511c039be12cb35a2448c00df890','PL',1),('709a6e5ffd81519cf8cd1b1125b551fc','PL',1),('4057169be3621d56847d5148ce560877','PL',1),('52ea1e3db509abf148a990ca8ecc0972','PL',1),('0d5b7e18929a81ea571f444d9d301a23','PL',1),('e5bee626ee837b90a013a46b45153ff5','PL',1),('d723b8afda1146f1da0ff91bb5545952','PL',1),('f083597a5ebb0fae68c17b28bd5b3bc7','PL',1),('393fc3d44852419d81262c4d1eaa0c04','PL',1),('a46c51540c0608d9369aeb809b443f53','PL',1),('23ae880e9eb7e534822c6292ee034994','LK',1),('a9c2ea2bd3106f142edf420dc02cdddd','RL',1),('4086dd53a9e443f4ab57207ce77402d2','RL',1),('ec9c0939123f287d7394e8251780f220','RL',1),('29a385d01f8316404952d101bc4f16c5','LL',1),('e727257a20a083467653328df4d15bef','LL',1),('96a2057079b00db6de02905feea8bd12','LV',1),('3b5d057daf1e84d746d01a16acf4f0bb','LV',1),('b2c75c96558c18c9e13ba31629f541b6','LV',1),('6a0d01e2b3c57632ef79886ba115c8de','LV',1),('7852152d702288d2ddc82c67ced9631e','LV',1),('cd44c6f5270f322a987675dbaf90e0d6','PA',1),('6a3500763db1f3c39e5d6051e80e65eb','LK',1),('fbe55a20368647cd1b05cf7abd4dce70','LK',1),('edfb624cb6413783023c52bc40cccb00','RK',1),('6f3a5cf9f32553e5e25f4c30c7ccec18','RK',1),('8791c166b90f77a078101f90ed4aeaa2','LK',1),('ca8737a61a931bade511b710aed96098','LK',1),('12327363809f68135c9b14e74ac74124','LK',1),('4cdbccaf4ab1871e7c049dd50585eb65','LK',1),('dc32c49414c71ac8f7528e9219552464','LK',1),('1dcde05aea3509b2cf89a41ceb3d700f','RK',1),('dfe60e10cebff56bebed07ef38a7e6f1','RK',1),('a523307d64ecee4c3cae5e59cf68c7d1','LK',1),('55797ef7f2be373b3781630be95d01b1','RK',1),('29acab642ac8c208b8b08ccc2b5f78db','LK',1),('028f8bb629f5a65f771be4d05ab57914','LK',1),('c3cd699d78e8e52869656640dae5964a','RK',1),('c9c683627750460e2f84e3eedb729ce0','LK',1),('25f45ca43f25964f7f7071c30e57870a','LK',1),('1b85f5bde815c383795cf892b229ec61','RK',1),('ecdedc02b4035fb812a6a92e432f6da4','RK',1),('19e78333a8f94919b10fdf07006129a1','LK',1),('7579e5b974d14149e6fa633d5598f9a8','LK',1),('492f6839756af7cf576a4b97c768e723','RK',1),('cf9b874d0c6563cb00122a40ca65e089','RK',1),('f84ff583687f3407636d8ce843b48ff0','LI',1),('f84ff583687f3407636d8ce843b48ff0','SI',1),('909b44eb01033314b357a3692b583387','BD',1),('a6861cae936bb27e472ee11acb679700','HT',1),('7dee9126a98c1e0d2445c0aecb3566ad','SP',1),('7dee9126a98c1e0d2445c0aecb3566ad','LY',3),('947630d488bcd64620176753d94a2333','LY',4),('947630d488bcd64620176753d94a2333','SP',1),('cb756aef2bc5ef3fa20b6f140801d1d2','SP',1),('89637b7467883c4689f55c645a095420','LY',12),('89637b7467883c4689f55c645a095420','SP',1),('b98fceee74b721925c833424a5bd63d4','RL',1),('e3d3717ad581030c03bed6641d76e088','LK',1),('7525aa868f2f7d2508f0e24b18a2b1b0','LK',1),('61948ab02c6e4849c2522d953694df5d','RK',1),('ff043e8a4b6d7b21620ad9f0978238d0','RK',1),('d876de578e9d8c2ce2dcd7c1bbb00681','LK',1),('dfd0352b60504b321899f738c860e3fc','RK',1),('01d8b1a59c0326441167d8375c4437ec','RK',1),('113abb6e3391c3e73972bb6bbe147687','LK',1),('17ca4161891a617a8b49b942edf93272','LK',1),('a4fb1606c5e3c491b5880862b48fafc5','LK',1),('b951738288fa04956249416a88c8fbef','BL',1),('170c2f10240e5bd064d46b26866ad1f3','SP',1),('51078d196317cdf869016b50370b2506','SP',1),('51078d196317cdf869016b50370b2506','PA',1),('170c2f10240e5bd064d46b26866ad1f3','HT',1),('170c2f10240e5bd064d46b26866ad1f3','LL',1),('170c2f10240e5bd064d46b26866ad1f3','PA',1),('6f67caf257daccd03bd2fe54841cb9f4','SP',1),('6f67caf257daccd03bd2fe54841cb9f4','PA',1),('80fc4afee1cd7e4a5a6d185a552dac02','LV',1),('80fc4afee1cd7e4a5a6d185a552dac02','SP',1),('0eb93c8e9f8394eb887e68636d723c7a','RL',1),('af0703ca30a10005fb4293374fe11c7d','RL',1),('5d64f117be81d698b4829bc3c3427b46','RL',1),('e461fb0c595fb42de4b774808b763225','RL',1),('e461fb0c595fb42de4b774808b763225','TR',1),('f573406e71d505fe44c4a7512909efc2','RL',1),('f573406e71d505fe44c4a7512909efc2','TR',1),('4ccc36f6e126945670dae224c7b3ac4e','LL',1),('4ccc36f6e126945670dae224c7b3ac4e','TR',1),('933d30fd44ad6b392dfc8a23b6e042af','RL',1),('b98fceee74b721925c833424a5bd63d4','RB',1),('51078d196317cdf869016b50370b2506','HT',1),('170c2f10240e5bd064d46b26866ad1f3','LV',1),('49ad2ea74168cf6ce1d68a3f49d03945','PA',1),('44dd327183e0e5edaba60351fd7ca68e','RN',1),('e12051ead6802a8fa24e3f3d536f561c','LN',1),('fa4fed57889f369847db296d991d9be5','RN',1),('98862309406ce91da1472207464abc4c','LN',1),('74dc1f14ab3fae0f266cd47a86ce7618','LN',1),('b923d2aa5324efdde89ef18577a99240','LN',1),('212530b33ad63b4b1bb335f47a492719','RN',1),('dfd2b9f32c7a2e842e51018414235598','LN',1),('af0703ca30a10005fb4293374fe11c7d','RB',1),('41d52d2ee8b93b9c352acd69434a6f4b','PL',1),('adb1092f3014456035856038d28384bf','PL',1),('03544b68f2015a8ffaeaf3d7bba8b455','PL',1),('2bc97ff609a8775454bc2c9a276b70a2','PL',1),('f8667a764f967d780c4ede50d602113e','PL',1),('e53072f540ac2013342a2d89d9067e3d','PL',1),('a7335d585e467ca66f49d6c3a96b3480','PL',1),('763601015186b44f6c6bf48ff1d3d217','PL',1),('493583cea487875f4964ae6dd3431762','PL',1),('710ccddb75bf16cb46fbdd8e882c3a71','PL',1),('46f5a22e8aa0ca64f295a66463e73341','PL',1),('6be77aaf694a4c2bc541346b9adfdb86','PL',1),('ea45de5fc71d70915ffe9ae4a392913e','HT',1),('f84ff583687f3407636d8ce843b48ff0','HT',1),('36736633f87c9c5b8a1f50371e7a7052','HT',1),('8515b998d5a64c49b9f0f8481bbb9e13','PL',1),('59db6e609132322b585db60db973da7a','RK',1),('4102d375082e94a2d4d0df1f49dcc37c','LI',1),('4102d375082e94a2d4d0df1f49dcc37c','SI',1),('80861d1897f0427a91e8e1886bde9009','LI',1),('80861d1897f0427a91e8e1886bde9009','SI',1),('142d18f0a749d3d02d8b1addbca15589','LI',1),('142d18f0a749d3d02d8b1addbca15589','SI',1),('54e9f1a94821a716e8e1546aee7b0f7a','LI',1),('54e9f1a94821a716e8e1546aee7b0f7a','SI',1),('ee8aaa62272a1b67a6120620a024d5ca','LK',1),('93e1af270009b12354137b94689637a0','LK',1),('68dca150a4ec40216f459659617cbe73','LK',1),('91bbcc9af30b0bfe09f477fba375f5cb','LK',1),('59819787bf261deb9bc15e03920b93cb','LK',1),('c86683ee308b4a492821d6827c5fd073','LK',1),('98ed60c3bcf5e38662667a4166737d17','LK',1),('2b30be5e6947ac4582f75b2733d13687','LK',1),('da6822b6955fb28e5ba818f5a491be22','RK',1),('40d78d697bdee2223dc148f88dea0ef9','SK',1),('a276b9cd65d962676cdf691011ca8f78','BL',1),('75a37c969806232516451da0d3688a2c','BL',1),('6433ea8557d7d519929be3215bcac59f','BL',1),('49f0866c1e3bcf5ec1f381cf96f0dd06','BL',1),('75dfb1e702f1eaa85471687de07da6e6','BL',1),('197e98c4bbd92ece524ed18026acfbc7','BL',1),('0201f8ab170c7af04c97cd86c25e2ab0','BL',1),('34a06f973f6f62344f1dad922589b1b5','LV',1),('71c1f683d10435a3d9cbb7f6052d3900','BL',1),('e9f8d577aa01abb9c6ffdd31862be16a','BL',1),('9a365990ee2f87e6ae69a8240b4b3d4c','BL',1),('05e756d2a9efc484e8a16238114b97ea','BL',1),('ff831c86a141380f572fa9a2ba7cae52','BL',1),('4dd3bf97557acb0afee48d1a51677d03','LY',1),('cc561d0d3840fe8482938208fe032a54','RN',1),('e59a4ecb40cf4131012cbbc87c548cac','LL',1),('4587eeb6aa513811a85d0cc32d1866dd','RL',1),('d15df1013d0948b4416a88fec00f5385','RL',1),('9d0274af06926c405696a533c2fbaeb9','RL',1),('a4989d3a5aceca977e232224143cb0f8','BD',2),('a4989d3a5aceca977e232224143cb0f8','LK',1),('a4989d3a5aceca977e232224143cb0f8','HT',1),('333a02138d385fe4c9f92660e27cac70','LK',1);
/*!40000 ALTER TABLE `organs` ENABLE KEYS */;
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

-- Dump completed on 2022-06-14  8:49:31
