-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema hm_uuid
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Table `uuids`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `uuids` (
  `UUID` CHAR(32) NOT NULL,
  `ENTITY_TYPE` VARCHAR(20) NOT NULL,
  `TIME_GENERATED` TIMESTAMP NOT NULL DEFAULT now(),
  `USER_ID` VARCHAR(50) NOT NULL,
  `USER_EMAIL` VARCHAR(50) NULL DEFAULT NULL,
  PRIMARY KEY (`UUID`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `ancestors`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `ancestors` (
  `ANCESTOR_UUID` CHAR(32) NOT NULL,
  `DESCENDANT_UUID` CHAR(32) NOT NULL,
  INDEX `IDX_ANC_UUID` (`ANCESTOR_UUID` ASC) VISIBLE,
  INDEX `IDX_DESC_UUID` (`DESCENDANT_UUID` ASC) VISIBLE,
  UNIQUE INDEX `UNQ_ANC_DEC_UUID` (`ANCESTOR_UUID` ASC, `DESCENDANT_UUID` ASC) VISIBLE,
  CONSTRAINT `ancestors_ibfk_1`
    FOREIGN KEY (`ANCESTOR_UUID`)
    REFERENCES `uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `ancestors_ibfk_2`
    FOREIGN KEY (`DESCENDANT_UUID`)
    REFERENCES `uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `data_centers`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `data_centers` (
  `UUID` CHAR(32) NOT NULL,
  `DC_UUID` VARCHAR(40) NOT NULL,
  `DC_CODE` VARCHAR(8) NOT NULL,
  PRIMARY KEY (`UUID`),
  UNIQUE INDEX `UNQ_DC_UUID` (`DC_UUID` ASC) VISIBLE,
  UNIQUE INDEX `UNQ_DC_CODE` (`DC_CODE` ASC) VISIBLE,
  INDEX `IDX_DC_All` (`UUID` ASC, `DC_UUID` ASC, `DC_CODE` ASC) VISIBLE,
  CONSTRAINT `data_centers_ibfk_1`
    FOREIGN KEY (`UUID`)
    REFERENCES `uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `files`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `files` (
  `UUID` CHAR(32) NOT NULL,
  `BASE_DIR` VARCHAR(50) NOT NULL,
  `PATH` MEDIUMTEXT NULL DEFAULT NULL,
  `CHECKSUM` VARCHAR(50) NULL DEFAULT NULL,
  `SIZE` BIGINT NULL DEFAULT NULL,
  `LAST_MODIFIED` TIMESTAMP NOT NULL DEFAULT now() ON UPDATE now(),
  PRIMARY KEY (`UUID`),
  CONSTRAINT `files_ibfk_1`
    FOREIGN KEY (`UUID`)
    REFERENCES `uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `organs`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `organs` (
  `DONOR_UUID` CHAR(32) NOT NULL,
  `ORGAN_CODE` VARCHAR(8) NOT NULL,
  `ORGAN_COUNT` INT NOT NULL DEFAULT '0',
  INDEX `IDX_ORGAN_CODE` (`ORGAN_CODE` ASC) VISIBLE,
  CONSTRAINT `organs_ibfk_1`
    FOREIGN KEY (`DONOR_UUID`)
    REFERENCES `uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `uuids_attributes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `uuids_attributes` (
  `UUID` CHAR(32) NOT NULL,
  `BASE_ID` VARCHAR(10) NULL DEFAULT NULL,
  `SUBMISSION_ID` VARCHAR(170) NULL DEFAULT NULL,
  `DESCENDANT_COUNT` INT NULL DEFAULT '0',
  PRIMARY KEY (`UUID`),
  UNIQUE INDEX `UNQ_HM_SUBMISSION_ID` (`SUBMISSION_ID` ASC) VISIBLE,
  UNIQUE INDEX `UNQ_BASE_ID` (`BASE_ID` ASC) VISIBLE,
  CONSTRAINT `uuids_attributes_ibfk_1`
    FOREIGN KEY (`UUID`)
    REFERENCES `uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- procedure ancestor_PTR
-- -----------------------------------------------------

DELIMITER $$
CREATE DEFINER=`hmroot`@`%` PROCEDURE `ancestor_PTR`(IN paramEntityUUID CHAR(32))
BEGIN
	-- Given the UUID of an entity, return information on each ancestor in
    -- the "Path To Root", including a "generation" numeric indication of how far
    -- back the entity is from the ancestor.
    --
    -- Execution such as
    -- CALL ancestor_PTR('ffff05bf4d6f1cd78ce71ad0db2f4e4f');
    -- returns a table like this:
    -- # UUID							ENTITY_TYPE	childUUID							generation
    -- 31118485d44caf82d31bf70756cc6434	LAB			c624abbe9836c7e3b6a8d8216a316f30	-7
    -- c624abbe9836c7e3b6a8d8216a316f30	DONOR		13129ad371683171b152618c83fd9e6f	-6
    -- 13129ad371683171b152618c83fd9e6f	SAMPLE		c5bd4ae9a43b580f821c5d499953bdec	-5
    -- c5bd4ae9a43b580f821c5d499953bdec	SAMPLE		da2c9ae6806e3a34b2221996b5d9ca3d	-4
    -- da2c9ae6806e3a34b2221996b5d9ca3d	SAMPLE		1dd9a68210ef57c390f90b06851877a4	-3
    -- 1dd9a68210ef57c390f90b06851877a4	DATASET		3333fdaa86c242b2d6fb33f6b66befb3	-2
    -- 3333fdaa86c242b2d6fb33f6b66befb3	DATASET		ffff05bf4d6f1cd78ce71ad0db2f4e4f	-1
    -- ffff05bf4d6f1cd78ce71ad0db2f4e4f	FILE		null								0
    --
	WITH RECURSIVE ENTITY_ANCESTORS AS  (
	  SELECT UUID
			 , ENTITY_TYPE
			 , CAST(null AS CHAR(32)) AS childUUID
			 , 0 AS generation
	  FROM uuids
	  WHERE UUID = paramEntityUUID
	  UNION ALL
	  SELECT parent.UUID
			 , parent.ENTITY_TYPE
			 , ancestors.DESCENDANT_UUID AS childUUID
			 , generation-1 AS generation
	  FROM uuids AS parent
		INNER JOIN ancestors ON parent.UUID = ancestors.ANCESTOR_UUID
		  INNER JOIN ENTITY_ANCESTORS AS ED on ancestors.DESCENDANT_UUID = ED.UUID
	)
	SELECT DISTINCT UUID, ENTITY_TYPE, childUUID, generation
	FROM ENTITY_ANCESTORS
	ORDER BY generation, UUID;

END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure all_descendants
-- -----------------------------------------------------

DELIMITER $$
CREATE DEFINER=`hmroot`@`%` PROCEDURE `all_descendants`(IN paramEntityUUID CHAR(32))
BEGIN
	-- Given the UUID of an entity, return information on every descendant it
    -- has, including a "generation" numeric indication of how far
    -- forward the descendant is from the entity.
    --
    -- Execution such as
    -- CALL all_descendants('13129ad371683171b152618c83fd9e6f ');
    -- returns a table with many rows, like this:
    -- # UUID							ENTITY_TYPE	parentUUID							generation
    -- 13129ad371683171b152618c83fd9e6f	SAMPLE		0
    -- 00fcb9fdcfdc5ca06c2a9ba003348c89	SAMPLE		13129ad371683171b152618c83fd9e6f	1
    -- 021630863302b5356e25bb544a6ee29c	SAMPLE		13129ad371683171b152618c83fd9e6f	1
    -- 2e94485c4f9c6189e5884b37a6da6ae4	SAMPLE		13129ad371683171b152618c83fd9e6f	1
    -- 357dafb8adfd626224ab7e56e2fc2698	SAMPLE		13129ad371683171b152618c83fd9e6f	1
    -- .
    -- .
    -- .
    -- ffffffe2331141e05ce10bf3019a984c	FILE		2c00130ea77e93aaaf7362b566bc454e	4
    -- ffffffe2331141e05ce10bf3019a984c	FILE		2c00130ea77e93aaaf7362b566bc454e	4
    -- ffff05bf4d6f1cd78ce71ad0db2f4e4f	FILE		3333fdaa86c242b2d6fb33f6b66befb3	5
    -- ffff4517a9a43fc55ee1489002b5de1b	FILE		1eadf62812799712d4b1232cc92b132f	5
    -- ffff4b1bc9451d8393bf13be2a43bcdb	FILE		cd25af3631d76c34691062d5a2b54e1a	5
    --
	WITH RECURSIVE ENTITY_DESCENDANTS AS (
	  SELECT UUID
			 , ENTITY_TYPE
			 , CAST(null AS CHAR(32)) AS parentUUID
			 , 0 as generation
	  FROM uuids
	  WHERE UUID = paramEntityUUID
	  UNION ALL
	  SELECT child.UUID
			 , child.ENTITY_TYPE
			 , ancestors.ANCESTOR_UUID AS parentUUID
			 , generation+1 as generation
	  FROM uuids AS child
		INNER JOIN ancestors ON child.UUID = ancestors.DESCENDANT_UUID
		  INNER JOIN ENTITY_DESCENDANTS AS EA on ancestors.ANCESTOR_UUID = EA.UUID
	)
	SELECT UUID
		   , ENTITY_TYPE
		   , parentUUID
		   , generation
	FROM ENTITY_DESCENDANTS
	ORDER BY generation, UUID;

END$$

DELIMITER ;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
