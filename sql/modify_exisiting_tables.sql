-- Rename tables to be more generalized
Rename TABLE hm_ancestors to ancestors,
	hm_data_centers to data_centers,
 	hm_files to files,
	hm_uuids to uuids,
	hm_organs to organs;

-- Rename various columns to be more generalized
-- Alter table 'uuids'
ALTER TABLE uuids CHANGE COLUMN `HUBMAP_BASE_ID` `BASE_ID` VARCHAR(10);
ALTER TABLE uuids CHANGE COLUMN `HM_UUID` `UUID` CHAR(32);

-- Alter table 'data_centers'
ALTER TABLE data_centers CHANGE COLUMN `HM_UUID` `UUID` CHAR(32);

-- Alter table 'files'
ALTER TABLE files CHANGE COLUMN `HM_UUID` `UUID` CHAR(32);
