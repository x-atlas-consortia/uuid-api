-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema hm_uuid
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema hm_uuid
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `hm_uuid` DEFAULT CHARACTER SET ascii ;
USE `hm_uuid` ;

-- -----------------------------------------------------
-- Table `hm_uuid`.`uuids`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hm_uuid`.`uuids` (
  `UUID` CHAR(32) NOT NULL,
  `ENTITY_TYPE` VARCHAR(20) NOT NULL,
  `TIME_GENERATED` TIMESTAMP NOT NULL,
  `USER_ID` VARCHAR(50) NOT NULL,
  `USER_EMAIL` VARCHAR(50) NULL DEFAULT NULL,
  PRIMARY KEY (`UUID`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `hm_uuid`.`ancestors`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hm_uuid`.`ancestors` (
  `ANCESTOR_UUID` CHAR(32) NOT NULL,
  `DESCENDANT_UUID` CHAR(32) NOT NULL,
  INDEX `IDX_ANC_UUID` (`ANCESTOR_UUID` ASC) VISIBLE,
  INDEX `IDX_DESC_UUID` (`DESCENDANT_UUID` ASC) VISIBLE,
  UNIQUE INDEX `UNQ_ANC_DEC_UUID` (`ANCESTOR_UUID` ASC, `DESCENDANT_UUID` ASC) VISIBLE,
  CONSTRAINT `ancestors_ibfk_1`
    FOREIGN KEY (`ANCESTOR_UUID`)
    REFERENCES `hm_uuid`.`uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `ancestors_ibfk_2`
    FOREIGN KEY (`DESCENDANT_UUID`)
    REFERENCES `hm_uuid`.`uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `hm_uuid`.`data_centers`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hm_uuid`.`data_centers` (
  `UUID` CHAR(32) NOT NULL,
  `DC_UUID` VARCHAR(40) NOT NULL,
  `DC_CODE` VARCHAR(8) NOT NULL,
  PRIMARY KEY (`UUID`),
  UNIQUE INDEX `UNQ_DC_UUID` (`DC_UUID` ASC) VISIBLE,
  UNIQUE INDEX `UNQ_DC_CODE` (`DC_CODE` ASC) VISIBLE,
  INDEX `IDX_DC_All` (`UUID` ASC, `DC_UUID` ASC, `DC_CODE` ASC) VISIBLE,
  CONSTRAINT `data_centers_ibfk_1`
    FOREIGN KEY (`UUID`)
    REFERENCES `hm_uuid`.`uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `hm_uuid`.`files`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hm_uuid`.`files` (
  `UUID` CHAR(32) NOT NULL,
  `BASE_DIR` VARCHAR(50) NOT NULL,
  `PATH` MEDIUMTEXT NULL DEFAULT NULL,
  `CHECKSUM` VARCHAR(50) NULL DEFAULT NULL,
  `SIZE` BIGINT NULL DEFAULT NULL,
  PRIMARY KEY (`UUID`),
  CONSTRAINT `files_ibfk_1`
    FOREIGN KEY (`UUID`)
    REFERENCES `hm_uuid`.`uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `hm_uuid`.`organs`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hm_uuid`.`organs` (
  `DONOR_UUID` CHAR(32) NOT NULL,
  `ORGAN_CODE` VARCHAR(8) NOT NULL,
  `ORGAN_COUNT` INT NOT NULL DEFAULT '0',
  INDEX `IDX_ORGAN_CODE` (`ORGAN_CODE` ASC) VISIBLE,
  CONSTRAINT `organs_ibfk_1`
    FOREIGN KEY (`DONOR_UUID`)
    REFERENCES `hm_uuid`.`uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `hm_uuid`.`uuids_attributes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `hm_uuid`.`uuids_attributes` (
  `UUID` CHAR(32) NOT NULL,
  `BASE_ID` VARCHAR(10) NULL DEFAULT NULL,
  `SUBMISSION_ID` VARCHAR(170) NULL DEFAULT NULL,
  `DESCENDANT_COUNT` INT NULL DEFAULT '0',
  PRIMARY KEY (`UUID`),
  UNIQUE INDEX `UNQ_HM_SUBMISSION_ID` (`SUBMISSION_ID` ASC) VISIBLE,
  UNIQUE INDEX `UNQ_BASE_ID` (`BASE_ID` ASC) VISIBLE,
  CONSTRAINT `uuids_attributes_ibfk_1`
    FOREIGN KEY (`UUID`)
    REFERENCES `hm_uuid`.`uuids` (`UUID`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
